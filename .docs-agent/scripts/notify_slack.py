"""Close the loop in Slack: reply in the thread a signal came from.

Used by create_briefs.py (brief created) and by the learn workflow (PR merged):
  python notify_slack.py --pr 123   → for every Slack source in the PR's brief,
                                       reply "Docs updated: <link>"
  python notify_slack.py --digest FILE → post FILE's text to the digest channel
  python notify_slack.py --announce 123 --status tested|needs_you|fixing|merged|closed
        → post the PR to slack.announce.channel (first time) or reply in its thread.
          The thread's timestamp is kept as a hidden marker in the PR body.
"""
from __future__ import annotations

import json
import os
import re
import sys

from common import config, gh, http_json

CFG = config()


def _token(workspace: str) -> str | None:
    for ws in CFG["slack"]["workspaces"]:
        if ws["name"] == workspace:
            return os.environ.get(ws["token_secret"])
    return None


def _channel_cfg(workspace: str, channel: str) -> dict:
    for ws in CFG["slack"]["workspaces"]:
        if ws["name"] == workspace:
            for ch in ws.get("channels", []):
                if ch["id"] == channel:
                    return ch
    return {}


def post(workspace: str, channel: str, text: str, thread_ts: str | None = None):
    token = _token(workspace)
    if not token:
        return
    body = {"channel": channel, "text": text, "unfurl_links": False}
    if thread_ts:
        body["thread_ts"] = thread_ts
    r = http_json("https://slack.com/api/chat.postMessage", method="POST",
                  headers={"Authorization": f"Bearer {token}"}, body=body)
    if not r.get("ok"):
        print(f"slack post failed: {r.get('error')}")


def reply_to_source(sig: dict, text: str):
    """Only replies where the channel config allows it. Never in community by default."""
    if sig.get("type") != "slack" or not sig.get("reply_in_thread"):
        return
    post(sig["workspace"], sig["channel"], text, sig["thread_ts"])


def notify_pr_merged(pr: int):
    data = json.loads(gh("pr", "view", str(pr), "--json", "body,url,title"))
    issues = re.findall(r"(?:Closes|Fixes|Resolves) #(\d+)", data["body"] or "")
    for n in issues:
        body = json.loads(gh("issue", "view", n, "--json", "body"))["body"]
        for sid in re.findall(r"<!-- source-id: (slack:[^ ]+) -->", body):
            _, ws, ch, ts = sid.split(":", 3)
            if _channel_cfg(ws, ch).get("reply_in_thread"):
                post(ws, ch, f"Docs updated: {data['title']} — {data['url']}", ts)


THREAD = re.compile(r"<!-- docs-slack-thread: (\S+) (\S+) -->")
STATUS = {
    "opened":    "Opened. Testing on staging now.",
    "tested":    "Tested on staging and ready for review.",
    "needs_you": "Needs a human: the reviewer couldn't clear it automatically. See the latest review comment.",
    "fixing":    "Reviewer found issues; the executor is fixing them.",
    "merged":    "Merged. The docs are live after the next deploy.",
    "closed":    "Closed without merging.",
}


def _post(workspace: str, channel: str, text: str, thread_ts: str | None = None) -> str | None:
    token = _token(workspace)
    if not token or not channel:
        print("announce: Slack token or channel missing, skipping")
        return None
    body = {"channel": channel, "text": text, "unfurl_links": False}
    if thread_ts:
        body["thread_ts"] = thread_ts
    r = http_json("https://slack.com/api/chat.postMessage", method="POST",
                  headers={"Authorization": f"Bearer {token}"}, body=body)
    if not r.get("ok"):
        print(f"announce failed: {r.get('error')}")
        return None
    return r.get("ts")


def announce(pr: int, status: str):
    a = CFG["slack"].get("announce") or {}
    if not a.get("channel"):
        return
    data = json.loads(gh("pr", "view", str(pr), "--json", "title,url,body,labels,files,number"))
    labels = {l["name"] for l in data["labels"]}
    L = CFG["docs"]["labels"]
    kind = "postman" if L["postman"] in labels else "skill_update" if L["skill_update"] in labels else "docs"
    if kind not in a.get("kinds", ["docs"]):
        return
    body = data.get("body") or ""
    m = THREAD.search(body)
    line = STATUS.get(status, status)
    if status in ("tested", "needs_you") and a.get("mention"):
        line += " " + " ".join(f"<@{u}>" for u in a["mention"])
    if m:  # follow-up in the PR's thread
        _post(a["workspace"], m.group(1), line, m.group(2))
        return
    what = {"docs": "New docs PR", "postman": "Postman collection update", "skill_update": "Skill update from the learner"}[kind]
    files = [f["path"] for f in data.get("files", [])]
    pages = [f for f in files if f.endswith((".mdx", ".md")) or f == "openapi.yaml"] or files
    shown = ", ".join(f"`{p}`" for p in pages[:5]) + (f" +{len(pages) - 5} more" if len(pages) > 5 else "")
    brief = re.search(r"(?:Closes|Fixes|Resolves) #(\d+)", body)
    text = (f"*{what}:* <{data['url']}|#{data['number']} {data['title']}>\n"
            f"Files: {shown or 'none'}\n"
            + (f"Brief: #{brief.group(1)}\n" if brief else "")
            + f"Status: {line}")
    ts = _post(a["workspace"], a["channel"], text)
    if ts:  # remember the thread so later updates land in it
        gh("pr", "edit", str(pr), "--body", body.rstrip() + f"\n\n<!-- docs-slack-thread: {a['channel']} {ts} -->")


if __name__ == "__main__":
    if "--announce" in sys.argv:
        n = int(sys.argv[sys.argv.index("--announce") + 1])
        st = sys.argv[sys.argv.index("--status") + 1] if "--status" in sys.argv else "opened"
        announce(n, st)
        sys.exit(0)
    if "--pr" in sys.argv:
        notify_pr_merged(int(sys.argv[sys.argv.index("--pr") + 1]))
    elif "--digest" in sys.argv:
        text = open(sys.argv[sys.argv.index("--digest") + 1]).read()
        post("internal", os.environ.get("SLACK_DIGEST_CHANNEL", ""), text)
