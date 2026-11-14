#!/bin/bash
# Qwen3.8 27B on one RTX 4090, AA-AgentPerf-Local 0.3.4 default replay, five setups:
#   lcpp-mtp2    AA managed run, recipe qwen38-27b-q4-k-m-mtp (AA's RTX 5090 run), llama.cpp b11026
#   lcpp-dflash7 AA managed run, recipe qwen38-27b-ud-q4-k-m-dflash-rtx-spark (AA's RTX Spark run), llama.cpp b11236
#   vllm-mtp3    vLLM 0.27.1, dbirks/Qwen3.8-27B-W4A16-AutoRound, launched as AA's tool launches vLLM, attached run;
#                --language-model-only skips the vision encoder, as the llama.cpp recipes' --no-mmproj does
#   ninfer-tree15  NInfer as built by the decode study (github.com/zedong-peng/qwen38-4090-decode: the patch series,
#                then code/reproduce/aa_serve_patch.py), the official NInfer v3 container, DFlash2 drafts of 15 tokens
#                with verify trees, every research knob off (the study's engine knobs that keep the dense verify head
#                finish within 0.2% of it here: prefill, not decode, is most of this workload); attached run
#   ninfer-requant the same server on the study's re-quantized container with its weight knobs: one start attempt.
#                Its decode-only weight copies leave no room for a 65,536-token KV cache; it is listed, not ranked
# usage: run_4090.sh GPU [REPS] [SETUPS]. SETUPS is a space-separated subset (default all five). Each setup: an aa-mini-v1
# check, then REPS full replays; a failed setup is logged and skipped.
set -u
G=$1 REPS=${2:-3} SETUPS=${3:-lcpp-mtp2 lcpp-dflash7 vllm-mtp3 ninfer-tree15 ninfer-requant}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); source "$HERE/env.local.sh"
W=$Q38_WORK M=$Q38_MODELS
E=$Q38_BUILD_ENV
export LD_LIBRARY_PATH=$E/lib:${Q38_NINFER_LIBS:+$Q38_NINFER_LIBS:}/usr/local/cuda/lib64 HF_HUB_CACHE=$W/hf-cache HF_HUB_OFFLINE=1 DO_NOT_TRACK=1
export XDG_CACHE_HOME=$W/.cache TMPDIR=$W/.tmp VLLM_NO_USAGE_STATS=1 TRITON_CACHE_DIR=$W/.cache/triton VLLM_CACHE_ROOT=$W/.cache/vllm
export FLASHINFER_WORKSPACE_BASE=$W/.cache
mkdir -p $TMPDIR
AA=$W/envs/aa/bin/agentperf-local
R=$W/runs/$(date +%Y%m%d-%H%M%S); mkdir -p $R
log() { echo "$(date -Is) $*" | tee -a $R/run.log; }
nvidia-smi --query-gpu=timestamp,index,utilization.gpu,memory.used,power.draw,temperature.gpu,clocks.sm \
  --format=csv,noheader,nounits -lms 2000 > $R/gpus.csv 2>/dev/null &
SMI=$!
trap 'kill $SMI 2>/dev/null' EXIT
log "gpu=$G reps=$REPS setups=$SETUPS"

managed() { # NAME BUILD PROFILE
  local name=$1 bin=$W/engines/$2/build/bin profile=$3
  log "$name $(PATH=$bin:$PATH llama-server --version 2>&1 | grep -i version | head -1) profile=$profile"
  for rep in mini $(seq 1 $REPS); do
    local extra=()
    [ $rep = mini ] && extra=(--replay aa-mini-v1)
    PATH=$bin:/usr/local/cuda/bin:$PATH $AA managed-run --profile-id $profile --framework llama-cpp --device $G \
      --no-progress --output-dir $R/$name/$rep "${extra[@]}" > $R/$name-$rep.log 2>&1
    local rc=$?
    log "$name $rep rc=$rc"
    [ $rc = 0 ] || return 1
  done
}

vllm_attached() { # NAME GPU_MEM_UTIL MAX_BATCHED [EXTRA_FLAG...]
  local name=$1 port=$((18500 + G)) py=$Q38_VLLM_ENV/bin
  mkdir -p $R/$name
  CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$G setsid $py/vllm serve $M/vllm/Qwen3.8-27B-W4A16-AutoRound \
    --served-model-name qwen3.8-27b --host 127.0.0.1 --port $port --max-model-len 65536 --tensor-parallel-size 1 \
    --max-num-seqs 1 --language-model-only --enable-prompt-tokens-details --enable-auto-tool-choice --tool-call-parser qwen3_coder \
    --reasoning-parser qwen3 --seed 0 --kv-cache-dtype fp8_e4m3 --gpu-memory-utilization $2 \
    --max-num-batched-tokens $3 --enable-chunked-prefill --async-scheduling --enable-prefix-caching \
    --speculative-config '{"method":"mtp","num_speculative_tokens":3}' "${@:4}" > $R/$name/server.log 2>&1 < /dev/null &
  local spid=$! t0=$SECONDS
  until curl -sf http://127.0.0.1:$port/v1/models > /dev/null 2>&1; do
    if ! kill -0 $spid 2>/dev/null || [ $((SECONDS - t0)) -gt 1800 ]; then
      log "$name server failed (util $2, batched $3)"
      tail -5 $R/$name/server.log >> $R/run.log
      kill -- -$spid 2>/dev/null
      sleep 10
      return 1
    fi
    sleep 5
  done
  log "$name ready after $((SECONDS - t0))s, util $2, batched $3, $(nvidia-smi -i $G --query-gpu=memory.used --format=csv,noheader)"
  local ok=0
  for rep in mini $(seq 1 $REPS); do
    local extra=()
    [ $rep = mini ] && extra=(--replay aa-mini-v1)
    $AA run --base-url http://127.0.0.1:$port/v1 --model qwen3.8-27b --device $G --no-progress \
      --output-dir $R/$name/$rep "${extra[@]}" > $R/$name-$rep.log 2>&1
    local rc=$?
    log "$name $rep rc=$rc"
    [ $rc = 0 ] || { ok=1; break; }
  done
  kill -- -$spid 2>/dev/null
  for i in $(seq 30); do kill -0 $spid 2>/dev/null || break; sleep 1; done
  kill -9 -- -$spid 2>/dev/null
  sleep 10
  return $ok
}

# the decode study's engine and weight knobs, as its serve.sh ours sets them
NINFER_REQUANT=(NINFER_PROPOSAL_SCREEN=3 NINFER_TREE_TEMPERATURE=1.25 NINFER_KV_VI8=1 NINFER_GDN_STATE_F16=1
  NINFER_GDN_CHUNKED_RECORD=1 NINFER_CONV_EPILOGUE=1 NINFER_ATTN_ROWSPLIT=3 NINFER_L2_FILL=121
  NINFER_L2_FILL_NORM_KB=1536 NINFER_L2_FILL_POST_KB=768 NINFER_L2_FILL_GATED_KB=768 NINFER_L2_FILL_RECORD_KB=2048
  NINFER_L2_FILL_ATTN_KB=4096 NINFER_TWO_LEVEL_HEAD=1 NINFER_HEAD_SCREEN=3 NINFER_SCREEN_TILED=1 NINFER_LS8=1 NINFER_DRAFT_CONV_Q4=1
  NINFER_Q3_SHADOW=1 NINFER_Q3_TILED=1)

ninfer_attached() { # NAME CONTAINER REPS [KNOB...]; REPS=0 is a start attempt only
  local name=$1 model=$2 reps=$3 port=$((18600 + G)); shift 3
  mkdir -p $R/$name
  CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$G setsid env ${@+"$@"} $Q38_NINFER_SERVE $model --host 127.0.0.1 \
    --port $port --model-id qwen3.8-27b --spec dflash2 --draft-tokens 15 --lm-head-draft --verify-tree --kv-dtype k8v4 \
    --max-context 65536 --kv-capacity 65536 --max-concurrency 1 --prefill-chunk 1024 \
    --request-log-jsonl $R/$name/requests.jsonl > $R/$name/server.log 2>&1 < /dev/null &
  local spid=$! t0=$SECONDS
  until curl -sf http://127.0.0.1:$port/v1/models > /dev/null 2>&1; do
    if ! kill -0 $spid 2>/dev/null || [ $((SECONDS - t0)) -gt 900 ]; then
      log "$name server failed"
      tail -5 $R/$name/server.log >> $R/run.log
      kill -- -$spid 2>/dev/null
      sleep 10
      return 1
    fi
    sleep 3
  done
  log "$name ready after $((SECONDS - t0))s, $(nvidia-smi -i $G --query-gpu=memory.used --format=csv,noheader)"
  local ok=0
  for rep in $([ $reps -gt 0 ] && echo mini) $(seq 1 $reps); do
    local extra=()
    [ $rep = mini ] && extra=(--replay aa-mini-v1)
    $AA run --base-url http://127.0.0.1:$port/v1 --model qwen3.8-27b --device $G --no-progress \
      --output-dir $R/$name/$rep "${extra[@]}" > $R/$name-$rep.log 2>&1
    local rc=$?
    log "$name $rep rc=$rc"
    [ $rc = 0 ] || { ok=1; break; }
  done
  kill -- -$spid 2>/dev/null
  for i in $(seq 30); do kill -0 $spid 2>/dev/null || break; sleep 1; done
  kill -9 -- -$spid 2>/dev/null
  sleep 10
  return $ok
}

for s in $SETUPS; do
  case $s in
    lcpp-mtp2) managed lcpp-mtp2 llama.cpp-b49650adb qwen38-27b-q4-k-m-mtp || log "lcpp-mtp2 FAILED" ;;
    lcpp-dflash7) managed lcpp-dflash7 llama.cpp-f1ea20621 qwen38-27b-ud-q4-k-m-dflash-rtx-spark || log "lcpp-dflash7 FAILED" ;;
    # 0.90/16384 and 0.95/4096 leave no room for a 65,536-token KV cache (2.91 GiB) next to the weights; one request
    # needs CUDA graphs only up to MTP's 4 tokens, which frees the rest
    vllm-mtp3) vllm_attached vllm-mtp3 0.97 2048 --compilation-config '{"max_cudagraph_capture_size":8}' ||
      log "vllm-mtp3 FAILED: does not fit a 65,536-token context in 24 GB" ;;
    ninfer-tree15) ninfer_attached ninfer-tree15 $Q38_NINFER_CONTAINERS/official/qwen3_8_27b.ninfer $REPS ||
      log "ninfer-tree15 FAILED" ;;
    ninfer-requant) ninfer_attached ninfer-requant $Q38_NINFER_CONTAINERS/ours/qwen3_8_27b.ninfer 0 "${NINFER_REQUANT[@]}" || log "ninfer-requant FAILED: does not start at a 65,536-token context" ;;
  esac
done
log DONE
