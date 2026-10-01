#!/usr/bin/env bash
set -euo pipefail
root="$HOME/qwen38-4090"
mode="${1:?pass ar, mtp, or dflash2 after GPU handoff}"
case "$mode" in
  ar) draft_tokens=0 ;;
  mtp) draft_tokens="${2:-4}" ;;
  dflash2) draft_tokens="${2:-7}" ;;
  *) exit 2 ;;
esac
export PATH="$root/tools/exl3-env/bin:$root/tools/build-env/bin:/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="$root/tools/exl3-env/lib:$root/tools/build-env/lib:/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"
export CUDA_VISIBLE_DEVICES=3 MAX_JOBS=4 TORCH_CUDA_ARCH_LIST=8.9
export PYTHONPATH="$root/repos/exllamav3-git:${PYTHONPATH:-}"
label="exl3-$mode-k$draft_tokens-cq4-cs4096"
command=( "$root/tools/exl3-env/bin/python" "$root/repos/exllamav3-git/benchmark_qwen38.py"
  --mode "$mode" --label "$label" --draft-tokens "$draft_tokens"
  --repo "$root/repos/exllamav3-git" --cases-helper "$root/benchmark_http.py"
  --gpu 3 --context 4096 --max-tokens 512 --reps 3
  --out "$root/results/$label" )
exec "${command[@]}"
