# g4090 EXL3 deployment record

2026-10-01: CPU preparation and the AR/MTP4/DFlash2-K7 GPU matrix completed. [Measured results and raw records](exl3-bench/README.md).

The runtime is a separate user environment at `~/qwen38-4090/tools/exl3-env`: Python 3.12.14, Torch 2.10.0+cu128, CUDA runtime 12.8, EXL3 1.5.3. Its native extension was compiled for SM89 with system CUDA 12.8.93 and at most four build workers. `pip check` and imports of the compiled extension, native DFlash2 architecture and Qwen3.5 MTP architecture passed with `CUDA_VISIBLE_DEVICES=""`.

The reference repositories in the local wiki remain unchanged and have clean Git workspaces. Actual runtime source is an independent remote Git clone: `~/qwen38-4090/repos/exllamav3-git`, official origin `https://github.com/turboderp-org/exllamav3.git`, detached commit `d3739fd393337b1ff4d6c2a342b12f0c87a9592f`. HyperQwen was cloned separately at `~/qwen38-4090/repos/HyperQwen-git`, official origin `https://github.com/syv-ai/HyperQwen.git`, commit `e1459c7631774f56de2f9425437d54e7e72ea688`; it has no installed runtime environment.

Both original source archives were shallow clones. A bundle could be produced but could not be cloned independently because it lacked parent objects, so it was rejected. Instead, read-only Git file transport made shallow bare mirrors outside the wiki; their copies on g4090 were used by `git clone --no-local --depth 1 file://…`. These remote clones passed `git fsck --full`, contain the fixed official commits, and have no `objects/info/alternates`. They do not depend on the local wiki or on the mirror remaining available. The already compiled, non-editable EXL3 installation was retained; importing code from the new clone uses its installed native extension and requires no rebuild. See [clone evidence](git-clone-provenance-exl3-hyperqwen.json) and [import/template check](exl3-git-import-and-template.json).

Pinned model downloads in `~/qwen38-4090/models`:

| Model | Official revision | Verified bytes |
| --- | --- | ---: |
| `r0b0tlab/Qwen3.8-27B-EXL3-4.00bpw` | `3f1771b8c21f83cbb8e82169559ced9f38ca04e5` | 16,533,419,632 |
| `r0b0tlab/Qwen3.8-27B-DFlash2-EXL3-4.00bpw` | `265b5240592907d2d55ff0dc4d5f66569692604d` | 1,254,705,438 |

Every file was verified against the official revision manifest: SHA256 for LFS objects, Git blob SHA1 for other files, plus recorded SHA256 for all downloaded files. The mirror transport was `https://hf-mirror.com`, because official HF DNS did not resolve on this host. The target index includes 39 `mtp.*` weights; its architecture is `Qwen3_5ForConditionalGeneration`, and the draft architecture is `DFlash2DraftModel`. This is a static compatibility check; model loading on a GPU remains a separate validation. [Full download checks](exl3-model-downloads.json), [installation evidence](exl3-cpu-install.json), [package versions](exl3-pip-freeze.txt).

Actual benchmark code is the untracked `benchmark_qwen38.py` and `run_qwen38_bench.sh` inside the remote EXL3 clone. The local [runner snapshot](benchmark_exl3.py) and [launch snapshot](run_exl3_bench.sh) are records, not local execution workspaces. Python syntax, shell syntax, a CPU-only dry run and the downloaded HF chat-template thinking-off suffix passed. The runner reads the same JSON/code/prose cases and output checks as `~/qwen38-4090/benchmark_http.py`; it never executes generated Python.

After explicit GPU handoff, the commands are:

```bash
bash ~/qwen38-4090/repos/exllamav3-git/run_qwen38_bench.sh ar
bash ~/qwen38-4090/repos/exllamav3-git/run_qwen38_bench.sh mtp 4
bash ~/qwen38-4090/repos/exllamav3-git/run_qwen38_bench.sh dflash2 7
```

These modes ran serially on physical GPU 3, with cache length 4096, Q4 K/V cache, temperature zero, thinking disabled, maximum 512 generated tokens, and three repetitions of each workload. Each request used a new process and a new Generator with batch size one; all 27 final `cached_tokens` were zero. `Generator.clear_queue()` only aborts/deallocates active jobs, so it was not used as a prefix-cache reset. Native MTP used the target's included head; K4 was explicit. The single MTP depth is reused for later draft positions; EXL3 warns that acceptance may decrease. The pinned DFlash2 model has `dflash_config.block_size=8`, so K7 is its actual native default. A subsequent K15 probe failed on its first request with a tensor-length mismatch (15 versus 7); the raw failure is preserved, and a CPU configuration guard now rejects this unsupported request before loading a GPU model.

Each raw result records full output, model load/warmup duration, generation-call duration, GPU snapshots, prompt/template/helper hashes, native token count and timing fields, cached tokens and draft acceptance. Model load and warmup are excluded from generation-call timing. EXL3 native generation speed uses `new_tokens / time_generate` (N convention), because the source starts that interval immediately before the first decode/draft forward. It includes first decode and excludes bulk prefill. The separate generation-call speed includes tokenization, prefill and decode. Native `time_prefill` is not client TTFT. These values must not be silently combined with HTTP server decode metrics or end-to-end HTTP throughput. GPU 3 is a shared card with another user's process; its before/after snapshots are part of the evidence.

The exact [measured runner](exl3-bench/exl3-runner-before-gpu.py) SHA256 is `32eb6a11d1cc03ee31863f268e68d42101a53a7f8b096b41a7b2c9f8e59ed715`. The current [runner snapshot](benchmark_exl3.py), including the subsequent CPU configuration guard, has SHA256 `390e1f7bdb52852bd66c0b4b7a9edd27fa5a241cc0aff6f623ce7dd0a1184e71`; its [diff](exl3-bench/exl3-runner-config-guard.diff) is preserved. Launcher SHA256: `8545736886c8711f4064f4efece3361b65f5fdaf8e12b30de037c2e5fa81aa96`.
