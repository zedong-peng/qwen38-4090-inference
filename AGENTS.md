# Working on this project

- The benchmark is the unmodified AA-AgentPerf-Local default replay: 65,536-token context, one sequence, exact output
  lengths, standard sampling. A run that changes any of these is a different result and does not go on the main chart.
- GPU work runs on the experiment server through its GPU queue, one method at a time; nothing else of ours on that card.
- No machine details in the repo (paths, host names, user names): they live in the untracked `bench/env.local.sh`.
- Methods that did not run keep their row with the reason; missing numbers stay missing.
- After changes: `python3 bench/collect.py` and `python3 tools/build_site.py`, then look at the page at desktop and
  phone width in both themes.
