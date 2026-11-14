# Copy to env.local.sh (untracked) and point these at this machine.
export Q38_WORK=/path/to/workdir        # envs/aa (agentperf-local 0.3.4), engines/, hf-cache/, runs/
export Q38_MODELS=/path/to/models       # vllm/Qwen3.8-27B-W4A16-AutoRound
export Q38_BUILD_ENV=/path/to/toolchain # the GCC toolchain llama.cpp was built with (its lib/ goes on LD_LIBRARY_PATH)
export Q38_VLLM_ENV=/path/to/env        # Python env with vLLM 0.27.1
export Q38_NINFER_SERVE=/path/to/ninfer-serve      # built from qwen38-4090-decode's series plus code/reproduce/aa_serve_patch.py and anchor_patch.py
export Q38_NINFER_CONTAINERS=/path/to/containers   # official/ and ours/, as qwen38-4090-decode's REPRODUCE.md downloads them
export Q38_NINFER_LIBS=/path/to/ffmpeg/lib         # FFmpeg libraries ninfer-serve links against, if not on the default path
