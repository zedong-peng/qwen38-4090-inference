---
license: apache-2.0
base_model: neroued/Qwen3.8-27B-NInfer
base_model_relation: quantized
pipeline_tag: image-text-to-text
tags:
  - ninfer
  - qwen3.8
  - rtx-4090
  - cuda
  - int8
  - speculative-decoding
  - mtp
  - dflash2
---

# Qwen3.8-27B, NInfer int8-prefill artifact for the RTX 4090

The official [NInfer Qwen3.8-27B artifact](https://huggingface.co/neroued/Qwen3.8-27B-NInfer)
with one change: its prefill GEMMs may quantize their activations to int8 and run on int8 tensor
cores. **The weights are byte-for-byte the official ones** (Q4/Q5 projections, Q8 vocabulary,
MTP head, DFlash2 drafter, vision tower, indexed proposal head, tokenizer and chat template); only
the activation permission of 512 projection inputs changes from `A16Only` to `AllowA8`.

**This file only runs on the NInfer build from
[JGamboa/ninfer-4090-windows](https://github.com/JGamboa/ninfer-4090-windows/tree/main)
(branch `main`), on an NVIDIA RTX 4090 (`sm_89`).** It does not load in
llama.cpp, vLLM or Transformers, nor in engines without the int8 prefill route.

## Files

| File | Size | SHA-256 |
|---|---:|---|
| `qwen3_8_27b_a8.ninfer` | 19.0 GiB (20,437,521,664 bytes) | `49bf76388e139defbe416c8cc0079abc1c78b59be2a41ff56ae960aeacf5fc19` |
| `qwen3_8_27b_a8.ninfer.conversion.json` | 0.5 MB | conversion report: sources, formats, permissions |

## What changes

- **Prefill** (129 or more tokens per step): activations are quantized per token and per 64
  channels (`scale = amax / 127`), the same groups as the weight scales, and the Q4/Q5 codes feed
  `m16n8k32` int8 tensor-core MMAs exactly. Each group's int32 sum is scaled by
  `weight_scale x activation_scale` in FP32.
- **Decode** (MTP, DFlash2 and n-gram verification included) keeps the BF16 route: the same text
  and speed as the official artifact.

## Measurements

Current figures for this artifact (2026-09-27, `main` at `e7d309e3`, one RTX 4090 at stock clocks
without a display, Windows 11, CUDA 13.4):

| Measurement | Result |
|---|---:|
| Prefill `pp512` / `pp2048` (`ninfer_bench`, int8 KV) | 5,310 / **5,730-5,790 tok/s** |
| Prefill, 64K-token prompt (needle test, rk4v4-e8 KV, answer exact) | **14.8-14.9 s** |
| Decode, no speculation (`tg128`) | 54.6 tok/s |
| Decode, MTP 3, six mixed prompts, greedy, thinking off | **120 tok/s** |

Against the official llama.cpp (`a894dae`) on the same machine, with a Q4_K_M GGUF made from the
same Qwen3.8-27B BF16 checkpoint, this artifact prefills 1.75-2.0x faster and decodes 1.1x faster
without speculation and 1.2-1.3x faster with MTP 3
([comparison](https://github.com/JGamboa/ninfer-4090-windows/blob/main/docs/llamacpp-comparison.md)).

Release comparison with the official artifact (2026-09-26, an earlier build, the card also driving
a 4K desktop at 60 Hz). Both artifacts on the same binary, runs alternated. All figures measured.

| | Official artifact | This artifact |
|---|---:|---:|
| Prefill `pp512` / `pp2048` (`ninfer_bench`, int8 KV) | 2,536 / 2,762 tok/s | **4,436 / 5,008 tok/s** |
| Prefill, 8K-token prompt (needle test, rk4v4-e8 KV) | 2.9 s | **1.6 s** |
| Prefill, 64K-token prompt | 27.4-27.6 s | **17.2 s** |
| Prefill, 128K-token prompt | 64.0 s | **43.0 s** |
| Needle-in-a-haystack answers at 8K / 64K / 128K | exact | exact |
| Quick perplexity, four corpora (bf16 KV) | 4.800742 | 4.794439 |
| Task quality, 45 deterministic tasks (`tools/eval`, thinking off) | 45/45 | 45/45 |
| Decode, no speculation (`tg128`) | 52.0 tok/s | 52.0 tok/s |
| MTP 3 round time | 23.7 ms | 23.7 ms |

Greedy output is identical to the official artifact whenever no prefill step reaches 129 tokens.
On longer prompts some answers diverge at a later token with equivalent wording (4 of 6 test
prompts, at words 3-152), as expected from a different rounding of the prompt activations.

## Usage

```bat
hf download jgamboa/Qwen3.8-27B-NInfer-4090 qwen3_8_27b_a8.ninfer --local-dir E:\LLM

ninfer-serve.exe E:\LLM\qwen3_8_27b_a8.ninfer --host 127.0.0.1 --port 8080 ^
  --max-context 100000 --kv-capacity 100000 --kv-dtype rk4v4-e8 --max-concurrency 3 ^
  --prefill-chunk 1408 --spec mtp --draft-tokens 3 --lm-head-draft --ngram chain --preserve-thinking
```

Build instructions, every option and the benchmark commands are in the
[repository README](https://github.com/JGamboa/ninfer-4090-windows/tree/main).

## How it was made

With the `qwen3_8_27b_a8` recipe, which copies the official artifact word for word and only sets
the permissions (about four minutes on the CPU, no BF16 checkpoint needed):

```bat
python -m tools.convert --model <qwen3.8 config dir> --recipe qwen3_8_27b_a8 ^
  --source reference=qwen3_8_27b.ninfer --source dflash2=<Qwen3.8-27B-DFlash2 dir> ^
  --components text,vision,mtp,dflash2 --name qwen3.8-27b --out qwen3_8_27b_a8.ninfer
```

The source is the official `qwen3_8_27b.ninfer` from
[neroued/Qwen3.8-27B-NInfer](https://huggingface.co/neroued/Qwen3.8-27B-NInfer) (SHA-256
`81f924d4...0375da`). All 1,184 bound objects, the component configurations and the six resources
were checked byte-identical to it.

## Credits and license

Qwen3.8-27B by the Qwen team; the NInfer engine and the official artifact by
[Neroued](https://github.com/Neroued/ninfer); DFlash2 drafter by
[z-lab](https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2). The int8 prefill route was developed
for the RTX 4090 in [JGamboa/ninfer-4090-windows](https://github.com/JGamboa/ninfer-4090-windows)
with [Claude Code](https://claude.com/claude-code). Apache License 2.0, as the base artifact.
