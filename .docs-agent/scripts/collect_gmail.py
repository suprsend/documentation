"""Collect resolved support threads from the Gmail support inbox.

Auth: OAuth refresh token for the support@ mailbox (scope gmail.modify).
Secrets: GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN.

  python collect_gmail.py              → run/signals-gmail.json (redacted)
  python collect_gmail.py --mark-seen  → labels those threads `seen_label`
                                         (run only after briefs were created,
                                         so a failed run retries next time)
"""
from __future__ import annotations

import base64
import json
import os
import sys

from common import RUN_DIR, config, http_json, known_source_ids, redact, write_signals

CFG = config()["gmail"]
BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def token() -> str:
    data = http_json("https://oauth2.googleapis.com/token", method="POST", form={
        "client_id": os.environ["GMAIL_CLIENT_ID"],
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })
    return data["access_token"]


def body_text(payload: dict) -> str:
    """Prefer text/plain; fall back to the first part with data."""
    stack, fallback = [payload], ""
    while stack:
        p = stack.pop(0)
        data = p.get("body", {}).get("data")
        if data:
            txt = base64.urlsafe_b64decode(data + "===").decode("utf-8", "replace")
            if p.get("mimeType") == "text/plain":
                return txt
            fallback = fallback or txt
        stack.extend(p.get("parts", []))
    return fallback


def strip_quoted(text: str) -> str:
    """Drop quoted history ("On ... wrote:" and > lines) to avoid repeating the thread."""
    lines = []
    for line in text.splitlines():
        if line.startswith(">") or (line.startswith("On ") and line.rstrip().endswith("wrote:")):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def header(msg: dict, name: str) -> str:
    for h in msg["payload"].get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def collect() -> list[dict]:
    if not os.environ.get("GMAIL_REFRESH_TOKEN"):
        print("skip gmail: GMAIL_REFRESH_TOKEN not set")
        return []
    auth = {"Authorization": f"Bearer {token()}"}
    listing = http_json(f"{BASE}/threads", headers=auth,
                        params={"q": CFG["query"], "maxResults": CFG["max_threads"]})
    out = []
    for t in listing.get("threads", []):
        th = http_json(f"{BASE}/threads/{t['id']}", headers=auth, params={"format": "full"})
        msgs = []
        for m in th.get("messages", []):
            sender = header(m, "From")
            role = "suprsend support" if "suprsend.com" in sender else "customer"
            msgs.append({"who": role, "text": redact(strip_quoted(body_text(m["payload"])))[:6000]})
        subject = header(th["messages"][0], "Subject") if th.get("messages") else ""
        out.append({
            "source_id": f"gmail:{t['id']}",
            "type": "support_email",
            "thread_id": t["id"],
            "subject": redact(subject),
            "url": f"https://mail.google.com/mail/u/0/#all/{t['id']}",
            "thread": msgs,
        })
    return out


def mark_seen():
    path = RUN_DIR / "signals-gmail.json"
    if not path.exists() or not os.environ.get("GMAIL_REFRESH_TOKEN"):
        return
    auth = {"Authorization": f"Bearer {token()}"}
    labels = http_json(f"{BASE}/labels", headers=auth).get("labels", [])
    label = next((l for l in labels if l["name"] == CFG["seen_label"]), None)
    if not label:
        label = http_json(f"{BASE}/labels", method="POST", headers=auth,
                          body={"name": CFG["seen_label"]})
    for s in json.loads(path.read_text()):
        http_json(f"{BASE}/threads/{s['thread_id']}/modify", method="POST", headers=auth,
                  body={"addLabelIds": [label["id"]]})
    print("gmail: marked threads as seen")


if __name__ == "__main__":
    if "--mark-seen" in sys.argv:
        mark_seen()
    else:
        known = known_source_ids()
        write_signals("gmail", [s for s in collect() if s["source_id"] not in known])
