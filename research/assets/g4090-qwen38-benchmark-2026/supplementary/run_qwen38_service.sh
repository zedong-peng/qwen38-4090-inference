#!/usr/bin/env bash
set -euo pipefail
TASK_SERVICE_ROOT="${HOME}/qwen38-4090"
export CUDA_VISIBLE_DEVICES=3
export LD_LIBRARY_PATH="${TASK_SERVICE_ROOT}/tools/build-env/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
python3 - <<'PY'
import socket
try:
 with socket.create_connection(("127.0.0.1",18038),timeout=2):
  raise RuntimeError("Service port already has a listener; refusing to replace it")
except ConnectionRefusedError:
 pass
PY
exec "${TASK_SERVICE_ROOT}/repos/qwen38-cinference-4090/build-sm89/apps/ninfer-serve" \
 "${TASK_SERVICE_ROOT}/models/qwen3_8_27b.v3.ninfer" \
 --host 127.0.0.1 --port 18038 --model-id qwen3.8-27b \
 --max-context "${QWEN38_CONTEXT:-16384}" --kv-capacity "${QWEN38_CONTEXT:-16384}" \
 --max-concurrency 1 --prefill-chunk 1024 --kv-dtype int8 \
 --spec mtp --draft-tokens "${QWEN38_DRAFT_TOKENS:-7}" --lm-head-draft \
 --default-max-tokens 8192 --temperature 0 --presence-penalty 0 --frequency-penalty 0 \
 --no-thinking --preserve-thinking \
 --request-log-jsonl "${TASK_SERVICE_ROOT}/logs/cinference-service.requests.jsonl"
