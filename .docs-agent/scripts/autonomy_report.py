"""Per-category autonomy readiness from metrics/prs/<pr>.json.

  python autonomy_report.py            → markdown table on stdout
  python autonomy_report.py --json     → same data as JSON

A category is "ready to graduate" (auto-merge) when, over the last
`graduation_window` closed PRs of that category, every PR was merged,
the median human edit ratio is <= graduation_max_human_edit_ratio,
and no PR needed more than one reviewer round.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict

from common import AGENT_DIR, config

A = config()["autonomy"]
WINDOW, MAX_RATIO = A["graduation_window"], A["graduation_max_human_edit_ratio"]


def report() -> list[dict]:
    rows = defaultdict(list)
    for f in sorted((AGENT_DIR / "metrics" / "prs").glob("*.json")):
        m = json.loads(f.read_text())
        rows[m["category"]].append(m)
    out = []
    for cat, ms in sorted(rows.items()):
        last = sorted(ms, key=lambda m: m["date"])[-WINDOW:]
        merged = sum(m["merged"] for m in last)
        ratio = statistics.median(m["human_edit_ratio"] for m in last)
        rounds = max(m["agent_review_rounds"] for m in last)
        ready = (len(last) >= WINDOW and merged == len(last)
                 and ratio <= MAX_RATIO and rounds <= 1)
        out.append({"category": cat, "prs": len(last), "merged": merged,
                    "median_human_edit_ratio": ratio, "max_review_rounds": rounds,
                    "auto_merge_on": A["auto_merge_docs"].get(cat, False),
                    "ready_to_graduate": ready})
    return out


if __name__ == "__main__":
    data = report()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2))
    else:
        print("| Category | PRs (window) | Merged | Median human edits | Max rounds | Auto-merge | Ready? |")
        print("|---|---|---|---|---|---|---|")
        for r in data:
            print(f"| {r['category']} | {r['prs']}/{WINDOW} | {r['merged']} | "
                  f"{r['median_human_edit_ratio']:.0%} | {r['max_review_rounds']} | "
                  f"{'on' if r['auto_merge_on'] else 'off'} | "
                  f"{'yes' if r['ready_to_graduate'] else 'not yet'} |")
