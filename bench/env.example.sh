# Copy to env.local.sh (untracked) and point these at this machine.
export Q38_WORK=/path/to/workdir        # envs/aa (agentperf-local 0.3.4), engines/, hf-cache/, runs/
export Q38_MODELS=/path/to/models       # vllm/Qwen3.8-27B-W4A16-AutoRound
export Q38_BUILD_ENV=/path/to/toolchain # the GCC toolchain llama.cpp was built with (its lib/ goes on LD_LIBRARY_PATH)
export Q38_VLLM_ENV=/path/to/env        # Python env with vLLM 0.27.1
