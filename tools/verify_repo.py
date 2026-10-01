#!/usr/bin/env python3
"""Check archive integrity and recompute every published measurement offline."""

import argparse
import hashlib
import json
import math
import os
import re
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "archives/public-files.json"
EXCLUDED = {".git", ".local", "dist", ".cache", "__pycache__", "node_modules", "vendor", "_site", ".jekyll-cache"}
PRIVATE_PATTERNS = [
    re.compile(r"/Users" + r"/(?!LOCAL_USER(?:/|\b))[^/\s\"']+"),
    re.compile(r"/home" + r"/(?!REMOTE_USER(?:/|\b))[^/\s\"']+"),
    re.compile(r"GPU-[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}"),
    re.compile(r"(?:sk-(?:proj-|ant-)?[A-Za-z0-9_\-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{20,})"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)authorization[\"']?\s*[:=]\s*[\"']?(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{20,}"),
]


def public_files():
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED)
        for name in sorted(files):
            path = Path(directory) / name
            if path == MANIFEST or name in {".DS_Store"} or name.startswith("._") or path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_symlink():
                raise ValueError("Public symlinks require explicit review: " + str(path.relative_to(ROOT)))
            yield path


def check(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, label):
    check(math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9), label)


def inventory():
    records = []
    for path in public_files():
        raw = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            check(path.suffix == ".png", "Unexpected binary public file: " + relative)
        else:
            check(not any(p.search(text) for p in PRIVATE_PATTERNS), "Private identifier or credential pattern in " + relative)
        check(not path.name.startswith(".env") or path.name == ".env.example", "Environment file cannot be published: " + relative)
        records.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return sorted(records, key=lambda r: r["path"])


def verify_measurements():
    folder = ROOT / "site/assets/benchmarks/qwen38-4090"
    results = json.loads((folder / "results.json").read_text())
    evidence = json.loads((folder / "samples.json").read_text())
    samples = evidence["samples"]
    rows = results["results"]
    check(len(samples) == 108 and len(rows) == 36, "Expected the saved 108-sample, 36-row snapshot")
    check(len({s["id"] for s in samples}) == len(samples), "Duplicate sample IDs")
    check(len({r["id"] for r in rows}) == len(rows), "Duplicate result IDs")
    check(len(evidence["source_files"]) == 48, "Expected 48 original source files")
    check(sum(s["cohort"] == "http" for s in samples) == 81, "HTTP sample count")
    check(sum(s["cohort"] == "native" for s in samples) == 27, "Native sample count")
    check(sum(c["status"] == "pending" for c in results["coverage"]) == 3, "Unmeasured schemes must remain pending")
    index = {s["id"]: s for s in samples}
    sources = {s["path"] for s in evidence["source_files"]}
    for sample in samples:
        label = sample["id"]
        check(sample["source_file"] in sources, label + ": missing source hash record")
        check(sample["cached_tokens"] == 0, label + ": nonzero prefix cache")
        check(34 <= sample["prompt_tokens"] <= 77, label + ": input token count")
        check(sample["request"]["messages"] == results["protocol"]["prompts"][sample["workload"]], label + ": prompt changed")
        check(sample["request"]["temperature"] == 0 and sample["request"]["max_tokens"] == 512, label + ": sampling changed")
        check(hashlib.sha256(sample["completion"].encode()).hexdigest() == sample["output_sha256"], label + ": completion hash")
        tokens = sample["completion_tokens"]
        if sample["cohort"] == "http":
            close(sample["decode_tps"], (tokens - 1) / (sample["server_timings"]["predicted_ms"] / 1000), label + ": decode formula")
            close(sample["e2e_tps"], tokens / sample["client_wall_s"], label + ": HTTP formula")
            check(sample["request"]["presence_penalty"] == sample["request"]["frequency_penalty"] == 0, label + ": penalties changed")
        else:
            close(sample["native_tps"], tokens / sample["time_generate_s"], label + ": native formula")
            close(sample["call_tps"], tokens / sample["generation_call_wall_s"], label + ": native call formula")
        if sample["workload"] == "json":
            check(sample["quality"]["valid_json"] and sample["quality"]["three_districts"], label + ": JSON quality")
            check(len(json.loads(sample["completion"])["districts"]) == 3, label + ": JSON structure")
        else:
            check(tokens == 512 and sample["finish_reason"] in {"length", "max_new_tokens"}, label + ": expected truncated output")
            if sample["workload"] == "code":
                check(sample["quality"]["python_syntax"] is False and sample["quality"]["semantic_tests"] == "not_run", label + ": quality claims changed")
            else:
                check(sample["quality"]["words"] < 500, label + ": prose quality claims changed")
    consumed = []
    for row in rows:
        grouped = [index[key] for key in row["sample_ids"]]
        consumed.extend(row["sample_ids"])
        check(len(grouped) == 3 and {s["rep"] for s in grouped} == {0, 1, 2}, row["id"] + ": repetitions")
        check(all(s["result_id"] == row["id"] and s["workload"] == row["workload"] and s["cohort"] == row["cohort"] for s in grouped), row["id"] + ": mixed samples")
        metrics = ("decode_tps", "e2e_tps") if row["cohort"] == "http" else ("native_tps", "call_tps")
        for key in metrics:
            values = [s[key] for s in grouped]
            close(row[key], statistics.median(values), row["id"] + ": median " + key)
            check(row[key + "_range"] == [min(values), max(values)], row["id"] + ": range " + key)
    check(len(consumed) == len(set(consumed)) == len(samples), "Every sample must appear in exactly one result")
    return {"results": len(rows), "samples": len(samples), "source_hash_records": len(sources), "metric_formulas_checked": len(samples) * 2}


def verify_local_originals():
    local = ROOT / ".local/originals/llm-inference"
    check(local.is_dir(), "Complete local original archive is not present in this checkout")
    manifest = json.loads((ROOT / "archives/original-files.json").read_text())
    for record in manifest["files"]:
        path = local / record["path"]
        if record.get("kind") == "symlink":
            check(path.is_symlink() and os.readlink(path) == record["target"], "Local original symlink changed: " + record["path"])
        else:
            check(path.is_file(), "Missing local original: " + record["path"])
            raw = path.read_bytes()
            check(len(raw) == record["bytes"] and hashlib.sha256(raw).hexdigest() == record["original_sha256"], "Original hash mismatch: " + record["path"])
    return manifest["file_count"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-manifest", action="store_true", help="Refresh public file hashes after intended edits; measurement/privacy checks still run")
    parser.add_argument("--local-originals", action="store_true", help="Also hash the complete ignored local original cache")
    args = parser.parse_args()
    actual = inventory()
    report = verify_measurements()
    if args.local_originals:
        report["local_original_files_verified"] = verify_local_originals()
    if args.update_manifest:
        MANIFEST.write_text(json.dumps({"schema_version": 1, "hash_semantics": "SHA-256 of the public repository files; excludes this manifest and ignored local/build directories", "files": actual}, indent=2) + "\n")
    expected = json.loads(MANIFEST.read_text())["files"]
    check(actual == expected, "Public file inventory/hash changed; review edits then use --update-manifest")
    report["public_files_verified"] = len(actual)
    print(json.dumps(report, indent=2))
