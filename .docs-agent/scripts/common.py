"""Shared helpers for the docs agent scripts. Stdlib + PyYAML only."""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]          # repo root
AGENT_DIR = ROOT / ".docs-agent"
RUN_DIR = AGENT_DIR / "run"                         # gitignored scratch for one run
RUN_DIR.mkdir(parents=True, exist_ok=True)


def config() -> dict:
    with open(AGENT_DIR / "config.yml") as f:
        cfg = yaml.safe_load(f)
    # bot_login can live in the repo variable DOCS_AGENT_LOGIN (workflows export it).
    bl = str(cfg["docs"].get("bot_login") or "")
    if not bl or bl.startswith("TODO") or bl == "DOCS_AGENT_LOGIN":
        cfg["docs"]["bot_login"] = os.environ.get("DOCS_AGENT_LOGIN", "")
    return cfg


# ---------- HTTP ----------

def http_json(url: str, method: str = "GET", headers: dict | None = None,
              params: dict | None = None, body: dict | None = None,
              form: dict | None = None) -> dict:
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    data = None
    headers = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        headers.setdefault("Content-Type", "application/json; charset=utf-8")
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else {}


def gh(*args: str, input: str | None = None) -> str:
    """Run the GitHub CLI (authenticated via GH_TOKEN) and return stdout."""
    out = subprocess.run(["gh", *args], input=input, capture_output=True,
                         text=True, check=True)
    return out.stdout


# ---------- Redaction ----------

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
# Phones: international (+CC ...) or 10+ digit runs with separators. Skips ISO dates/times.
_PHONE = re.compile(r"(?<![\w/:.-])(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?){2,4}\d{3,5}(?![\w:])")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$")
_KEYS = re.compile(
    r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{8,}"
    r"|\bxox[abpr]-[A-Za-z0-9-]{10,}"
    r"|\bgh[pousr]_[A-Za-z0-9]{20,}"
    r"|\bSS\.WSS\.[A-Za-z0-9_.-]{8,}"
    r"|\bBearer\s+[A-Za-z0-9_\-.=]{12,}"
    r"|(?i:\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*)['\"]?[^\s'\"]{8,}"
)


def _phone(m: re.Match) -> str:
    s = m.group(0)
    digits = sum(c.isdigit() for c in s)
    if _DATE.match(s.strip()) or digits < 10 or digits > 15:
        return s
    return "[phone]"


def redact(text: str, cfg: dict | None = None) -> str:
    cfg = cfg or config().get("redaction", {})
    keep = set(cfg.get("keep_domains", []))
    if not text:
        return text
    if cfg.get("api_keys", True):
        text = _KEYS.sub("[REDACTED_SECRET]", text)
    if cfg.get("emails", True):
        text = _EMAIL.sub(lambda m: m.group(0) if m.group(1) in keep else "[email]", text)
    if cfg.get("phones", True):
        text = _PHONE.sub(_phone, text)
    return text


# ---------- Signals file ----------

def write_signals(kind: str, items: list[dict]) -> Path:
    """Each collector writes run/signals-<kind>.json; the planner reads them all."""
    path = RUN_DIR / f"signals-{kind}.json"
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"[{kind}] wrote {len(items)} signal(s) → {path.relative_to(ROOT)}")
    return path


LOCAL = os.environ.get("DOCS_AGENT_MODE") == "local"     # set by .docs-agent/local/da
STATE_DIR = AGENT_DIR / "local" / "state"                  # gitignored; local mode only


def local_ledger() -> dict:
    path = STATE_DIR / "ledger.json"
    return json.loads(path.read_text()) if path.exists() else {}


def remember_sources(entries: dict[str, str]):
    """Local mode: record source_id → what happened to it (brief id / skipped reason)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    led = local_ledger()
    led.update(entries)
    (STATE_DIR / "ledger.json").write_text(json.dumps(led, indent=2, ensure_ascii=False))


def known_source_ids() -> set[str]:
    """Source IDs already turned into a brief (open or closed), for dedupe.

    GitHub mode: briefs embed `<!-- source-id: ... -->` markers in the issue body.
    Local mode: .docs-agent/local/state/ledger.json.
    """
    if LOCAL:
        return set(local_ledger())
    label = config()["docs"]["labels"]["brief"]
    try:
        raw = gh("issue", "list", "--label", label, "--state", "all",
                 "--limit", "300", "--json", "body")
    except Exception as e:  # first run / no gh auth locally
        print(f"warn: could not list briefs for dedupe: {e}")
        return set()
    ids: set[str] = set()
    for issue in json.loads(raw):
        ids.update(re.findall(r"<!-- source-id: (\S+) -->", issue.get("body") or ""))
    # Skipped / merged signals are recorded as comments on the ledger issue.
    n = ledger_issue()
    if n:
        comments = json.loads(gh("issue", "view", str(n), "--json", "comments"))["comments"]
        for c in comments:
            ids.update(re.findall(r"<!-- source-id: (\S+) -->", c.get("body") or ""))
    return ids


LEDGER_LABEL = "docs-agent-ledger"


def ledger_issue(create: bool = False) -> int | None:
    """One long-lived issue that records every signal the planner has seen."""
    try:
        found = json.loads(gh("issue", "list", "--label", LEDGER_LABEL, "--state", "all",
                              "--limit", "1", "--json", "number"))
    except Exception:
        return None
    if found:
        return found[0]["number"]
    if not create:
        return None
    gh("label", "create", LEDGER_LABEL, "--force", "--color", "BFD4F2",
       "--description", "Docs agent: signals already processed")
    url = gh("issue", "create", "--title", "Docs agent ledger (do not close)",
             "--label", LEDGER_LABEL, "--body",
             "Every Slack thread, support email and push the planner has looked at. "
             "Each comment is one planner run. Used for dedupe.").strip()
    return int(url.rstrip("/").split("/")[-1])
