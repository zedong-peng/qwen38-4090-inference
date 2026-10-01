#!/usr/bin/env python3
"""Start one owned localhost server at a time, measure, and release its GPU."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request


def require_no_listener(host, port):
    # A bind probe can reject closed servers' TIME_WAIT sockets.
    try:
        with socket.create_connection((host, port), timeout=2):
            pass
    except ConnectionRefusedError:
        return
    raise RuntimeError(f"refusing to reuse existing listener at {host}:{port}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--modes", default="0,3,5")
    parser.add_argument("--kv-dtype", default="int8")
    parser.add_argument("--out", required=True)
    parser.add_argument("--context", type=int, default=4096)
    parser.add_argument("--gpu", type=int, default=3)
    parser.add_argument("--port", type=int, default=18038)
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args()
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    events = []
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(args.gpu))
    base_url = "http://127.0.0.1:" + str(args.port)
    helper = Path(__file__).with_name("benchmark_http.py")
    for k in [int(x) for x in args.modes.split(",")]:
        label = args.label + "-k" + str(k)
        require_no_listener("127.0.0.1", args.port)
        command = [args.bin, args.model, "--host", "127.0.0.1", "--port", str(args.port),
                   "--model-id", "qwen3.8-27b",
                   "--max-context", str(args.context), "--kv-capacity", str(args.context),
                   "--max-concurrency", "1", "--prefill-chunk", "1024", "--kv-dtype", args.kv_dtype,
                   "--no-prefix-reuse", "--greedy", "--request-log-jsonl",
                   str(output / (label + ".requests.jsonl"))]
        if k:
            command += ["--spec", "mtp", "--draft-tokens", str(k), "--lm-head-draft"]
        event = {"label": label, "command": command, "visible_gpu": args.gpu}
        with (output / (label + ".server.log")).open("w") as log:
            proc = subprocess.Popen(command, stdout=log, stderr=log, env=env)
            try:
                start = time.monotonic()
                ready = False
                while proc.poll() is None and time.monotonic() - start < 180:
                    try:
                        with urllib.request.urlopen(base_url + "/health", timeout=2) as response:
                            ready = response.status == 200
                        own_log = (output / (label + ".server.log")).read_text(errors="replace")
                        ready = ready and proc.poll() is None and ("listening on " + base_url) in own_log
                        if ready:
                            break
                    except OSError:
                        time.sleep(0.5)
                event.update({"startup_s": time.monotonic() - start, "ready": ready})
                if ready:
                    bench = [sys.executable, str(helper), "--base-url", base_url, "--label", label,
                             "--out", str(output), "--gpu", str(args.gpu), "--reps", str(args.reps)]
                    event["benchmark_exit_code"] = subprocess.run(bench, env=env).returncode
                else:
                    event["startup_exit_code"] = proc.poll()
                    print(label + ": startup failed; inspect " + str(output / (label + ".server.log")), flush=True)
            except BaseException as error:
                event["error"] = repr(error)
                raise
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=10)
                event["server_exit_code"] = proc.poll()
                events.append(event)
                (output / (args.label + ".runs.json")).write_text(json.dumps(events, indent=2))


if __name__ == "__main__":
    main()
