#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$HOME/qwen38-4090"
TASK_TABBY_REPO="$TASK_ROOT/repos/tabbyAPI"
TASK_EXL_ENV="$TASK_ROOT/tools/exl3-env"
TASK_BUILD_ENV="$TASK_ROOT/tools/build-env"
cd "$TASK_TABBY_REPO"
export PYTHONPATH="$TASK_TABBY_REPO"
if (( $# > 0 )) && [[ "$1" == "--check" ]]; then
  export CUDA_VISIBLE_DEVICES=""
  exec "$TASK_EXL_ENV/bin/python" "$TASK_TABBY_REPO/runtime-g4090/validate_config_cpu.py"
fi
if [[ "$#" != 0 ]]; then
  echo "Usage: $0 [--check]" >&2
  exit 2
fi
export CUDA_VISIBLE_DEVICES=3
TASK_LIBRARY_PREV=""
if [[ -v LD_LIBRARY_PATH ]]; then TASK_LIBRARY_PREV="$LD_LIBRARY_PATH"; fi
export LD_LIBRARY_PATH="$TASK_EXL_ENV/lib:$TASK_BUILD_ENV/lib:/usr/local/cuda/lib64:$TASK_LIBRARY_PREV"
# Prevent Tabby's built-in port fallback from silently changing the endpoint.
"$TASK_EXL_ENV/bin/python" - <<'PORT'
import socket
with socket.socket() as probe:
    probe.bind(('127.0.0.1',18041))
PORT
exec "$TASK_EXL_ENV/bin/python" "$TASK_TABBY_REPO/main.py" \
  --config "$TASK_TABBY_REPO/runtime-g4090/dflash2-benchmark.yml"
