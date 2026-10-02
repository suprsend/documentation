"""Keep the Postman collection and its copy in this repo in sync.

  python postman_sync.py pull     → write postman/collection.json from Postman and record
                                    postman/.remote-hash (what Postman looked like)
  python postman_sync.py env OUT  → write a newman environment file from config + env vars
  python postman_sync.py check    → fail if the repo collection contains secret values
  python postman_sync.py push     → upload postman/collection.json to Postman, but only if
                                    Postman still matches .remote-hash (nobody edited it
                                    in the Postman app since the agent pulled)

Needs POSTMAN_API_KEY for pull/push. Uses the Postman API v1:
GET/PUT https://api.getpostman.com/collections/{uid}
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

from common import ROOT, config, http_json

# Secret-shaped values that must never be literal in the committed collection.
# Covers Management (SS.ST.), Workspace (SS.WS.) and public API (SS.API.) tokens
# in both top-level request headers and anywhere inside saved `response[]` items
# (`response[*].header` and `response[*].originalRequest.header`).
_TOKEN_PREFIX = re.compile(r"SS\.(ST|WS|API)\.[A-Za-z0-9._\-]+")
_BEARER_LITERAL = re.compile(r"(?i)Bearer\s+(?!\{\{)([A-Za-z0-9._\-]{12,})")
_SVCTOKEN_LITERAL = re.compile(r"(?i)ServiceToken\s+(?!\{\{)([A-Za-z0-9._\-]{12,})")

CFG = config()["postman"]
FILE = ROOT / CFG["file"]
HASH_FILE = FILE.parent / ".remote-hash"
URL = f"https://api.getpostman.com/collections/{CFG['collection_uid']}"
VOLATILE_INFO = {"_postman_id", "updatedAt", "createdAt", "lastUpdatedBy", "uid", "fork"}


def _headers() -> dict:
    return {"X-Api-Key": os.environ["POSTMAN_API_KEY"]}


def normalise(col: dict) -> dict:
    col = json.loads(json.dumps(col))
    for k in VOLATILE_INFO:
        col.get("info", {}).pop(k, None)

    def strip_ids(node):
        if isinstance(node, dict):
            for k in ("id", "_postman_id", "uid"):
                node.pop(k, None)
            for v in node.values():
                strip_ids(v)
        elif isinstance(node, list):
            for v in node:
                strip_ids(v)
    strip_ids(col)
    return col


def digest(col: dict) -> str:
    return hashlib.sha256(json.dumps(normalise(col), sort_keys=True).encode()).hexdigest()


def pull():
    col = http_json(URL, headers=_headers())["collection"]
    for k in VOLATILE_INFO - {"_postman_id"}:   # keep item ids: Postman needs them on PUT
        col.get("info", {}).pop(k, None)
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(col, indent=2, ensure_ascii=False) + "\n")
    HASH_FILE.write_text(digest(col) + "\n")
    print(f"pulled {col['info']['name']} → {FILE.relative_to(ROOT)}")


def env(out: str):
    values = []
    for key, spec in CFG["environment"].items():
        val = os.environ.get(spec[4:], "") if str(spec).startswith("env:") else spec
        values.append({"key": key, "value": val, "type": "secret" if str(spec).startswith("env:") else "default",
                       "enabled": True})
    with open(out, "w") as f:
        json.dump({"name": "docs-agent staging", "values": values}, f)
    print(f"environment → {out}")


def _iter_header_values(col: dict):
    """Yield (path, value) for every header value anywhere in the collection,
    including saved responses (`response[*].header`,
    `response[*].originalRequest.header`). PR #255 shipped leaked ServiceToken
    values in saved responses because the old check only read the file as text
    without knowing where headers live; walk the tree so nothing escapes."""
    def walk(node, path):
        if isinstance(node, dict):
            # A Postman header is {"key": "...", "value": "..."}; emit raw values.
            if "key" in node and "value" in node and isinstance(node.get("value"), str):
                yield path, node["value"]
            for k, v in node.items():
                yield from walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{path}[{i}]")
    yield from walk(col, "")


def check():
    """The collection is public. No secret value may ever be baked into it.

    Three sweeps:
      1. Known env-provided secret values (exact match anywhere in the file).
      2. Known SuprSend token prefixes `SS.ST.`, `SS.WS.`, `SS.API.`
         (catches rotated/stale tokens the env no longer knows about).
      3. `Bearer <literal>` / `ServiceToken <literal>` header values that are
         not `{{variables}}` — any header, including inside saved responses.
    """
    text = FILE.read_text()
    col = json.loads(text)

    problems: list[str] = []

    env_leaks = [spec[4:] for spec in CFG["environment"].values()
                 if str(spec).startswith("env:") and os.environ.get(spec[4:])
                 and os.environ[spec[4:]] in text]
    if env_leaks:
        problems.append(
            f"collection contains the value of {', '.join(env_leaks)}: use {{{{variables}}}}")

    prefix_hits = sorted({m.group(0) for m in _TOKEN_PREFIX.finditer(text)})
    if prefix_hits:
        problems.append(
            "collection contains SuprSend token prefixes (SS.ST./SS.WS./SS.API.): "
            + ", ".join(prefix_hits[:5])
            + (f" (+{len(prefix_hits) - 5} more)" if len(prefix_hits) > 5 else ""))

    literal_header_hits: list[str] = []
    for path, value in _iter_header_values(col):
        if _BEARER_LITERAL.search(value) or _SVCTOKEN_LITERAL.search(value):
            literal_header_hits.append(f"{path} = {value[:40]}…")
    if literal_header_hits:
        problems.append(
            "header values hold literal tokens (use {{api_key}} / {{service_token}}): "
            + "; ".join(literal_header_hits[:5])
            + (f" (+{len(literal_header_hits) - 5} more)"
               if len(literal_header_hits) > 5 else ""))

    if problems:
        sys.exit("\n".join(problems))
    print("no secrets in collection")


def push():
    remote = http_json(URL, headers=_headers())["collection"]
    expected = HASH_FILE.read_text().strip() if HASH_FILE.exists() else None
    if expected and digest(remote) != expected:
        sys.exit("Postman changed since the agent pulled it (someone edited it in the app). "
                 "Re-run docs-postman to rebase on the latest version, then merge again.")
    local = json.loads(FILE.read_text())
    http_json(URL, method="PUT", headers=_headers(), body={"collection": local})
    print("pushed collection to Postman")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pull":
        pull()
    elif cmd == "env":
        env(sys.argv[2])
    elif cmd == "check":
        check()
    elif cmd == "push":
        push()
    else:
        sys.exit(__doc__)
