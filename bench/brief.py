"""Print one line from a finished agentperf-local result directory: completion time and the headline rates."""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
s = json.loads((out / "summary.json").read_text())
t = s["totals"]
print(
    f"turns={t['successful_turns']}/{t['turns']} completion={t['total_inference_latency_ms'] / 60000:.2f}min "
    f"out_tps={s.get('output_tokens_per_second') or 0:.1f} cached={t.get('total_server_cached_prompt_tokens')} "
    f"uncached={t.get('total_server_uncached_prompt_tokens')}"
)
