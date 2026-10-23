#!/bin/bash
# usage: run_method.sh METHOD GPU [REPS]
# Starts METHOD's server on one GPU, checks it with the aa-mini-v1 replay, runs the AA-AgentPerf-Local default
# replay REPS times, then stops the server. Everything lands in $Q38_WORK/runs/METHOD/<timestamp>/.
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$HERE/env.local.sh"; source "$HERE/methods.sh"
METHOD=$1 GPU=$2 REPS=${3:-1}
PORT=$((18400 + GPU))
OUT=$Q38_WORK/runs/$METHOD/$(date +%Y%m%d-%H%M%S); mkdir -p "$OUT"
AA=$Q38_WORK/envs/aa/bin/agentperf-local
export HF_HUB_OFFLINE=1 VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1 SGLANG_DISABLE_USAGE_STATS=1
export XDG_CACHE_HOME=$Q38_WORK/.cache TRITON_CACHE_DIR=$Q38_WORK/.cache/triton VLLM_CACHE_ROOT=$Q38_WORK/.cache/vllm
export FLASHINFER_WORKSPACE_BASE=$Q38_WORK/.cache TMPDIR=$Q38_WORK/.tmp PATH=/usr/local/cuda/bin:$PATH
log() { echo "$(date -Is) $*" | tee -a "$OUT/run.log"; }

method_setup "$METHOD" "$PORT" "$OUT" || exit 2
printf '%q ' env "${SERVE_ENV[@]}" "${CMD[@]}" > "$OUT/launch.sh"; echo >> "$OUT/launch.sh"
log "method=$METHOD gpu=$GPU reps=$REPS"

# GPU telemetry for all four cards (the box is shared; other cards' load is part of the record)
nvidia-smi --query-gpu=timestamp,index,utilization.gpu,memory.used,power.draw,temperature.gpu,clocks.sm \
  --format=csv,noheader,nounits -lms 1000 > "$OUT/gpus.csv" 2>/dev/null &
SMI=$!

CUDA_VISIBLE_DEVICES=$GPU setsid env "${SERVE_ENV[@]}" "${CMD[@]}" > "$OUT/server.log" 2>&1 < /dev/null &
SPID=$!
stop() {
  kill -- -$SPID 2>/dev/null; for i in $(seq 30); do kill -0 -- -$SPID 2>/dev/null || break; sleep 1; done
  kill -9 -- -$SPID 2>/dev/null; kill $SMI 2>/dev/null
}
trap stop EXIT

t0=$SECONDS
until curl -sf "http://127.0.0.1:$PORT/v1/models" > "$OUT/models.json" 2>/dev/null; do
  kill -0 $SPID 2>/dev/null || { log "FAIL server exited during startup"; tail -30 "$OUT/server.log"; exit 3; }
  [ $((SECONDS - t0)) -gt 2400 ] && { log "FAIL startup timeout"; exit 3; }
  sleep 5
done
log "ready after $((SECONDS - t0))s; gpu$GPU memory $(nvidia-smi -i $GPU --query-gpu=memory.used --format=csv,noheader)"

replay() { # NAME [args]
  local name=$1; shift
  "$AA" run --base-url "http://127.0.0.1:$PORT/v1" --model "$MODEL_ID" --device "$GPU" --output-dir "$OUT/$name" \
    "$@" > "$OUT/$name.log" 2>&1
  local rc=$?
  log "$name rc=$rc $(python3 "$HERE/brief.py" "$OUT/$name" 2>/dev/null)"
  return $rc
}
replay mini --replay aa-mini-v1 || { tail -30 "$OUT/mini.log"; exit 4; }
for r in $(seq 1 "$REPS"); do replay full-$r || exit 5; done
log DONE
