"""Gather everything humans said and changed on a closed docs-agent PR.

  python collect_feedback.py --pr 123   → run/feedback.json, run/metrics-line.json

Feedback sources (in order of signal strength):
  1. Human commits pushed to the PR branch (what they actually rewrote)
  2. "@docs-agent ..." change requests + review comments (what they asked for)
  3. Reviewer-agent findings and how many rounds it took
  4. Answers on the brief issue (open questions the planner should have caught)
  5. Closed without merge → the whole brief was wrong or unwanted
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess

from common import AGENT_DIR, RUN_DIR, config, gh

CFG = config()
BOT = CFG["docs"]["bot_login"]
TRAILER = CFG["docs"]["commit_trailer"]
REPO = CFG["docs"]["repo"]


def is_agent_commit(c: dict) -> bool:
    msg = c["commit"]["message"]
    login = (c.get("author") or {}).get("login", "")
    return TRAILER in msg or login == BOT or login.endswith("[bot]")   # BOT = the docs bot account


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", type=int, required=True)
    n = ap.parse_args().pr

    pr = json.loads(gh("pr", "view", str(n), "--json",
                       "number,title,body,url,state,mergedAt,createdAt,closedAt,labels,"
                       "headRefName,baseRefName,additions,deletions"))
    commits = json.loads(gh("api", f"repos/{REPO}/pulls/{n}/commits?per_page=100"))
    reviews = json.loads(gh("api", f"repos/{REPO}/pulls/{n}/reviews?per_page=100"))
    rcomments = json.loads(gh("api", f"repos/{REPO}/pulls/{n}/comments?per_page=100"))
    icomments = json.loads(gh("api", f"repos/{REPO}/issues/{n}/comments?per_page=100"))

    # Human edits = the patches of commits humans pushed themselves (merge commits,
    # e.g. "Update branch", excluded). If humans never pushed, it's empty.
    human_commits = [c for c in commits
                     if not is_agent_commit(c) and len(c.get("parents", [])) < 2]
    human_diff, human_lines = "", 0
    for c in human_commits:
        detail = json.loads(gh("api", f"repos/{REPO}/commits/{c['sha']}"))
        human_diff += f"### commit {c['sha'][:10]} by {(c.get('author') or {}).get('login', '?')}: " \
                      f"{c['commit']['message'].splitlines()[0]}\n"
        for f in detail.get("files", []):
            human_lines += f["additions"] + f["deletions"]
            human_diff += f"--- {f['filename']}\n{(f.get('patch') or '')[:8000]}\n"

    def human(c):  # REST objects: bots have user.type == "Bot"
        u = c.get("user") or {}
        login = u.get("login", "")
        # The docs bot is a normal user account, so match it by login too.
        return u.get("type") != "Bot" and not login.endswith("[bot]") and login != BOT

    requests = [{"who": c["user"]["login"], "text": c["body"], "at": c["created_at"]}
                for c in icomments + rcomments
                if human(c) and "@docs-agent" in (c.get("body") or "")]
    review_comments = [{"who": c["user"]["login"], "path": c.get("path"),
                        "line": c.get("line"), "text": c["body"]}
                       for c in rcomments if human(c) and "@docs-agent" not in c["body"]]
    review_verdicts = [{"who": r["user"]["login"], "state": r["state"], "text": r.get("body", "")}
                       for r in reviews if human(r)]
    agent_reviews = [c["body"] for c in icomments
                     if "<!-- docs-reviewer -->" in (c.get("body") or "")]

    brief = None
    m = re.search(r"(?:Closes|Fixes|Resolves) #(\d+)", pr.get("body") or "")
    if m:
        issue = json.loads(gh("api", f"repos/{REPO}/issues/{m.group(1)}"))
        issue_comments = json.loads(gh("api", f"repos/{REPO}/issues/{m.group(1)}/comments?per_page=100"))
        jb = re.search(r"```json\r?\n(.*?)\r?\n```", issue["body"] or "", re.S)
        brief = {"number": issue["number"], "title": issue["title"],
                 "json": json.loads(jb.group(1)) if jb else None,
                 "human_answers": [c["body"] for c in issue_comments if human(c)]}

    total_lines = max(pr["additions"] + pr["deletions"], 1)
    merged = pr.get("mergedAt") is not None
    labels = {l["name"] for l in pr.get("labels", [])}
    local = CFG["docs"]["labels"].get("local") in labels
    category = "local" if local else "postman" if CFG["docs"]["labels"]["postman"] in labels else \
        ((brief or {}).get("json") or {}).get("doc_category", "unknown")
    opened = dt.datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
    closed = dt.datetime.fromisoformat((pr.get("closedAt") or pr["createdAt"]).replace("Z", "+00:00"))

    full_diff = ""
    if local:  # for hand-written PRs the whole diff is the lesson
        full_diff = subprocess.run(["gh", "pr", "diff", str(n)], capture_output=True, text=True).stdout[:80000]
    feedback = {
        "pr": {k: pr[k] for k in ("number", "title", "url", "state")},
        "merged": merged,
        "written_by_human": local,     # the whole PR is a human's version of the brief
        "human_diff_full": full_diff or None,
        "brief": brief,
        "human_edit_diff": human_diff[:60000],
        "change_requests": requests,
        "review_comments": review_comments,
        "review_verdicts": review_verdicts,
        "agent_review_rounds": len(agent_reviews),
        "agent_review_last": agent_reviews[-1][:6000] if agent_reviews else None,
    }
    metrics = {
        "pr": n, "date": closed.date().isoformat(), "category": category,
        "merged": merged, "human_commits": len(human_commits),
        "human_edit_ratio": round(human_lines / total_lines, 3),
        "change_requests": len(requests), "review_comments": len(review_comments),
        "agent_review_rounds": len(agent_reviews),
        "hours_to_close": round((closed - opened).total_seconds() / 3600, 1),
    }
    (RUN_DIR / "feedback.json").write_text(json.dumps(feedback, indent=2, ensure_ascii=False))
    (RUN_DIR / "metrics-line.json").write_text(json.dumps(metrics))
    # One file per PR: no merge conflicts between concurrent learner PRs, and the
    # workflow commits it straight to main so a rejected skill PR doesn't lose it.
    out = AGENT_DIR / "metrics" / "prs"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{n}.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
