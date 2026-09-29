"""Act on the reviewer's verdict (run/review.json) for one PR.

  pass         → request human reviewers; enable auto-merge if this category graduated
  fix          → add `docs-agent:fix` (executor revises) unless max rounds reached
                 or a human pushed the last commit (then just leave the comment)
  needs_human  → add `docs-agent:needs-human`, request reviewers
  missing file → treat as needs_human (reviewer crashed)
"""
from __future__ import annotations

import json
import re
import sys

from common import RUN_DIR, config, gh
from notify_slack import announce

CFG = config()
L = CFG["docs"]["labels"]


def _announce(pr: int, status: str):
    try:  # Slack trouble must never block the pipeline
        announce(pr, status)
    except Exception as e:
        print(f"slack announce failed: {e}")


def main(pr: int):
    path = RUN_DIR / "review.json"
    review = json.loads(path.read_text()) if path.exists() else {"verdict": "needs_human"}
    verdict = review.get("verdict", "needs_human")

    data = json.loads(gh("pr", "view", str(pr), "--json", "body,commits,comments"))
    rounds = sum(  # includes the comment the reviewer just posted
        "<!-- docs-reviewer -->" in (c.get("body") or "") for c in data["comments"])
    last_msg = data["commits"][-1]["messageBody"] + data["commits"][-1]["messageHeadline"] \
        if data["commits"] else ""
    human_pushed_last = CFG["docs"]["commit_trailer"] not in last_msg
    reviewers = ",".join(CFG["docs"]["reviewers"])

    print(f"verdict={verdict} rounds={rounds} human_pushed_last={human_pushed_last}")

    if verdict == "fix" and not human_pushed_last and rounds <= CFG["reviewer"]["max_rounds"]:
        gh("pr", "edit", str(pr), "--add-label", L["fix"])
        _announce(pr, "fixing")
        return

    if verdict in ("fix", "needs_human"):
        gh("pr", "edit", str(pr), "--add-label", L["needs_human"], "--add-reviewer", reviewers)
        _announce(pr, "needs_you")
        return

    # pass
    try:
        gh("pr", "edit", str(pr), "--remove-label", L["needs_human"])
    except Exception:
        pass  # label wasn't there
    gh("pr", "edit", str(pr), "--add-reviewer", reviewers)
    _announce(pr, "tested")
    m = re.search(r"(?:Closes|Fixes|Resolves) #(\d+)", data["body"] or "")
    category = None
    if m:
        body = json.loads(gh("issue", "view", m.group(1), "--json", "body"))["body"]
        jb = re.search(r"```json\r?\n(.*?)\r?\n```", body, re.S)
        category = json.loads(jb.group(1)).get("doc_category") if jb else None
    if category and CFG["autonomy"]["auto_merge_docs"].get(category):
        print(f"category {category} has graduated → enabling auto-merge")
        gh("pr", "merge", str(pr), "--auto", "--squash")


if __name__ == "__main__":
    main(int(sys.argv[1]))
