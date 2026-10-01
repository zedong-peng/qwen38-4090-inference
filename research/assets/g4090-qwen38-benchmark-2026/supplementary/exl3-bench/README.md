# g4090 EXL3 GPU measurements

Measured 2026-10-01, EXL3 commit `d3739fd393337b1ff4d6c2a342b12f0c87a9592f`, Torch 2.10.0+cu128, RTX 4090 physical GPU 3 (`GPU-REDACTED`). This was a shared card. Before/after GPU snapshots in every raw request retain other users' changing activity; no other user's process was altered.

The target was pinned Qwen3.8-27B EXL3 4.00bpw, with Q4 K/V cache, context 4096, batch one, temperature zero, thinking disabled, and maximum 512 generated tokens. The JSON/code/prose user messages match the HTTP benchmark helper. Each of the three modes ran three repetitions per workload in separate fresh processes, excluding model load and warmup from generation-call timing. All 27 requests completed, and every final `cached_tokens` was zero.

| Mode | JSON native / call token/s | Code native / call token/s | Prose native / call token/s |
| --- | ---: | ---: | ---: |
| AR K0 | 53.52 / 51.57 | 53.49 / 52.84 | 53.39 / 53.03 |
| Native MTP K4 | 132.95 / 121.24 | 134.34 / 130.10 | 73.65 / 72.84 |
| DFlash2 K7 | 142.98 / 126.86 | 185.25 / 172.71 | 80.19 / 78.94 |

Values are medians of three repetitions. **Native** means EXL3's `new_tokens / time_generate`, using its N counter convention and excluding bulk prefill. **Call** means `new_tokens / generation_call_wall_s`, including tokenization, prefill and decode, while excluding model load/warmup. These are native measurements, not HTTP server decode rates or HTTP end-to-end throughput. [Full aggregate metrics](exl3-suite-summary.json) retain prefill time, load/warmup time, acceptance, token counts, cache counts and quality checks.

All JSON responses used 171 native new tokens and passed JSON/three-district checks. Code and prose responses used the 512-token budget. Every code response failed the Python syntax check at this truncated output budget; generated code was not executed. Story outputs contained 392–394 words, below the requested 500 words. A successful generation request therefore does not establish a complete or semantically correct answer.

DFlash2 was the fastest EXL3 configuration in all three cases. Its draft acceptance medians were 59.74% / 70.76% / 19.42% for JSON/code/prose; MTP4's were 79.27% / 77.40% / 30.17%. The Cinf HTTP matrix on this machine recorded higher corresponding throughputs: K7 JSON/code server decode 238.62 / 213.94 and HTTP end-to-end 208.45 / 205.35 token/s; K3 prose server decode 100.24 and HTTP end-to-end 98.89 token/s. Counter and API timing conventions differ, so the native and HTTP columns remain separate. These observed results support retaining Cinf for the persistent service.

The largest recorded before/after GPU memory readings were 14,961 MiB (AR), 15,819 MiB (MTP4), and 17,247 MiB (DFlash2 K7). They include other processes and are snapshots, not an isolated model footprint or peak-memory measurement. The initial AR process spent 119.67 seconds loading/warming up. Lazy initialization also affected the first generation in each mode; those rows were retained, including AR's initial 10.05-second prefill. Medians do not replace the individual observations.

The downloaded draft's [pinned configuration](dflash2-config-pinned.json) has `dflash_config.block_size=8`. Native EXL3 sets its default draft length to `block_size-1`, so **K7 is the actual default for these weights**. A K15 probe naturally exited on its first worker with `tensor a (15)` versus `tensor b (7)` mismatch, not OOM. [Failure records](exl3-dflash2-k15-cq4-cs4096/exl3-dflash2-k15-cq4-cs4096.json) and the [worker log](exl3-dflash2-k15-cq4-cs4096/exl3-dflash2-k15-cq4-cs4096-json-0.log) remain archived. It has no throughput or cached-token result. The runner now validates the model-specific limit on CPU; its [guard diff](exl3-runner-config-guard.diff) and [CPU rejection check](exl3-dflash2-k15-guard-check.json) are included.

The exact executed [runner](exl3-runner-before-gpu.py) has SHA256 `32eb6a11d1cc03ee31863f268e68d42101a53a7f8b096b41a7b2c9f8e59ed715`. The [guarded runner](benchmark_exl3_guarded.py) has SHA256 `390e1f7bdb52852bd66c0b4b7a9edd27fa5a241cc0aff6f623ce7dd0a1184e71`. All code ran or was edited inside the independent remote Git clone; local wiki source repositories remain original and clean. [Deployment provenance and model integrity checks](../exl3-deployment-notes.md).

Raw mode records: [AR](exl3-ar-k0-cq4-cs4096/exl3-ar-k0-cq4-cs4096.json), [MTP4](exl3-mtp-k4-cq4-cs4096/exl3-mtp-k4-cq4-cs4096.json), [DFlash2 K7](exl3-dflash2-k7-cq4-cs4096/exl3-dflash2-k7-cq4-cs4096.json). Each directory also contains all nine individual result JSONs and worker logs. The master logs and failed K15 probe are retained beside them.
