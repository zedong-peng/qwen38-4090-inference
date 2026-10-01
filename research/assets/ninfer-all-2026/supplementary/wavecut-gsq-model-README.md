---
license: apache-2.0
base_model:
- ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF
- z-lab/Qwen3.8-27B-DFlash2
base_model_relation: merge
tags:
- ninfer
- gguf
- gsq
- rco
- mixed-precision
- qwen3.8
- rtx-3090
- rtx-4090
- rtx-5090
- image-text-to-text
---

# Qwen3.8-27B GSQ-RCO IQ3_S, NInfer v3 artifact

A [NInfer](https://github.com/Neroued/ninfer) **v3** artifact of ISTA-DASLab's
[Qwen3.8-27B GSQ-RCO IQ3_S](https://huggingface.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF) (3.5 bits
per weight) for **NInfer-all**, the `master` branch of
[iamwavecut/ninfer-all](https://github.com/iamwavecut/ninfer-all), which serves the RTX 3090,
RTX 4090 and RTX 5090. The GGUF assigns a ggml quantization type to every tensor; this artifact
keeps each tensor's ggml blocks byte for byte, so nothing is requantized, and the engine multiplies
the blocks in place. Stock NInfer builds refuse this file: the `gguf_*` formats exist only in that
line, from commit [`8706bfc0`](https://github.com/iamwavecut/ninfer-all/commit/8706bfc078bc35bd571494f9904217e9fbe11c41)
on.

## What is inside

| component | representation |
|---|---|
| text projections (64 layers) | the GGUF's own blocks, one type per tensor: IQ3_S, IQ3_XXS, IQ4_XS, Q4_K, IQ2_S, Q2_K, IQ2_XS, IQ2_XXS and one IQ1_M, 3.5 bits per weight on average |
| output head, token table | Q4_K, IQ2_S, as in the GGUF |
| MTP head | the GGUF's Q6_K next-token head |
| GDN A/B controls, norms, convolution, `A_log`, `dt_bias` | BF16/FP32, restored from llama.cpp's exporter conventions (grouped value heads, `w` instead of `1 + w`, `A_log` from `-exp(A_log)`); the GDN output projection keeps its stored column order and reads its input through a recorded permutation |
| DFlash2 adapter | [z-lab/Qwen3.8-27B-DFlash2](https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2), Q8 |
| proposal head | the output head's own Q4_K rows for the 131,072 most frequent tokens of NInfer's token ranking |
| Vision tower | the release's BF16 projector, groupwise Q4/Q5/Q6/Q8 as in the official artifact |
| chat template | NInfer's pinned `qwen3_8.jinja` |

One `.ninfer` file of 15,017,456,896 bytes (13.99 GiB; 10.95 GiB of text weights are resident
without Vision and drafters), next to its conversion report, `SHA256SUMS` and `NOTICE`.

Conversion command, from the repository's tree:

```bash
python3 -m tools.convert \
  --model Qwen3.8-27B \
  --recipe qwen3_8_27b_gguf \
  --source gguf=Qwen3.8-27B-GSQ-RCO-IQ3_S-mtp.gguf \
  --source vision=mmproj-Qwen3.8-27B-BF16.gguf \
  --source dflash2=Qwen3.8-27B-DFlash2 \
  --components text,vision,mtp,dflash2 \
  --resource chat_template.jinja=tools/chat_templates/qwen3_8.jinja \
  --proposal \
  --name qwen3.8-27b \
  --out Qwen3.8-27B-GSQ-RCO-IQ3_S-ninfer-v3.ninfer
```

`--model` needs only the base model's configuration and tokenizer files.

## Running

Build `master` ([its README](https://github.com/iamwavecut/ninfer-all#readme);
`CMAKE_CUDA_ARCHITECTURES` is `86`, `89` or `120a`). A single stream with MTP:

```bash
ninfer-serve Qwen3.8-27B-GSQ-RCO-IQ3_S-ninfer-v3.ninfer --model-id qwen3.8-27b \
  --max-context 176128 --kv-capacity 176128 --kv-dtype rk8v4 --gdn-state-fp16 \
  --spec mtp --draft-tokens 3
```

`--spec dflash2 --draft-tokens 5` drafts with the DFlash2 adapter instead; `--vision` adds images.
Products of up to eight tokens (decode, verification) decode each weight once for every token and
dot it with ggml's q8_1 activations; prompts run llama.cpp's integer tensor-core kernel, vendored
into the engine. [GGUF block formats](https://github.com/iamwavecut/ninfer-all/blob/master/docs/gguf.md)
describes both.

## Quality

WikiText-2 test perplexity with the protocol of the GSQ-RCO model card (the test rows joined by
blank lines, disjoint 2,048-token windows; `ninfer-perplexity --context 2048 --disjoint`, BF16 KV):

| model | perplexity |
|---|---:|
| **this artifact** | **7.071** |
| GSQ-RCO IQ3_S, as its model card states | 7.07 |
| BF16 Qwen3.8-27B, as the GSQ-RCO card states | 7.05 |
| official Qwen3.8-27B NInfer artifact (Q4/Q5 groups) | 7.286 |

Reasoning, with NInfer's [capability evaluation](https://github.com/iamwavecut/ninfer-all/blob/master/eval/README.md)
(EvalScope 1.10.0, temperature 1.0, one sampled run each, RTX 5090), the protocol the official
artifact was scored with:

| benchmark | this artifact | official Qwen3.8-27B NInfer artifact |
|---|---:|---:|
| IFBench (prompt-level strict) | **80.33%** | 77.67% |
| AIME 2025 | **100.00%** | 96.67% |
| AIME 2026 | **100.00%** | 96.67% |
| GPQA-Diamond | **88.38%** | 87.37% |

The GSQ-RCO card reports 100 on AIME 2025 and 89.39 on GPQA-Diamond for this quantization with its
own protocol (BF16: 100 and 89.90). One run of GPQA-Diamond's 198 questions varies by about two
points.

## Speed

September 2026, `rk8v4` KV, one request at a time, greedy, thinking off, measured with the
repository's reference client (`tools/bench/refbench.py`). Every row pairs this artifact with the
official Qwen3.8-27B NInfer artifact on the same card in the same sitting: an RTX 3090 at 420 W and
an RTX 4090 at 450 W with a 176,128-token window (the official DFlash2 row on the RTX 4090 at
167,936), an RTX 5090 at 450 W with 262,144. Short chat is the mean decode rate over five
512-token answers.

| | RTX 3090 | RTX 4090 | RTX 5090 |
|---|---:|---:|---:|
| short chat, no speculation | **59.9** / 40.3 tok/s | **70.6** / 55.0 tok/s | **107.5** / 88.1 tok/s |
| short chat, MTP, 3 drafts | **108.7** / 82.7 tok/s | **146.4** / 109.3 tok/s | **221.4** / 178.1 tok/s |
| short chat, DFlash2, 5 drafts | **115.6** / 109.2 tok/s | **169.4** / 141.3 tok/s | **226.5** / 222.5 tok/s |
| decode after 32K tokens, no speculation | **50.4** / 38.4 tok/s | **66.0** / 52.2 tok/s | **100.3** / 83.2 tok/s |
| time to first token, 8K prompt | **4.95** / 5.43 s | **2.21** / 3.17 s | **2.01** / 2.23 s |
| time to first token, 32K prompt | **20.5** / 22.2 s | **9.3** / 12.8 s | **8.6** / 9.3 s |
| device memory, idle, no speculation | 17.3 / 21.3 GiB | 17.5 / 21.4 GiB | 19.3 / 23.6 GiB |

(this artifact / the official one). The official artifact's published reference numbers, measured
on other boards (RTX 3090 at 390 W, RTX 5090 at 575 W), are 48.2 / 97.2 / 117.1 tok/s on the RTX
3090, 54.8 / 109.0 / 138.1 on the RTX 4090 and 92.0 / 184.7 / 221.0 on the RTX 5090 for the three
short-chat rows.

## Credits and license

Quantized weights: ISTA-DASLab, Qwen3.8-27B GSQ-RCO GGUFs, produced with
[GSQ](https://arxiv.org/abs/2604.18556) and [RCO](https://arxiv.org/abs/2605.00649) from
Qwen/Qwen3.8-27B. DFlash2 adapter: z-lab. Tokenizer and frontend resources: Qwen/Qwen3.8-27B. All
are Apache-2.0; their attribution notices are collected in `NOTICE` (original local cache). This repository only
re-packs those weights into NInfer's container.
