"""Collect candidate doc signals from Slack (internal + community workspaces).

For each configured channel, reads top-level messages from the lookback window
plus their thread replies. `mode: flagged` channels only keep threads where
someone reacted with the flag emoji. Community content is redacted.

Bot scopes needed: channels:history, groups:history, channels:read, reactions:read,
users:read, chat:write (internal only, for replies; see notify_slack.py).
Channels flagged `external` (and whole workspaces flagged `external`, like the
community) are redacted and never replied to. `auto_channels: true` watches every
public channel the bot has been invited to.

Output: run/signals-slack.json — one signal per thread.
"""
from __future__ import annotations

import os
import time
import urllib.error

from common import config, http_json, known_source_ids, redact, write_signals

CFG = config()
SLACK = CFG["slack"]
API = "https://slack.com/api/"


def call(token: str, method: str, **params) -> dict:
    for attempt in range(5):
        try:
            data = http_json(API + method, headers={"Authorization": f"Bearer {token}"},
                             params=params)
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Slack rate limit: honour Retry-After
                time.sleep(int(e.headers.get("Retry-After", 2 ** attempt)))
                continue
            raise
        if data.get("ok"):
            return data
        raise RuntimeError(f"slack {method}: {data.get('error')}")
    raise RuntimeError(f"slack {method}: still rate limited after retries")


def has_flag(msg: dict) -> bool:
    return any(r.get("name") == SLACK["flag_emoji"] for r in msg.get("reactions", []))


def user_name(token: str, uid: str, cache: dict) -> str:
    if uid not in cache:
        try:
            u = call(token, "users.info", user=uid)["user"]
            cache[uid] = u.get("real_name") or u.get("name") or uid
        except Exception:
            cache[uid] = uid
    return cache[uid]


def collect() -> list[dict]:
    oldest = time.time() - SLACK["lookback_hours"] * 3600
    out = []
    for ws in SLACK["workspaces"]:
        token = os.environ.get(ws["token_secret"])
        if not token:
            print(f"skip workspace {ws['name']}: {ws['token_secret']} not set")
            continue
        is_community = ws.get("external", False)
        names: dict = {}
        channels = list(ws.get("channels", []))
        if ws.get("auto_channels"):
            try:
                joined = call(token, "users.conversations", types="public_channel,private_channel", limit=500,
                              exclude_archived="true").get("channels", [])
                known = {c["id"] for c in channels}
                channels += [{"id": c["id"], "name": c.get("name"), "mode": ws.get("default_mode", "all"),
                              "reply_in_thread": False} for c in joined if c["id"] not in known]
            except Exception as e:
                print(f"warn: {ws['name']}: could not list the bot's channels: {e}")
        for ch in channels:
            try:
                out.extend(collect_channel(token, ws, ch, oldest, is_community, names))
            except Exception as e:  # one bad channel must not block planning
                print(f"warn: {ws['name']}/{ch['id']}: {e}")
    return out


def collect_channel(token, ws, ch, oldest, is_community, names) -> list[dict]:
    out = []
    is_community = is_community or ch.get("external", False)
    hist = call(token, "conversations.history", channel=ch["id"],
                oldest=f"{oldest:.6f}", limit=200)
    for msg in hist.get("messages", []):
        if msg.get("subtype") in {"channel_join", "channel_leave", "channel_topic"}:
            continue
        if (msg.get("subtype") == "bot_message" or msg.get("bot_id")) and not ch.get("include_bots"):
            continue
        replies = [msg]
        if msg.get("reply_count"):
            replies = call(token, "conversations.replies", channel=ch["id"],
                           ts=msg["ts"], limit=200).get("messages", [msg])
        flagged = any(has_flag(m) for m in replies)
        if ch["mode"] == "flagged" and not flagged:
            continue
        perm = call(token, "chat.getPermalink", channel=ch["id"],
                    message_ts=msg["ts"]).get("permalink")
        thread = []
        for m in replies:
            if m.get("bot_id") and not m.get("user"):
                who = m.get("username") or (m.get("bot_profile") or {}).get("name") or "bot"
            else:
                who = "community member" if is_community else user_name(token, m.get("user", ""), names)
            text = m.get("text", "")
            thread.append({"who": who, "text": redact(text) if is_community else text,
                           "is_bot": bool(m.get("bot_id"))})
        out.append({
            "source_id": f"slack:{ws['name']}:{ch['id']}:{msg['ts']}",
            "type": "slack",
            "workspace": ws["name"],
            "channel": ch["id"],
            "channel_name": ch.get("name"),
            "thread_ts": msg["ts"],
            "url": perm,
            "flagged": flagged,
            "reply_in_thread": ch.get("reply_in_thread", False) and not is_community,
            "thread": thread,
        })
    return out


if __name__ == "__main__":
    known = known_source_ids()
    write_signals("slack", [s for s in collect() if s["source_id"] not in known])
