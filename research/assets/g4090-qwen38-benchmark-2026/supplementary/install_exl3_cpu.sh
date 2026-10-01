#!/usr/bin/env bash
# Run only after the pinned source archive has been unpacked and Python 3.12 created.
# All operations are CPU-side; model loading/inference requires a later GPU handoff.
set -euo pipefail
TASK_EXL_ROOT="$HOME/qwen38-4090"
TASK_EXL_ENV="$TASK_EXL_ROOT/tools/exl3-env"
TASK_BUILD_ENV="$TASK_EXL_ROOT/tools/build-env"
TASK_EXL_REPO="$TASK_EXL_ROOT/repos/exllamav3"
export PATH="$TASK_EXL_ENV/bin:$TASK_BUILD_ENV/bin:/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="$TASK_EXL_ENV/lib:$TASK_BUILD_ENV/lib:/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"
export CUDA_VISIBLE_DEVICES=""
export CUDA_HOME=/usr/local/cuda
export MAX_JOBS=4
export TORCH_CUDA_ARCH_LIST=8.9
export CC="$TASK_BUILD_ENV/bin/x86_64-conda-linux-gnu-gcc"
export CXX="$TASK_BUILD_ENV/bin/x86_64-conda-linux-gnu-g++"
export CUDAHOSTCXX="$CXX"
export PIP_CACHE_DIR="$TASK_EXL_ROOT/tools/exl3-pip-cache"
python -c 'import sys; assert sys.version_info[:2] == (3, 12); print(sys.version)'
python -m pip install --index-url https://pypi.org/simple 'setuptools>=77' wheel ninja
python -m pip install 'torch==2.10.0' --index-url https://download.pytorch.org/whl/cu128
printf 'torch==2.10.0\n' > "$TASK_EXL_ROOT/tools/exl3-constraints.txt"
python -m pip install --no-build-isolation --constraint "$TASK_EXL_ROOT/tools/exl3-constraints.txt" \
    --index-url https://pypi.org/simple "$TASK_EXL_REPO[examples]"
python -m pip check
python - <<'PY'
import json, pathlib, sys, importlib.metadata
import torch, exllamav3
import exllamav3_ext
from exllamav3.architecture import dflash2, qwen3_5_mtp
root = pathlib.Path.home() / 'qwen38-4090'
result = {
    'python': sys.version,
    'torch': torch.__version__,
    'torch_cuda': torch.version.cuda,
    'exllamav3': importlib.metadata.version('exllamav3'),
    'source': json.loads((root / 'repos/exllamav3/SOURCE_PROVENANCE.json').read_text()),
    'extension': exllamav3_ext.__file__,
    'dflash2_module': dflash2.__file__,
    'qwen3_5_mtp_module': qwen3_5_mtp.__file__,
    'gpu_loaded': False,
}
assert torch.__version__.startswith('2.10.0') and torch.version.cuda == '12.8'
(root / 'results/exl3-cpu-install.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
PY
python -m pip freeze > "$TASK_EXL_ROOT/results/exl3-pip-freeze.txt"
