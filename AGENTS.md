# Working on this project

- The benchmark is AA-AgentPerf-Local's default replay, unmodified: 65,536-token context, one sequence, exact output
  lengths, standard sampling. A run that changes any of these is a different result and does not go on the page.
- The page is AA's table plus the RTX 4090, kept as small as theirs: one table, a few setups that people actually use.
- GPU work runs on the experiment server through its GPU queue; nothing else of ours on that card.
- No machine details in the repo (paths, host names, user names): they live in the untracked `bench/env.local.sh`.
- After changes: `python3 bench/collect.py --runs RUNS` and `python3 tools/build_site.py`, then look at the page at
  desktop and phone width in both themes.
