#!/usr/bin/env python3
"""Export a public, reproducible snapshot of the archived short-request benchmark.

Reads saved results only: no model, network, GPU query or inference is performed.
Usage: python3 export_results.py /path/to/benchmark-asset --output /path/to/output
"""

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


UPDATED = "2026-10-02"
WORKLOADS = ("json", "code", "prose")
PUBLIC_BASE = "/assets/benchmarks/qwen38-4090/"
ENGINES = {
    "cinference": {
        "engine": "Cinference",
        "repository": "https://github.com/jram4/ninfer-4090",
        "commit": "70ebb1290dc7abe246c20696a24d21f77faee8d4",
        "quantization": "NInfer Q4/Q5, Q8 output head (v3 container)",
        "kv_cache": "INT8",
    },
    "ninfer": {
        "engine": "NInfer (Erik 4090 port)",
        "repository": "https://github.com/eriknelson/ninfer-4090",
        "commit": "1bd56c9a1bdf457c6188391a9385d44d86e953aa",
        "quantization": "NInfer Q4/Q5, Q8 output head (v2 container)",
        "kv_cache": "INT8",
    },
    "llamacpp": {
        "engine": "llama.cpp + CUDA",
        "repository": "https://github.com/ggml-org/llama.cpp",
        "commit": "a4d880fd5c7f88713ded6db9f0111893bd78afa6",
        "quantization": "Unsloth UD-Q4_K_M; Q4_0 MTP sidecar",
        "kv_cache": "F16",
    },
    "exl3": {
        "engine": "ExLlamaV3",
        "repository": "https://github.com/turboderp-org/exllamav3",
        "commit": "d3739fd393337b1ff4d6c2a342b12f0c87a9592f",
        "quantization": "EXL3 4.00 bpw; DFlash2 draft 4.00 bpw where enabled",
        "kv_cache": "Q4 K/V",
    },
}


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quality_summary(workload, samples):
    if workload == "json":
        if not all(s["quality"].get("valid_json") and s["quality"].get("three_districts") for s in samples):
            raise ValueError("JSON quality records differ from the expected snapshot")
    else:
        if not all(s["completion_tokens"] == 512 and s["finish_reason"] in ("length", "max_new_tokens") for s in samples):
            raise ValueError("Expected truncated 512-token output")
        if workload == "code" and not all(s["quality"].get("python_syntax") is False and s["quality"].get("semantic_tests") == "not_run" for s in samples):
            raise ValueError("Code quality records differ from the expected snapshot")
        if workload == "prose" and not all(s["quality"]["words"] < 500 for s in samples):
            raise ValueError("Prose quality records differ from the expected snapshot")
    return {
        "json": "JSON parse and three-district structure passed (3/3); semantics not evaluated.",
        "code": "512-token limit reached; incomplete code; recorded fenced-code syntax check failed (3/3); semantic tests not run.",
        "prose": "512-token limit reached; fewer than requested 500 words; incomplete task.",
    }[workload]


def gpu_snapshot(csv):
    # Preserve card totals and interference evidence, without UUIDs or process identities.
    fields = [x.strip() for x in csv.split(",")]
    if len(fields) != 7:
        raise ValueError("Unexpected GPU snapshot format")
    keys = ("memory_used_mib", "memory_free_mib", "utilization_pct", "power_w", "temperature_c")
    return dict(zip(keys, map(float, fields[2:])))


def metric(row, key):
    return statistics.median(sample[key] for sample in row)


def checked_close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"Median mismatch: {actual} != {expected}")


def export(archive, output):
    supplementary = archive / "supplementary"
    http_dir = supplementary / "remote-evidence/results/http-bench-matched"
    native_dir = supplementary / "exl3-bench"
    samples, results, sources, prompts = [], [], [], {}

    def add_source(path):
        relative = path.relative_to(supplementary).as_posix()
        sources.append({"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size})
        return relative

    def add_result(label, workload, engine_id, configuration, cohort, grouped, summary):
        engine = ENGINES[engine_id]
        row = {
            "id": label + "-" + workload,
            "engine_id": engine_id,
            "engine": engine["engine"],
            "configuration": configuration,
            "cohort": cohort,
            "workload": workload,
            "decode_tps": None,
            "e2e_tps": None,
            "native_tps": None,
            "call_tps": None,
            "quantization": engine["quantization"],
            "kv_cache": engine["kv_cache"],
            "context_tokens": 4096,
            "max_output_tokens": 512,
            "repetitions": len(grouped),
            "commit": engine["commit"],
            "source_url": engine["repository"] + "/tree/" + engine["commit"],
            "samples_url": PUBLIC_BASE + "samples.json",
            "sample_ids": [sample["id"] for sample in grouped],
            "prompt_tokens": [sample["prompt_tokens"] for sample in grouped],
            "output_tokens": [sample["completion_tokens"] for sample in grouped],
            "finish_reasons": [sample["finish_reason"] for sample in grouped],
            "quality_summary": quality_summary(workload, grouped),
            "draft_acceptance": statistics.median(s["draft_acceptance"] for s in grouped)
            if all(s["draft_acceptance"] is not None for s in grouped)
            else None,
        }
        keys = (("decode_tps", "median_decode_tps"), ("e2e_tps", "median_end_to_end_output_tps")) if cohort == "http" else (
            ("native_tps", "median_exl3_native_generation_tps"), ("call_tps", "median_generation_call_output_tps")
        )
        for key, summary_key in keys:
            row[key] = metric(grouped, key)
            checked_close(row[key], summary[summary_key])
            row[key + "_range"] = [min(s[key] for s in grouped), max(s[key] for s in grouped)]
        if len(grouped) != 3 or {s["rep"] for s in grouped} != {0, 1, 2}:
            raise ValueError("Exactly three measured repetitions required")
        results.append(row)

    configurations = [
        ("cinference-int8-k0", "cinference", "AR"),
        ("cinference-int8-k3", "cinference", "MTP3"),
        ("cinference-int8-k7", "cinference", "MTP7"),
        ("ninfer-erik-int8-k0", "ninfer", "AR"),
        ("ninfer-erik-int8-k3", "ninfer", "MTP3"),
        ("ninfer-erik-int8-k5", "ninfer", "MTP5"),
        ("llama-udq4-k0", "llamacpp", "AR"),
        ("llama-udq4-k3", "llamacpp", "MTP3"),
        ("llama-udq4-k7", "llamacpp", "MTP7"),
    ]
    for label, engine_id, configuration in configurations:
        path = http_dir / (label + ".json")
        source = add_source(path)
        summary_path = http_dir / (label + ".summary.json")
        add_source(summary_path)
        summaries = {s["workload"]: s for s in read_json(summary_path)}
        grouped = {workload: [] for workload in WORKLOADS}
        for saved in read_json(path):
            workload = saved["workload"]
            if workload not in WORKLOADS:
                continue  # Warmup requests are explicitly excluded.
            request = saved["request"]
            thinking = request.get("enable_thinking", request.get("chat_template_kwargs", {}).get("enable_thinking"))
            if request["temperature"] != 0 or request["max_tokens"] != 512 or thinking is not False:
                raise ValueError("Unexpected request protocol")
            if request["presence_penalty"] != 0 or request["frequency_penalty"] != 0 or request["seed"] != 42:
                raise ValueError("Unexpected sampling protocol")
            response = saved["response"]
            usage, timings = response["usage"], response["timings"]
            cached = usage["prompt_tokens_details"]["cached_tokens"]
            if cached != 0:
                raise ValueError("Cached prefix detected")
            completion = response["choices"][0]["message"]["content"]
            item = {
                "id": label + "-" + workload + "-" + str(saved["rep"]),
                "result_id": label + "-" + workload,
                "cohort": "http", "workload": workload, "rep": saved["rep"], "utc": saved["utc"],
                "request": request, "completion": completion, "output_sha256": saved["output_sha256"],
                "completion_tokens": usage["completion_tokens"], "prompt_tokens": usage["prompt_tokens"],
                "cached_tokens": cached, "finish_reason": response["choices"][0]["finish_reason"],
                "decode_tps": saved["server_decode_tps"], "e2e_tps": saved["end_to_end_output_tps"],
                "client_wall_s": saved["wall_s"], "server_timings": timings,
                "draft_acceptance": saved.get("draft_acceptance"), "quality": saved["quality_check"],
                "gpu_before": gpu_snapshot(saved["gpu_before"]), "gpu_after": gpu_snapshot(saved["gpu_after"]),
                "source_file": source,
            }
            checked_close(item["decode_tps"], 1000 * (item["completion_tokens"] - 1) / timings["predicted_ms"])
            checked_close(item["e2e_tps"], item["completion_tokens"] / item["client_wall_s"])
            prompts.setdefault(workload, request["messages"])
            if prompts[workload] != request["messages"]:
                raise ValueError("HTTP prompt mismatch within comparison cohort")
            samples.append(item)
            grouped[workload].append(item)
        for workload in WORKLOADS:
            add_result(label, workload, engine_id, configuration, "http", grouped[workload], summaries[workload])

    for label, configuration in (
        ("exl3-ar-k0-cq4-cs4096", "AR"),
        ("exl3-mtp-k4-cq4-cs4096", "MTP4"),
        ("exl3-dflash2-k7-cq4-cs4096", "DFlash2 K7"),
    ):
        folder = native_dir / label
        summary_path = folder / (label + ".summary.json")
        add_source(summary_path)
        summaries = {s["workload"]: s for s in read_json(summary_path)}
        for workload in WORKLOADS:
            grouped = []
            for rep in range(3):
                path = folder / (label + "-" + workload + "-" + str(rep) + ".json")
                source = add_source(path)
                saved = read_json(path)
                raw = saved["raw_result"]
                if raw["cached_tokens"] != 0 or not saved["cold_prefix_verified"]:
                    raise ValueError("Native prefix cache detected")
                if saved["messages"] != prompts[workload] or saved["temperature"] != 0 or saved["seed"] != 42:
                    raise ValueError("Native prompt or sampling mismatch")
                item = {
                    "id": label + "-" + workload + "-" + str(rep), "result_id": label + "-" + workload,
                    "cohort": "native", "workload": workload, "rep": rep, "utc": saved["utc"],
                    "request": {"messages": saved["messages"], "temperature": 0, "seed": 42, "max_tokens": 512, "enable_thinking": False},
                    "completion": saved["completion"], "output_sha256": saved["output_sha256"],
                    "completion_tokens": raw["new_tokens"], "prompt_tokens": raw["prompt_tokens"], "cached_tokens": 0,
                    "finish_reason": raw["eos_reason"], "native_tps": saved["exl3_native_generation_tps"],
                    "call_tps": saved["generation_call_output_tps"], "generation_call_wall_s": saved["generation_call_wall_s"],
                    "time_generate_s": raw["time_generate"], "time_prefill_s": raw["time_prefill"],
                    "load_and_warmup_s": saved["model_load_and_warmup_s"],
                    "draft_acceptance": saved.get("draft_acceptance"), "quality": saved["quality_check"],
                    "gpu_before": gpu_snapshot(saved["gpu_before"]), "gpu_after": gpu_snapshot(saved["gpu_after"]),
                    "source_file": source,
                }
                checked_close(item["native_tps"], item["completion_tokens"] / item["time_generate_s"])
                checked_close(item["call_tps"], item["completion_tokens"] / item["generation_call_wall_s"])
                samples.append(item)
                grouped.append(item)
            add_result(label, workload, "exl3", configuration, "native", grouped, summaries[workload])

    if len(results) != 36 or len(samples) != 108 or len({s["id"] for s in samples}) != 108:
        raise ValueError("Incomplete benchmark snapshot")
    payload = {
        "schema_version": 1, "updated_at": UPDATED, "model": "Qwen3.8-27B",
        "hardware": {"gpu": "RTX 4090", "gpu_count": 1, "vram_gib": 24, "shared_machine": True, "driver": "570.124.06", "cuda": "12.8"},
        "protocol": {
            "id": "zedong-qwen38-short-v1", "context_tokens": 4096, "max_output_tokens": 512, "repetitions": 3,
            "temperature": 0, "thinking": False, "seed": 42, "presence_penalty": 0, "frequency_penalty": 0,
            "concurrency": 1, "prefix_cache": "disabled / observed cached_tokens=0", "prompts": prompts,
            "measured_prompt_tokens_range": [min(s["prompt_tokens"] for s in samples), max(s["prompt_tokens"] for s in samples)],
            "http_measured_samples": 81, "native_measured_samples": 27, "http_excluded_warmups": 9,
            "limitations": [
                "Different published quantizations and KV dtypes: compare deployment configurations, not isolated engine kernels.",
                "A single physical 4090 on a shared machine; snapshots do not establish exclusive GPU isolation.",
                "Code and prose hit the 512-token output cap. Recorded fenced-code syntax checks failed; semantic tests were not run. JSON structural checks passed.",
                "Three repetitions per workload. No streaming TTFT or confidence intervals were measured.",
                "Native EXL3 and HTTP timers have different boundaries and must remain separate cohorts.",
                "This 4K short-request protocol is not AA-AgentPerf-Local's 64K multi-turn protocol.",
            ],
        },
        "metrics": {
            "decode_tps": "(output_tokens - 1) / server_decode_seconds; first output token is accounted in prompt processing.",
            "e2e_tps": "output_tokens / client HTTP wall seconds, including prompt processing.",
            "native_tps": "output_tokens / EXL3 time_generate; includes the first decode token, excludes bulk prefill.",
            "call_tps": "output_tokens / in-process generation call seconds, including tokenization/prefill, excluding load/warmup.",
        },
        "results": results,
        "coverage": [
            {"name": ENGINES[key]["engine"], "status": "measured",
             "detail": "AR / MTP3 / MTP7" if key in ("cinference", "llamacpp") else "AR / MTP3 / MTP5" if key == "ninfer" else "AR / MTP4 / DFlash2 K7; separate timing cohort",
             "url": ENGINES[key]["repository"]}
            for key in ("llamacpp", "cinference", "ninfer", "exl3")
        ] + [
            {"name": "Unsloth native inference", "status": "pending", "detail": "Unsloth GGUF weights were used by llama.cpp. That does not test Unsloth's native Python inference route.", "url": "https://github.com/unslothai/unsloth"},
            {"name": "vLLM", "status": "pending", "detail": "Community 4090 recipes exist; local matched-protocol result pending.", "url": "https://github.com/vllm-project/vllm"},
            {"name": "SGLang", "status": "pending", "detail": "No local matched-protocol result yet.", "url": "https://github.com/sgl-project/sglang"},
        ],
        "public_reports": [
            {"name": "Artificial Analysis: local hardware leaderboard", "detail": "Includes Qwen3.8-27B on 5090 and other systems; no 4090 entry found as of 2026-10-02. 64K / 168-turn agent workload; not comparable with this short-request snapshot.", "url": "https://artificialanalysis.ai/hardware-inference-stack/laptops-workstations"},
            {"name": "Inference Atlas", "detail": "569 community records at checked commit b93f628; 127 Qwen3.8-27B records, none on RTX 4090. Accepts result JSON through reviewed pull requests.", "url": "https://0xbakeer.github.io/inference-atlas/"},
            {"name": "Qwen Local-Run Directory", "detail": "72 deployment recipes / 8 engines, including 4090. A source directory with evidence labels, rather than one controlled speed ranking.", "url": "https://local.host.impossibuild.ai/"},
            {"name": "Poor Paul's Benchmark", "detail": "Open GGUF benchmarking database. Checked current dataset has no Qwen3.8 or RTX 4090 records.", "url": "https://poorpaul.dev/"},
            {"name": "HyperQwen 4090 port: vLLM + DFlash2", "detail": "Author reports 237.9 code decode tok/s on a single 4090, 65K context, AutoRound W4A16, CUDA13 / driver595.84. Different workload and quantization; not reproduced here. Large raw result files not found in the checked tree.", "url": "https://github.com/sidnaZ/qwen38-27b-rtx4090/blob/main/RELEASE.md"},
            {"name": "Qwen3.8 speculative decoding benchmark", "detail": "Single 4090 / WSL2 / llama.cpp b10588, bartowski Q4_K_M, Q8 KV. MTP3 code 104.01 and JSON 104.32 tok/s on a larger 8K task matrix. Public raw JSONL/CSV; different protocol, not reproduced here.", "url": "https://github.com/kuotunyu/qwen38-speculative-decoding-benchmark/blob/main/QWEN38_REPORT.md"},
        ],
        "model_artifacts": [
            {"name": "NInfer target (v2)", "url": "https://huggingface.co/neroued/Qwen3.8-27B-NInfer", "revision": "3526913004b1cf552cb57b88d6a5c6f5e4a89a70", "sha256": "eec39564993d6e9c7d5e383382a760f093465c9d163ec9a1bd6b80199514bf3e"},
            {"name": "NInfer v3 converted container (same original payload)", "sha256": "efec7393d517dc3cdda1f8fa0f3333bd03ffe61610418f059d6758afcaece006"},
            {"name": "Unsloth UD-Q4_K_M", "url": "https://huggingface.co/unsloth/Qwen3.8-27B-GGUF", "revision": "4ca720788d1e01f1bff70c033e0d0028fd02e502", "sha256": "322e194ff79741c7baa497c240f677f54b201b0efab44ca8e50f122b39123482"},
            {"name": "Unsloth Q4_0 MTP sidecar", "url": "https://huggingface.co/unsloth/Qwen3.8-27B-GGUF", "revision": "4ca720788d1e01f1bff70c033e0d0028fd02e502", "sha256": "50d9ce5a6da381bbcfb31061cf73df94a90e6faf8efeddee379a9cb8f1501c6e"},
            {"name": "EXL3 4.00 bpw target", "url": "https://huggingface.co/r0b0tlab/Qwen3.8-27B-EXL3-4.00bpw", "revision": "3f1771b8c21f83cbb8e82169559ced9f38ca04e5"},
            {"name": "EXL3 4.00 bpw DFlash2 draft", "url": "https://huggingface.co/r0b0tlab/Qwen3.8-27B-DFlash2-EXL3-4.00bpw", "revision": "265b5240592907d2d55ff0dc4d5f66569692604d"},
        ],
    }
    sample_payload = {"schema_version": 1, "protocol_id": payload["protocol"]["id"], "source_files": sources, "samples": samples}
    output.mkdir(parents=True, exist_ok=True)
    for filename, data in (("results.json", payload), ("samples.json", sample_payload)):
        (output / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"result_rows": len(results), "measured_samples": len(samples), "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.archive, args.output)
