#!/usr/bin/env python3
"""Snapshot Artificial Analysis's laptops & workstations data into bench/aa_snapshot.json.

The page ships its data in the Next.js flight stream: one object with `systems`, `models`, `workload` and `runs`.
This pulls that object out unchanged (every system, model and run, with launch commands) and stamps it with the
source and the retrieval date.

    python3 tools/fetch_aa.py [--html saved_page.html]
"""
import argparse
import datetime
import json
import pathlib
import re
import urllib.request

SOURCE = "https://artificialanalysis.ai/hardware-inference-stack/laptops-workstations"
OUT = pathlib.Path(__file__).resolve().parent.parent / "bench" / "aa_snapshot.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def flight(html):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, re.S)
    return "".join(json.loads('"' + c + '"') for c in chunks)


def data_object(stream):
    """The enclosing object of the `runs` list: walk back over `{` until one decodes with the expected keys."""
    dec, at = json.JSONDecoder(), stream.find('"runs":[')
    while at > 0:
        at = stream.rfind("{", 0, at)
        try:
            obj, _ = dec.raw_decode(stream[at:])
        except ValueError:
            continue
        if isinstance(obj, dict) and {"systems", "models", "runs"} <= obj.keys():
            return obj
    raise SystemExit("no systems/models/runs object in the page; its layout has changed")


def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return None if x == "$undefined" else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", help="parse a saved copy of the page instead of fetching it")
    args = ap.parse_args()
    if args.html:
        html = pathlib.Path(args.html).read_text(errors="replace")
    else:
        req = urllib.request.Request(SOURCE, headers={"User-Agent": UA})
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    data = clean(data_object(flight(html)))
    snap = {"source": SOURCE, "retrieved": datetime.date.today().isoformat(), **data}
    OUT.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n")
    print(f"{OUT.relative_to(OUT.parent.parent)}: {len(data['systems'])} systems, {len(data['models'])} models, "
          f"{len(data['runs'])} runs")


if __name__ == "__main__":
    main()
