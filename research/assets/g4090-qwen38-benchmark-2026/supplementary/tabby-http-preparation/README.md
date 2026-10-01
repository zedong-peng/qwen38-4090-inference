# Inactive benchmark-only DFlash2 HTTP launcher

Nothing started or enabled. Only an explicit launch without --check selects GPU3.

CPU validation:
  ~/qwen38-4090/repos/tabbyAPI/launch_dflash2_http.sh --check

Foreground GPU start, after root agent handoff:
  ~/qwen38-4090/repos/tabbyAPI/launch_dflash2_http.sh

Endpoint http://127.0.0.1:18041; request model qwen3.8-27b. Alias uses official dummy_model_names; the physical model directory remains unchanged. Use temperature=0, seed42, presence_penalty=0, frequency_penalty=0, max_tokens512 and chat_template_kwargs.enable_thinking=false. The config forces thinking false and avoids safe_defaults sampler overrides.

Cold-prefix for the current short JSON/code/prose suite:
- Templated prompt must be below256 tokens and prompt+output below2048 checkpoint.
- sysmem_recurrent_cache=0 stores no checkpoint in these short cases. Recurrent models skip partial-page reuse; full-page KV reuse needs a stored recurrent checkpoint.
- Confirm timings.cache_n=0 and usage.prompt_tokens_details.cached_tokens=0 for every measured response.
- cache_prompt=false is not an official Tabby cache-control field.
- model.warmup=false avoids load-time long synthetic prompts reaching a zero-budget checkpoint. The short Say hello benchmark warmup can run instead.
- Zero budget is NOT safe for general long prompts: RecurrentCache.put can attempt to evict an empty cache. For wider cold tests use a fresh process or unload/load with nonzero recurrent budget, repeating all model/draft load settings.
- No official global disable-prefix or clear-cache endpoint was found; only /v1/model/unload and /v1/model/load. No runtime monkeypatch installed.

Timing:
Tabby get_timings predicts gen_tokens/gen_time because EXL3 gen_time includes the first decode pass; NInfer/llama divide output_tokens-1 by predicted_ms. Preserve these server definitions and use client wall-based e2e as a common denominator.

Exact sources:
Tabby config_sample.yml/common/config_models.py for keys; common/tabby_config.py for --config; backends/exllamav3/model.py for generator settings and cached-token accounting; endpoints/OAI/utils/common_.py for usage and timing. EXL3 generator/pagetable.py limits prefix KV reuse to recurrent checkpoints; generator/job.py skips recurrent partial-page reuse and stashes prompt-end checkpoints; cache/recurrent.py shows zero-budget eviction.
