#!/usr/bin/env python3
"""EXL3 native metrics, one fresh process per request. --dry-run never imports torch."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time


def read_helper(path):
    spec = importlib.util.spec_from_file_location("benchmark_cases", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def worker(args, helper):
    # The orchestrator sets CUDA_VISIBLE_DEVICES before this separate process imports torch.
    import torch
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from exllamav3 import Generator, model_init

    torch.set_num_threads(4)
    torch.manual_seed(42)
    parser = argparse.ArgumentParser()
    model_init.add_args(parser, cache=True, add_sampling_args=True, add_draft_model_args=True,
                        default_cache_size=args.context, default_recurrent_cache_size=0.0)
    flags = ["-m", str(args.target), "-cs", str(args.context), "-cq", "4", "-temp", "0",
             "-ndt", str(args.draft_tokens)]
    if args.mode == "mtp":
        flags += ["-mtp"]
    elif args.mode == "dflash2":
        flags += ["-dm", str(args.draft)]
    model_args = parser.parse_args(flags)
    row = {"label": args.label, "mode": args.mode, "workload": args.workload, "rep": args.rep,
           "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "model_flags": flags,
           "torch": torch.__version__, "torch_cuda": torch.version.cuda,
           "cold_prefix_method": "fresh process and fresh Generator per request",
           "cases_helper_sha256": hashlib.sha256(args.cases_helper.read_bytes()).hexdigest(),
           "source": json.loads((args.repo / "SOURCE_PROVENANCE.json").read_text()),
           "gpu_before": helper.gpu_snapshot(args.gpu)}
    load_start = time.perf_counter()
    model, config, cache, tokenizer, draft_model, draft_config, draft_cache = model_init.init(model_args)
    torch.cuda.synchronize()
    row["model_load_and_warmup_s"] = time.perf_counter() - load_start
    generator = Generator(model=model, cache=cache, tokenizer=tokenizer,
                          draft_model=draft_model, draft_cache=draft_cache,
                          num_draft_tokens=args.draft_tokens, recurrent_cache_size=0, max_batch_size=1,
                          max_chunk_size=args.context)
    # Use the exact downloaded HF Jinja template rather than chat.py's example system prompt.
    template_path = args.target / "chat_template.jinja"
    template_text = template_path.read_text()
    template_env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    def raise_exception(message):
        raise ValueError(message)
    template_env.globals["raise_exception"] = raise_exception
    messages = [{"role": "user", "content": helper.CASES[args.workload]}]
    rendered = template_env.from_string(template_text).render(
        messages=messages, add_generation_prompt=True, enable_thinking=False)
    if not rendered.endswith("<think>\n\n</think>\n\n"):
        raise ValueError("HF template did not produce the expected thinking-disabled suffix")
    row.update({"messages": messages, "enable_thinking": False, "max_tokens": args.max_tokens,
                "seed": 42, "temperature": 0, "rendered_prompt": rendered,
                "rendered_prompt_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
                "chat_template_sha256": hashlib.sha256(template_text.encode()).hexdigest()})
    stop_conditions = list(config.eos_token_id_list or [])
    if tokenizer.eos_token_id is not None:
        stop_conditions.append(tokenizer.eos_token_id)
    stop_conditions = list(dict.fromkeys(stop_conditions))
    torch.cuda.synchronize()
    start = time.perf_counter()
    completion, raw = generator.generate(
        rendered, max_new_tokens=args.max_tokens, seed=42,
        sampler=model_init.get_arg_sampler(model_args), encode_special_tokens=True,
        add_bos=False, completion_only=True, return_last_results=True,
        token_healing=False, stop_conditions=stop_conditions)
    torch.cuda.synchronize()
    row["generation_call_wall_s"] = time.perf_counter() - start
    def json_value(value):
        if isinstance(value, torch.Tensor):
            return value.detach().cpu().tolist()
        if isinstance(value, dict):
            return {key: json_value(item) for key, item in value.items() if key != "job"}
        if isinstance(value, (list, tuple)):
            return [json_value(item) for item in value]
        return value
    row["raw_result"] = json_value(raw)  # Excludes only the live Python Job object.
    row["completion"] = completion
    row["output_sha256"] = hashlib.sha256(completion.encode()).hexdigest()
    row["quality_check"] = helper.check_output(args.workload, completion)
    row["gpu_after"] = helper.gpu_snapshot(args.gpu)
    row["cold_prefix_verified"] = raw.get("cached_tokens") == 0
    tokens, generate_s = raw["new_tokens"], raw["time_generate"]
    row["exl3_native_generation_tps"] = tokens / generate_s if generate_s > 0 else None
    row["generation_call_output_tps"] = tokens / row["generation_call_wall_s"]
    draft_total = raw.get("accepted_draft_tokens", 0) + raw.get("rejected_draft_tokens", 0)
    row["draft_acceptance"] = raw.get("accepted_draft_tokens", 0) / draft_total if draft_total else None
    row["metric_definition"] = {
        "exl3_native_generation_tps": "new_tokens / time_generate; EXL3 N convention",
        "time_generate": "first generation/draft forward start to EOS; includes first decode, excludes bulk prefill",
        "generation_call_wall_s": "in-process generate call including tokenization, prefill and decode; excludes model load/warmup",
        "time_prefill": "native bulk-prefill interval, not measured client TTFT",
        "http_comparable": False,
    }
    args.result.write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n")
    if not row["cold_prefix_verified"]:
        raise RuntimeError(f"Expected cold prefix, got cached_tokens={raw.get('cached_tokens')}")


def main():
    root = Path.home() / "qwen38-4090"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["ar", "mtp", "dflash2"], required=True)
    parser.add_argument("--label")
    parser.add_argument("--target", type=Path, default=root / "models/Qwen3.8-27B-EXL3-4.00bpw")
    parser.add_argument("--draft", type=Path, default=root / "models/Qwen3.8-27B-DFlash2-EXL3-4.00bpw")
    parser.add_argument("--repo", type=Path, default=root / "repos/exllamav3-git")
    parser.add_argument("--cases-helper", type=Path, default=Path(__file__).with_name("benchmark_http.py"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--gpu", type=int, default=3)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--context", type=int, default=4096)
    parser.add_argument("--draft-tokens", type=int, default=7)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--workload", help=argparse.SUPPRESS)
    parser.add_argument("--rep", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--result", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.label = args.label or "exl3-" + args.mode
    if args.mode == "ar":
        args.draft_tokens = 0
    args.draft_block_size = None
    if args.mode == "dflash2":
        model_config = json.loads((args.draft / "config.json").read_text())
        args.draft_block_size = model_config["dflash_config"]["block_size"]
        if not 1 <= args.draft_tokens < args.draft_block_size:
            parser.error(f"DFlash2 draft_tokens must be 1..{args.draft_block_size - 1} "
                         f"for this model (block_size={args.draft_block_size}); got {args.draft_tokens}")
    helper = read_helper(args.cases_helper)
    if args.dry_run:
        print(json.dumps({"mode": args.mode, "target": str(args.target), "draft": str(args.draft),
                          "draft_tokens": args.draft_tokens, "draft_block_size": args.draft_block_size, "context": args.context,
                          "max_tokens": args.max_tokens, "reps": args.reps, "workloads": helper.CASES,
                          "cold_prefix": "fresh process per request", "gpu_operations": "none"}, indent=2))
        return
    args.out.mkdir(parents=True, exist_ok=True)
    if args.worker:
        worker(args, helper)
        return
    env = os.environ.copy()
    env.update({"CUDA_VISIBLE_DEVICES": str(args.gpu), "MAX_JOBS": "4", "TORCH_CUDA_ARCH_LIST": "8.9"})
    env["PYTHONPATH"] = str(args.repo) + os.pathsep + env.get("PYTHONPATH", "")
    rows = []
    for workload in helper.CASES:
        for rep in range(args.reps):
            result = args.out / f"{args.label}-{workload}-{rep}.json"
            log = result.with_suffix(".log")
            command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--mode", args.mode,
                       "--label", args.label, "--target", str(args.target), "--draft", str(args.draft),
                       "--repo", str(args.repo), "--cases-helper", str(args.cases_helper),
                       "--out", str(args.out), "--gpu", str(args.gpu), "--context", str(args.context),
                       "--max-tokens", str(args.max_tokens), "--draft-tokens", str(args.draft_tokens),
                       "--workload", workload, "--rep", str(rep), "--result", str(result)]
            started = time.perf_counter()
            with log.open("w") as output:
                try:
                    finished = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT,
                                              env=env, timeout=args.timeout)
                    row = json.loads(result.read_text()) if result.exists() else {
                        "label": args.label, "mode": args.mode, "workload": workload, "rep": rep}
                    if finished.returncode != 0:
                        row["error"] = {"exit_code": finished.returncode, "log": str(log)}
                except subprocess.TimeoutExpired:
                    row = {"label": args.label, "workload": workload, "rep": rep,
                           "error": {"timeout_s": args.timeout, "log": str(log)}}
            row["fresh_process_wall_s"] = time.perf_counter() - started
            rows.append(row)
            (args.out / f"{args.label}.json").write_text(json.dumps(rows, indent=2) + "\n")
            print(json.dumps({key: row.get(key) for key in ["mode", "workload", "rep",
                              "exl3_native_generation_tps", "generation_call_output_tps", "error"]}), flush=True)
            if "error" in row:
                raise RuntimeError(f"EXL3 worker failed; inspect {log}")
    summary = []
    for workload in helper.CASES:
        valid = [row for row in rows if row["workload"] == workload and "error" not in row]
        summary.append({"mode": args.mode, "workload": workload, "successful_reps": len(valid),
                        "median_exl3_native_generation_tps": statistics.median(
                            row["exl3_native_generation_tps"] for row in valid),
                        "median_generation_call_output_tps": statistics.median(
                            row["generation_call_output_tps"] for row in valid),
                        "quality_checks": [row["quality_check"] for row in valid]})
    (args.out / f"{args.label}.summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
