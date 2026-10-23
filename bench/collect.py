"""Build the page data (results.json, samples.json) from bench/methods.json, bench/references.json and the run tree.

usage: python3 bench/collect.py [--runs RUNS_DIR] [--out results/]
The run tree is what bench/run_4090.sh writes: RUNS_DIR/<timestamp>/<setup>/<rep>/ (agentperf-local result
directories) next to <timestamp>/run.log and gpus.csv. A setup with no finished full replay is listed as pending, or as
failed with the reason its log gives. Completion time is the median over full replays (AA reports one run).
"""

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORKLOAD = {
    "name": "AA-AgentPerf-Local default replay (agentperf-default-v1)",
    "runner": "agentperf-local 0.3.4",
    "tasks": 8, "turns": 168, "tool_calls": 172, "context_tokens": 65536, "concurrency": 1,
    "output_policy": "exact (ignore_eos, recorded length)", "sampling": "temperature 0.7, top_p 0.8, top_k 20, min_p 0",
}
HARDWARE = {
    "system": "NVIDIA GeForce RTX 4090", "memory_gb": 24, "bandwidth_gbs": 1008, "power_limit_w": 450,
    "driver": "570.124.06", "cpu": "Intel Xeon Silver 4210", "shared": "one card of a shared four-card server",
}
# a retry of a setup under another launch setting counts as that setup
ALIASES = {"vllm-mtp3b": "vllm-mtp3"}


def load(path):
    return json.loads(Path(path).read_text())


def get(d, *keys):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def replay(rep_dir):
    s = load(rep_dir / "summary.json")
    tot = s["totals"]
    turns = [json.loads(x) for x in (rep_dir / "turns.jsonl").read_text().splitlines() if x.strip()]
    dep = rep_dir / "deployment.json"
    r = {
        "run": "/".join(rep_dir.parts[-3:]),
        "launch": get(load(dep), "deployment", "server_launch_command") if dep.exists() else None,
        "ok": bool(s.get("success")) and tot["failed_turns"] == 0,
        "completion_s": tot["total_inference_latency_ms"] / 1000,
        "output_tps": s.get("output_tokens_per_second"),
        "ttft_p50_ms": get(s, "latency_distributions_ms", "time_to_first_token", "p50"),
        "cached_tokens": tot.get("total_server_cached_prompt_tokens"),
        "uncached_tokens": tot.get("total_server_uncached_prompt_tokens"),
        "output_tokens": tot.get("total_server_output_tokens"),
    }
    samples = [[get(t, "turn_id"), get(t, "tokens", "server_prompt_tokens"), get(t, "tokens", "server_cached_prompt_tokens"),
                get(t, "tokens", "server_output_tokens"), get(t, "timing", "time_to_first_token_ms"),
                get(t, "timing", "generation_ms"), get(t, "timing", "e2e_latency_ms")] for t in turns]
    return r, samples


def collect(runs_dir):
    """Finished replays per setup, and the reason for each setup whose latest attempt failed."""
    found, failures = {}, {}
    for attempt in sorted(runs_dir.iterdir()) if runs_dir and runs_dir.exists() else []:
        log = (attempt / "run.log").read_text() if (attempt / "run.log").exists() else ""
        for setup in sorted(p for p in attempt.iterdir() if p.is_dir()):
            failures.pop(ALIASES.get(setup.name, setup.name), None)  # a later attempt supersedes an earlier failure
            for rep in sorted(setup.iterdir()):
                if rep.name != "mini" and (rep / "summary.json").exists():
                    r, smp = replay(rep)
                    if r["ok"]:
                        found.setdefault(ALIASES.get(setup.name, setup.name), []).append((r, smp))
        for line in log.splitlines():
            if "FAILED" in line:
                name = line.split()[1]
                failures[ALIASES.get(name, name)] = line.split("FAILED", 1)[1].strip(" :") or "did not finish"
    return found, failures


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "results")
    a = ap.parse_args()
    found, failures = collect(a.runs)
    methods, samples = [], {}
    for m in load(HERE / "methods.json")["methods"]:
        out = dict(m)
        reps = found.get(m["id"], [])
        if reps:
            runs = [r for r, _ in reps]
            out.update(status="ok", runs=runs, completion_s=statistics.median(r["completion_s"] for r in runs))
            samples[m["id"]] = {r["run"]: smp for r, smp in reps}
        elif m["id"] in failures:
            out.update(status="failed", reason=failures[m["id"]])
        else:
            out["status"] = "pending"
        methods.append(out)
    refs = load(HERE / "references.json")
    a.out.mkdir(parents=True, exist_ok=True)
    data = {"updated": datetime.now().strftime("%Y-%m-%d"), "workload": WORKLOAD, "hardware": HARDWARE,
            "methods": methods, "references": refs["systems"], "references_source": refs["source"],
            "references_retrieved": refs["retrieved"]}
    (a.out / "results.json").write_text(json.dumps(data, indent=1) + "\n")
    (a.out / "samples.json").write_text(json.dumps(
        {"columns": ["turn_id", "prompt_tokens", "cached_tokens", "output_tokens", "ttft_ms", "generation_ms", "e2e_ms"],
         "methods": samples}, separators=(",", ":")) + "\n")
    print(", ".join(f"{m['id']} {m['status']}" + (f" {m['completion_s'] / 60:.2f} min over {len(m['runs'])}" if m.get("runs") else "")
                    for m in methods))


if __name__ == "__main__":
    main()
