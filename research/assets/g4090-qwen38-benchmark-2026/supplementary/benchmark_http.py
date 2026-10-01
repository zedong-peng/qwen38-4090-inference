#!/usr/bin/env python3
"""Record complete responses, server timings and client wall time; stdlib only."""
import argparse
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import time
import urllib.error
import urllib.request

CASES = {
    "json": "Return ONLY a JSON object (no prose, no code fence) describing a fictional city with keys: name (string), founded (integer year), population (integer), districts (array of exactly 3 objects each with name and area_km2), climate {summer_c: number, winter_c: number}, coastal (boolean).",
    "code": "Write a complete Python module implementing an LRU cache class with get, put and delete, followed by at most five concise unittest test methods that exercise eviction order. Put everything in one ```python block and end the block with: if __name__ == '__main__': unittest.main()",
    "prose": "Write a 500-word short story about a lighthouse keeper who receives a letter from the future.",
}


def post(url, body):
    request = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def check_output(workload, text):
    # Generated code is parsed, never executed.
    if workload == "json":
        try:
            obj = json.loads(text)
            districts = obj.get("districts") if isinstance(obj, dict) else None
            return {"valid_json": True, "three_districts": isinstance(districts, list) and len(districts) == 3}
        except (ValueError, TypeError, AttributeError):
            return {"valid_json": False}
    if workload == "code":
        blocks = re.findall(r"```python\s*\n(.*?)```", text, re.S)
        try:
            tree = ast.parse(blocks[-1] if blocks else text)
            return {"python_syntax": bool(tree.body), "semantic_tests": "not_run"}
        except SyntaxError:
            return {"python_syntax": False, "semantic_tests": "not_run"}
    return {"words": len(text.split())}


def gpu_snapshot(index):
    args = ["nvidia-smi", "-i", str(index),
            "--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu",
            "--format=csv,noheader,nounits"]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else {"error": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"error": str(error)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18038")
    parser.add_argument("--label", required=True)
    parser.add_argument("--model", default="qwen3.8-27b")
    parser.add_argument("--engine", choices=["ninfer", "llama"], default="ninfer")
    parser.add_argument("--out", required=True)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--gpu", type=int, default=3)
    args = parser.parse_args()
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for workload, prompt in [("warmup", "Say hello.")] + list(CASES.items()):
        for rep in range(1 if workload == "warmup" else args.reps):
            body = {"model": args.model, "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0, "max_tokens": 16 if workload == "warmup" else args.max_tokens,
                    "stream": False, "seed": 42, "presence_penalty": 0.0, "frequency_penalty": 0.0}
            if args.engine == "ninfer":
                body["enable_thinking"] = False
            else:
                body.update({"chat_template_kwargs": {"enable_thinking": False}, "cache_prompt": False})
            row = {"label": args.label, "workload": workload, "rep": rep,
                   "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "request": body,
                   "gpu_before": gpu_snapshot(args.gpu)}
            start = time.perf_counter()
            try:
                response = post(args.base_url + "/v1/chat/completions", body)
                row.update({"wall_s": time.perf_counter() - start, "response": response,
                            "gpu_after": gpu_snapshot(args.gpu)})
                usage, timings = response.get("usage", {}), response.get("timings", {})
                tokens = usage.get("completion_tokens")
                if tokens is None:
                    tokens = timings.get("predicted_n")
                if not isinstance(tokens, int) or tokens < 0:
                    raise ValueError("response has no valid completion token count")
                row["completion_tokens"] = tokens
                row["end_to_end_output_tps"] = tokens / row["wall_s"]
                row["server_decode_tps"] = timings.get("predicted_per_second")
                row["server_prefill_tps"] = timings.get("prompt_per_second")
                row["server_prompt_ms"] = timings.get("prompt_ms")
                if timings.get("draft_n"):
                    row["draft_acceptance"] = timings.get("draft_n_accepted", 0) / timings["draft_n"]
                content = response["choices"][0]["message"].get("content") or ""
                row["output_sha256"] = hashlib.sha256(content.encode()).hexdigest()
                if workload != "warmup":
                    row["quality_check"] = check_output(workload, content)
            except urllib.error.HTTPError as error:
                row["error"] = {"status": error.code, "body": error.read().decode(errors="replace")}
            except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
                row["error"] = str(error)
            row.setdefault("wall_s", time.perf_counter() - start)
            rows.append(row)
            (destination / (args.label + ".json")).write_text(json.dumps(rows, indent=2))
            print(json.dumps({key: row.get(key) for key in ["label", "workload", "rep",
                             "completion_tokens", "server_decode_tps", "end_to_end_output_tps", "error"]}), flush=True)
    summary = []
    for workload in CASES:
        valid = [r for r in rows if r["workload"] == workload and "error" not in r]
        def median(key):
            values = [r[key] for r in valid if r.get(key) is not None]
            return statistics.median(values) if values else None
        summary.append({"label": args.label, "workload": workload, "successful_reps": len(valid),
                        "failed_reps": args.reps - len(valid),
                        "median_decode_tps": median("server_decode_tps"),
                        "median_end_to_end_output_tps": median("end_to_end_output_tps"),
                        "median_prefill_tps": median("server_prefill_tps"),
                        "median_server_prompt_ms": median("server_prompt_ms"),
                        "median_draft_acceptance": median("draft_acceptance"),
                        "finish_reasons": [r["response"]["choices"][0].get("finish_reason") for r in valid],
                        "quality_checks": [r["quality_check"] for r in valid]})
    (destination / (args.label + ".summary.json")).write_text(json.dumps(summary, indent=2))
    return 1 if any("error" in row for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
