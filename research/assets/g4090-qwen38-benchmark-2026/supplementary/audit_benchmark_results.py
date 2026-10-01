#!/usr/bin/env python3
"""Audit saved benchmark evidence; never contact a model server or GPU."""
import argparse
import collections
import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics

WORKLOADS = ("json", "code", "prose")
METRICS = {
    "median_decode_tps": "server_decode_tps",
    "median_end_to_end_output_tps": "end_to_end_output_tps",
    "median_prefill_tps": "server_prefill_tps",
    "median_server_prompt_ms": "server_prompt_ms",
    "median_draft_acceptance": "draft_acceptance",
}
GPU_FIELDS = ("memory_used_mib", "memory_free_mib", "utilization_percent",
              "power_watts", "temperature_c")

def median(values):
    numbers = [x for x in values if isinstance(x, (int, float)) and math.isfinite(x)]
    return statistics.median(numbers) if numbers else None

def value_range(values):
    numbers = [x for x in values if isinstance(x, (int, float)) and math.isfinite(x)]
    return {"min": min(numbers), "max": max(numbers), "median": median(numbers)} if numbers else None

def read_snapshot(path, sources, pending):
    try:
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("file changed during read")
        obj = json.loads(data)
        sources.append({"path": str(path), "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "mtime_ns": after.st_mtime_ns})
        return obj
    except (OSError, ValueError) as error:
        pending.append({"path": str(path), "reason": str(error)})
        return None

def response_info(row):
    response = row.get("response") or {}
    choices = response.get("choices") or [{}]
    choice = choices[0]
    usage, timings = response.get("usage") or {}, response.get("timings") or {}
    cached = {
        "timings_cache_n": timings.get("cache_n"),
        "usage_cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
    }
    return choice.get("finish_reason"), cached

def gpu_range(rows):
    samples, errors = [], []
    for row in rows:
        for phase in ("gpu_before", "gpu_after"):
            raw = row.get(phase)
            if not isinstance(raw, str):
                if raw is not None:
                    errors.append({"phase": phase, "value": raw})
                continue
            parts = [x.strip() for x in raw.split(",")]
            try:
                sample = {"index": int(parts[0]), "uuid": parts[1]}
                sample.update(zip(GPU_FIELDS, [float(x) for x in parts[2:7]]))
                if len(parts) != 7:
                    raise ValueError("expected seven GPU snapshot columns")
                samples.append(sample)
            except (ValueError, IndexError):
                errors.append({"phase": phase, "value": raw})
    return {"samples": len(samples),
            "gpu_indices": sorted({s["index"] for s in samples}),
            "gpu_uuids": sorted({s["uuid"] for s in samples}),
            "ranges": {key: value_range([s[key] for s in samples]) for key in GPU_FIELDS},
            "snapshot_errors": errors,
            "other_process_attribution": "Unavailable: snapshots contain card totals, not process IDs or per-process memory. Shared-server isolation is not established."}

def audit_workload(label, workload, rows, published, expected):
    selected = [r for r in rows if r.get("workload") == workload]
    successful = [r for r in selected if "error" not in r]
    failed = [r for r in selected if "error" in r]
    repetitions = [r.get("rep") for r in selected]
    complete_reps = len(selected) == expected and sorted(repetitions) == list(range(expected))
    metrics = {name: median([r.get(key) for r in successful]) for name, key in METRICS.items()}
    comparisons = {}
    if isinstance(published, dict):
        for name, actual in metrics.items():
            reported = published.get(name)
            equal = actual is None and reported is None
            if isinstance(actual, (int, float)) and isinstance(reported, (int, float)):
                equal = math.isclose(actual, reported, rel_tol=1e-9, abs_tol=1e-9)
            comparisons[name] = {"raw": actual, "published": reported, "match": equal}
        comparisons["successful_reps"] = {"raw": len(successful), "published": published.get("successful_reps"),
                                            "match": len(successful) == published.get("successful_reps")}
        comparisons["failed_reps"] = {"raw": len(failed), "published": published.get("failed_reps"),
                                       "match": len(failed) == published.get("failed_reps")}
    zero_checks = [{"rep": r.get("rep"),
                    "presence_penalty_explicit_zero": r.get("request", {}).get("presence_penalty") == 0,
                    "frequency_penalty_explicit_zero": r.get("request", {}).get("frequency_penalty") == 0}
                   for r in selected]
    penalty_ok = bool(selected) and all(x["presence_penalty_explicit_zero"] and
                                        x["frequency_penalty_explicit_zero"] for x in zero_checks)
    cache = [dict({"rep": r.get("rep")}, **response_info(r)[1]) for r in successful]
    cached_values = [v for c in cache for k, v in c.items() if k != "rep" and isinstance(v, (int, float))]
    cache_zero = bool(cached_values) and all(v == 0 for v in cached_values)
    quality = [r.get("quality_check") for r in successful]
    quality_counts = {}
    for check in quality:
        for key, value in (check or {}).items():
            quality_counts.setdefault(key, collections.Counter())[str(value)] += 1
    finished = [response_info(r)[0] for r in successful]
    summary_ok = bool(comparisons) and all(c["match"] for c in comparisons.values())
    completed = complete_reps and summary_ok
    return {"label": label, "workload": workload,
            "status": "complete" if completed else "pending_or_inconsistent",
            "expected_reps": expected, "observed_reps": len(selected), "repetition_ids": repetitions,
            "successful_reps": len(successful), "failed_reps": len(failed),
            "errors": [{"rep": r.get("rep"), "error": r.get("error")} for r in failed],
            **metrics, "summary_consistency": comparisons,
            "completion_tokens": [r.get("completion_tokens") for r in successful],
            "completion_token_range": value_range([r.get("completion_tokens") for r in successful]),
            "finish_reasons": finished, "length_capped_reps": finished.count("length"),
            "quality_checks": quality,
            "quality_counts": {k: dict(v) for k, v in quality_counts.items()},
            "output_sha256": [r.get("output_sha256") for r in successful],
            "penalty_checks": zero_checks, "penalties_explicit_zero": penalty_ok,
            "cache_observations": cache, "all_observed_cached_tokens_zero": cache_zero,
            "request_controls": [{"rep": r.get("rep"), "temperature": r.get("request", {}).get("temperature"),
                                   "seed": r.get("request", {}).get("seed"),
                                   "max_tokens": r.get("request", {}).get("max_tokens"),
                                   "enable_thinking": r.get("request", {}).get("enable_thinking"),
                                   "chat_template_kwargs": r.get("request", {}).get("chat_template_kwargs"),
                                   "cache_prompt": r.get("request", {}).get("cache_prompt"),
                                   "prompt_sha256": hashlib.sha256(json.dumps(r.get("request", {}).get("messages"), sort_keys=True).encode()).hexdigest()}
                                  for r in selected],
            "gpu_snapshot_range": gpu_range(selected),
            "primary_matched_speed_eligible": completed and penalty_ok and cache_zero and not failed,
            "quality_interpretation": "Transport success and valid syntax/JSON checks do not prove semantic task correctness; length-capped code/prose are incomplete outputs."}

def audit_dataset(root, name, expected):
    directory = root / "results" / name
    sources, pending, loaded = [], [], {}
    for path in sorted(directory.glob("*.json")):
        obj = read_snapshot(path, sources, pending)
        if obj is not None:
            loaded[path.name] = obj
    result = {"directory": str(directory), "input_sources": sources,
              "pending_or_unreadable_files": pending, "labels": []}
    for filename, rows in loaded.items():
        if filename.endswith((".summary.json", ".runs.json")) or not isinstance(rows, list):
            continue
        if not rows or not all(isinstance(r, dict) and "workload" in r for r in rows):
            continue
        label = rows[0].get("label", filename[:-5])
        published_rows = loaded.get(label + ".summary.json") or []
        published = {r.get("workload"): r for r in published_rows if isinstance(r, dict)}
        events = [e for fname, obj in loaded.items() if fname.endswith(".runs.json") and isinstance(obj, list)
                  for e in obj if isinstance(e, dict) and e.get("label") == label]
        results = [audit_workload(label, w, rows, published.get(w), expected) for w in WORKLOADS]
        result["labels"].append({"label": label, "raw_file": str(directory / filename),
                                 "summary_present": label + ".summary.json" in loaded,
                                 "complete": all(r["status"] == "complete" for r in results),
                                 "server_run_events": events,
                                 "warmup": {"observed": len([r for r in rows if r.get("workload") == "warmup"]),
                                            "errors": [r.get("error") for r in rows if r.get("workload") == "warmup" and "error" in r]},
                                 "workloads": results})
    result["completed_labels"] = [x["label"] for x in result["labels"] if x["complete"]]
    result["pending_labels"] = [x["label"] for x in result["labels"] if not x["complete"]]
    result["interpretation"] = ("Primary matched requests explicitly set presence/frequency penalties to zero; each eligible result still carries its quality and shared-GPU caveats."
                                if name == "http-bench-matched" else
                                "Initial diagnostic only. Requests omit explicit penalties; the reported Cinference default presence penalty was 1.5. Do not combine with primary matched rankings.")
    if name != "http-bench-matched":
        for label in result["labels"]:
            for work in label["workloads"]:
                work["primary_matched_speed_eligible"] = False
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.home() / "qwen38-4090")
    parser.add_argument("--expected-reps", type=int, default=3)
    args = parser.parse_args()
    if args.expected_reps < 1:
        parser.error("--expected-reps must be positive")
    sources, pending, clones = [], [], []
    for name in ("remote-git-clones-ninfer.json", "git-clone-provenance-exl3-hyperqwen.json", "llama-git-clone.json"):
        path = args.root / "results" / name
        obj = read_snapshot(path, sources, pending)
        if obj is not None:
            clones.append({"path": str(path), "record": obj})
    audit = {"schema_version": 1, "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "generated_by": str(Path(__file__).resolve()),
             "execution_scope": "Read saved JSON only; no server requests, GPU query, inference, or benchmark execution.",
             "metric_definitions": {"server_decode_tps": "Copied from server predicted_per_second; current NInfer/llama exclude the first output token from predicted_ms.",
                                    "end_to_end_output_tps": "completion_tokens / client wall_s; includes the full HTTP request.",
                                    "server_prompt_ms": "Server prompt-processing time; not client streaming TTFT.",
                                    "quality": "Recorded JSON/syntax/word checks only; generated semantic tests were not executed.",
                                    "gpu": "MiB/card totals from saved nvidia-smi snapshots; other process identities cannot be inferred."},
             "initial_diagnostic": audit_dataset(args.root, "http-bench", args.expected_reps),
             "primary_matched": audit_dataset(args.root, "http-bench-matched", args.expected_reps),
             "git_clone_evidence": {"sources": sources, "records": clones, "pending": pending}}
    destination = args.root / "results" / "primary-benchmark-audit.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(audit, indent=2) + "\n")
    temporary.replace(destination)
    print("Saved", destination)
    for name in ("initial_diagnostic", "primary_matched"):
        result = audit[name]
        print(name, "complete:", ", ".join(result["completed_labels"]) or "none",
              "pending:", ", ".join(result["pending_labels"]) or "none")
        for label in result["labels"]:
            if label["complete"]:
                for r in label["workloads"]:
                    print(label["label"], r["workload"], "decode=", r["median_decode_tps"],
                          "e2e=", r["median_end_to_end_output_tps"], "failed=", r["failed_reps"],
                          "penalty0=", r["penalties_explicit_zero"], "cached0=", r["all_observed_cached_tokens_zero"])

if __name__ == "__main__":
    main()
