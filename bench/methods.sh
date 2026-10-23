# Server launch for each method. Every server gets a 65,536-token context, one sequence and its engine's own
# prefix cache, as AA-AgentPerf-Local requires. `method_setup METHOD PORT OUT` sets CMD (argv), SERVE_ENV
# (extra environment) and MODEL_ID (the name requests use); it may write a config file into OUT.

W=$Q38_WORK M=$Q38_MODELS
GGUF=$M/gguf DRAFT_GGUF=$M/gguf/Qwen3.8-27B-DFlash2-Q4_K_M.gguf

llama_common() { # BIN PORT
  echo "$1 --alias qwen3.8-27b --host 127.0.0.1 --port $2 --ctx-size 65536 --parallel 1 --gpu-layers all --jinja"
}
# The three AA recipes for Qwen3.8 27B, flag for flag (recipes/qwen3-8-27b in aa-agentperf-local 0.3.4).
AA_MTP2="--batch-size 4096 --ubatch-size 2048 --no-mmproj --spec-type draft-mtp --spec-draft-n-max 2 --backend-sampling --spec-draft-backend-sampling"
AA_DFLASH7="--batch-size 4096 --ubatch-size 512 --no-mmproj --model-draft $DRAFT_GGUF --spec-type draft-dflash --spec-draft-n-max 7 --spec-draft-backend-sampling"

vllm_common() { # PYTHON_ENV MODEL PORT
  echo "$1/bin/vllm serve $2 --served-model-name qwen3.8-27b --host 127.0.0.1 --port $3 --max-model-len 65536 \
    --max-num-seqs 1 --tensor-parallel-size 1 --language-model-only --enable-prefix-caching --enable-prompt-tokens-details \
    --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3 --seed 0"
}

method_setup() {
  local m=$1 port=$2 out=$3
  SERVE_ENV=() MODEL_ID=qwen3.8-27b
  local L=$W/engines/llama.cpp/build/bin/llama-server
  local IK=$W/engines/ik_llama.cpp/build/bin/llama-server
  case $m in
    # llama.cpp master
    lcpp-q4km-ar)       CMD=($(llama_common $L $port) --model $GGUF/Qwen3.8-27B-Q4_K_M.gguf --no-webui --verbosity 4) ;;
    lcpp-q4km-mtp2)     CMD=($(llama_common $L $port) --model $GGUF/Qwen3.8-27B-Q4_K_M.gguf $AA_MTP2 --no-webui --verbosity 4) ;;
    lcpp-udq4km-dflash7) CMD=($(llama_common $L $port) --model $GGUF/Qwen3.8-27B-UD-Q4_K_M.gguf $AA_DFLASH7 --no-webui --verbosity 4) ;;
    # ik_llama.cpp
    ik-q4km-ar)         CMD=($IK --alias qwen3.8-27b --host 127.0.0.1 --port $port --ctx-size 65536 --parallel 1 -ngl 99 --jinja \
                          --model $GGUF/Qwen3.8-27B-Q4_K_M.gguf) ;;
    ik-q4km-mtp2)       CMD=($IK --alias qwen3.8-27b --host 127.0.0.1 --port $port --ctx-size 65536 --parallel 1 -ngl 99 --jinja \
                          --model $GGUF/Qwen3.8-27B-Q4_K_M.gguf --spec-type mtp:n_max=2,p_min=0.0) ;;
    ik-udq4km-dflash7)  CMD=($IK --alias qwen3.8-27b --host 127.0.0.1 --port $port --ctx-size 65536 --parallel 1 -ngl 99 --jinja \
                          --model $GGUF/Qwen3.8-27B-UD-Q4_K_M.gguf --model-draft $DRAFT_GGUF -ngld 99 --spec-type dflash:n_max=7) ;;
    # vLLM 0.27.1 as released, AutoRound W4A16; KV and memory as AA's own vLLM recipes (fp8 KV, 0.9 of the card)
    vllm-w4a16-ar)      CMD=($(vllm_common $W/envs/vllm $M/vllm/Qwen3.8-27B-W4A16-AutoRound $port) \
                          --kv-cache-dtype fp8_e4m3 --gpu-memory-utilization 0.9) ;;
    vllm-w4a16-mtp3)    CMD=($(vllm_common $W/envs/vllm $M/vllm/Qwen3.8-27B-W4A16-AutoRound $port) \
                          --kv-cache-dtype fp8_e4m3 --gpu-memory-utilization 0.9 \
                          --speculative-config '{"method":"mtp","num_speculative_tokens":3}') ;;
    # vLLM 0.27.1 with the sidnaZ RTX 4090 patches and recipe (runtime/start-single-user.sh), one sequence
    vsz-*)
      local spec
      case $m in
        vsz-w4a16-ar) spec=() ;;
        vsz-w4a16-mtp3) spec=(--speculative-config '{"method":"mtp","num_speculative_tokens":3}') ;;
        vsz-w4a16-dflash7) spec=(--speculative-config "{\"method\":\"dflash\",\"model\":\"$M/vllm/Qwen3.8-27B-DFlash2-W4A16\",\"num_speculative_tokens\":7}") ;;
        *) return 1 ;;
      esac
      SERVE_ENV=(FLASHINFER_DISABLE_VERSION_CHECK=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True VLLM_USE_FLASHINFER_SAMPLER=0
        VLLM_SPEC_DECODE_ATTN=1 VLLM_SPEC_DECODE_ATTN_QMAX=8 VLLM_DFLASH2_LOOKUP=1 VLLM_V2_CUDAGRAPH_MEM_MIB=1400)
      CMD=($(vllm_common $Q38_SIDNAZ_ENV $M/vllm/Qwen3.8-27B-W4A16-AutoRound-fast $port) \
        --gpu-memory-utilization 0.93 --kv-cache-memory 5583457484 --api-server-count 1 --attention-backend FLASH_ATTN \
        --kv-cache-dtype bfloat16 --mamba-ssm-cache-dtype float16 --async-scheduling --max-num-batched-tokens 2048 \
        "${spec[@]}" --compilation-config '{"max_cudagraph_capture_size":8,"custom_ops":["+rms_norm","+silu_and_mul"]}' \
        --mamba-cache-mode align) ;;
    # SGLang, AWQ INT4
    sgl-awq-ar|sgl-awq-mtp3)
      local spec=()
      [ $m = sgl-awq-mtp3 ] && spec=(--speculative-algorithm NEXTN --speculative-num-steps 3 --speculative-eagle-topk 1 --speculative-num-draft-tokens 4)
      CMD=($W/envs/sglang/bin/python -m sglang.launch_server --model-path $M/awq/Qwen3.8-27B-AWQ-INT4 --served-model-name qwen3.8-27b \
        --host 127.0.0.1 --port $port --context-length 65536 --max-running-requests 1 --tp-size 1 --mem-fraction-static 0.88 \
        --kv-cache-dtype fp8_e4m3 --max-mamba-cache-size 1 --tool-call-parser qwen3_coder --reasoning-parser qwen3 \
        --enable-cache-report --language-only "${spec[@]}") ;;
    # ExLlamaV3 through TabbyAPI, EXL3 4.0 bpw (turboderp SC_4.00bpw_H5), FP16 cache
    exl3-*)
      local mode=disabled draft= ntok=
      case $m in
        exl3-4bpw-ar) ;;
        exl3-4bpw-mtp) mode=mtp ;;
        exl3-4bpw-dflash7) mode=model draft=z-lab-Qwen3.8-27B-DFlash2 ntok=7 ;;
        *) return 1 ;;
      esac
      cat > $out/tabby.yml <<EOF
network: {host: 127.0.0.1, port: $port, disable_auth: true}
logging: {log_prompt: false, log_generation_params: false, log_requests: false}
model:
  model_dir: $M/exl3
  model_name: Qwen3.8-27B-SC4.00bpw-H5
  backend: exllamav3
  max_seq_len: 65536
  cache_size: 65536
  cache_mode: FP16
  max_batch_size: 1
  tensor_parallel: false
  gpu_split_auto: true
draft_model:
  draft_mode: $mode
  draft_model_dir: $M/src
  draft_model_name: $draft
  draft_num_tokens: $ntok
sampling: {override_preset: }
EOF
      MODEL_ID=Qwen3.8-27B-SC4.00bpw-H5
      CMD=($W/envs/exl3/bin/python $W/engines/tabbyAPI/main.py --config $out/tabby.yml) ;;
    # NInfer (qwen38-4090-decode, f5cc590 plus ignore_eos): `serve.sh official` engine knobs, but a 65,536-token
    # context, prefix reuse on, and sampling and thinking left to the request
    ninfer-v3-dflash15)
      SERVE_ENV=(NINFER_TWO_LEVEL_HEAD=1 NINFER_HEAD_SCREEN=3 NINFER_SCREEN_TILED=1 NINFER_PROPOSAL_SCREEN=3
        NINFER_TREE_TEMPERATURE=1.25 NINFER_KV_VI8=1 NINFER_GDN_STATE_F16=1 NINFER_GDN_CHUNKED_RECORD=1
        NINFER_CONV_EPILOGUE=1 NINFER_ATTN_ROWSPLIT=3 NINFER_L2_FILL=121 NINFER_L2_FILL_NORM_KB=1536
        NINFER_L2_FILL_POST_KB=768 NINFER_L2_FILL_GATED_KB=768 NINFER_L2_FILL_RECORD_KB=2048 NINFER_L2_FILL_ATTN_KB=4096)
      CMD=($W/engines/ninfer-aa/build-nordc/apps/ninfer-serve $M/ninfer-v3-dflash2/qwen3_8_27b.ninfer --host 127.0.0.1
        --port $port --model-id qwen3.8-27b --spec dflash2 --draft-tokens 15 --lm-head-draft --verify-tree --kv-dtype k8v4
        --max-context 65536 --kv-capacity 65536 --max-concurrency 1 --prefill-chunk 1024) ;;
    *) echo "unknown method $m" >&2; return 1 ;;
  esac
}
