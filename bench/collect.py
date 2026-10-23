"""Build the page data (results.json, samples.json) from bench/methods.json, bench/references.json and the run tree.

usage: python3 bench/collect.py [--runs RUNS_DIR] [--out results/]
A method with no finished full replay under RUNS_DIR/<method>/ is listed as pending; a run whose log says FAIL is
listed as failed with the reason. Completion time is the median over full replays (AA reports one).
"""

import argparse
import csv
import json
import statistics
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORKLOAD = {
    "name": "AA-AgentPerf-Local default replay (agentperf-default-v1)",
    "runner": "agentperf-local 0.3.4",
    "tasks": 8, "turns": 168, "tool_calls": 172, "output_tokens": 30883, "largest_prompt_tokens": 56000,
    "context_tokens": 65536, "concurrency": 1, "output_policy": "exact (ignore_eos, recorded length)",
    "sampling": "temperature 0.7, top_p 0.8, top_k 20",
}
HARDWARE = {
    "gpu": "NVIDIA GeForce RTX 4090", "memory_gb": 24, "bandwidth_gbs": 1008, "power_limit_w": 450,
    "msrp_usd": 1599, "rest_of_system_usd": 2500, "driver": "570.124.06", "cuda": "12.8",
    "cpu": "Intel Xeon Silver 4210", "shared": "one card of a shared four-card server",
}
def load(path):
    return json.loads(Path(path).read_text())


def turns_of(run):
    return [json.loads(line) for line in (run / "turns.jsonl").read_text().splitlines() if line.strip()]


def get(d, *keys):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def gpu_stats(attempt, gpu, start, end):
    """Energy (Wh) and mean power over [start, end], peak memory over the whole attempt, from gpus.csv."""
    path = attempt / "gpus.csv"
    if not path.exists():
        return None, None, None
    energy = 0.0; watts = []; peak = 0.0; last = None
    for row in csv.reader(path.open()):
        if len(row) < 7 or row[1].strip() != str(gpu):
            continue
        try:
            t = datetime.strptime(row[0].strip(), "%Y/%m/%d %H:%M:%S.%f").timestamp()
            mem, pw = float(row[3]), float(row[4])
        except ValueError:
            continue
        peak = max(peak, mem)
        if start <= t <= end:
            if last is not None:
                energy += pw * (t - last) / 3600
            watts.append(pw); last = t
    return (energy or None), (statistics.mean(watts) if watts else None), (peak / 1024 if peak else None)


def run_result(attempt, run, gpu):
    s = load(run / "summary.json")
    tot = s["totals"]
    turns = turns_of(run)
    ttft = [get(t, "timing", "time_to_first_token_ms") for t in turns]
    gen = [get(t, "timing", "generation_ms") for t in turns]
    unc = [get(t, "tokens", "server_uncached_prompt_tokens") for t in turns]
    prefill_s = sum(x for x in ttft if x) / 1000
    prefill_tps = sum(unc) / prefill_s if unc and None not in unc and prefill_s else None
    start = datetime.fromisoformat(s["started_at"]).timestamp(); end = datetime.fromisoformat(s["ended_at"]).timestamp()
    energy, power, peak = gpu_stats(attempt, gpu, start, end)
    r = {
        "run": f"{attempt.name}/{run.name}",
        "ok": bool(s.get("success")) and tot["failed_turns"] == 0,
        "completion_s": tot["total_inference_latency_ms"] / 1000,
        "output_tps": s.get("output_tokens_per_second"),
        "prefill_tps": prefill_tps,
        "ttft_p50_ms": get(s, "latency_distributions_ms", "time_to_first_token", "p50"),
        "prefill_s": prefill_s,
        "generation_s": sum(x for x in gen if x) / 1000,
        "cached_tokens": tot.get("total_server_cached_prompt_tokens"),
        "uncached_tokens": tot.get("total_server_uncached_prompt_tokens"),
        "output_tokens": tot.get("total_server_output_tokens"),
        "energy_wh": energy, "avg_power_w": power, "peak_mem_gb": peak,
    }
    samples = [[get(t, "turn_id"), get(t, "tokens", "server_prompt_tokens"), get(t, "tokens", "server_cached_prompt_tokens"),
                get(t, "tokens", "server_output_tokens"), get(t, "timing", "time_to_first_token_ms"),
                get(t, "timing", "generation_ms"), get(t, "timing", "e2e_latency_ms")] for t in turns]
    return r, samples


def method_result(m, runs_dir):
    base = runs_dir / m["id"] if runs_dir else None
    attempts = sorted(base.iterdir()) if base and base.exists() else []
    results, samples, failure = [], {}, None
    for attempt in attempts:
        log = (attempt / "run.log").read_text() if (attempt / "run.log").exists() else ""
        gpu = next((w.split("=")[1] for w in log.split() if w.startswith("gpu=")), "1")
        for run in sorted(attempt.glob("full-*")):
            if (run / "summary.json").exists():
                r, smp = run_result(attempt, run, gpu)
                if r["ok"]:
                    results.append(r); samples[r["run"]] = smp
        if "FAIL" in log:
            failure = log.split("FAIL", 1)[1].splitlines()[0].strip()
    out = dict(m)
    if results:
        out["status"] = "ok"
        out["runs"] = results
        mid = sorted(results, key=lambda r: r["completion_s"])[(len(results) - 1) // 2]
        for k in ("completion_s", "output_tps", "prefill_tps", "ttft_p50_ms", "energy_wh", "avg_power_w", "peak_mem_gb",
                  "prefill_s", "generation_s"):
            out[k] = mid[k]
    elif failure:
        out["status"], out["reason"] = "failed", m.get("reason") or failure
    else:
        out["status"] = "pending"
    return out, samples


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "results")
    a = ap.parse_args()
    meta, refs = load(HERE / "methods.json"), load(HERE / "references.json")
    methods, samples = [], {}
    for m in meta["methods"]:
        r, smp = method_result(m, a.runs)
        r["engine_url"] = meta["engines"][m["engine"]]["url"]
        r["weights_source"] = meta["weights"][m["weights"]]
        methods.append(r)
        if smp:
            samples[m["id"]] = smp
    references = [dict(s, decodingText=(s["decoding"] + " " + str(s["draft"])) if s.get("draft") else s["decoding"])
                  for s in refs["systems"]]
    a.out.mkdir(parents=True, exist_ok=True)
    data = {"updated": datetime.now().strftime("%Y-%m-%d"), "workload": WORKLOAD, "hardware": HARDWARE,
            "methods": methods, "references": references, "references_source": refs["source"]}
    (a.out / "results.json").write_text(json.dumps(data, indent=1) + "\n")
    (a.out / "samples.json").write_text(json.dumps(
        {"columns": ["turn_id", "prompt_tokens", "cached_tokens", "output_tokens", "ttft_ms", "generation_ms", "e2e_ms"],
         "methods": samples}, separators=(",", ":")) + "\n")
    print(f"{sum(m['status'] == 'ok' for m in methods)} measured, {sum(m['status'] == 'pending' for m in methods)} pending, "
          f"{sum(m['status'] == 'failed' for m in methods)} failed -> {a.out}")


if __name__ == "__main__":
    main()
