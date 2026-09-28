"""Turn the planner's run/briefs.json into GitHub issues (the handoff to the executor).

* confidence >= planner.auto_ready_min_confidence and no open questions
      → labels: docs-brief, docs-brief:ready     (executor starts automatically)
* otherwise → labels: docs-brief, docs-brief:needs-info  (a human answers, then adds :ready)
* skipped / merged signals → one comment on the ledger issue (dedupe)
* Slack threads with reply_in_thread → short reply linking the brief
"""
from __future__ import annotations

import json

from common import RUN_DIR, config, gh, ledger_issue
from notify_slack import reply_to_source

CFG = config()
L = CFG["docs"]["labels"]
MIN_CONF = CFG["planner"]["auto_ready_min_confidence"]


def ensure_labels():
    colors = {L["brief"]: "0E8A16", L["ready"]: "1D76DB", L["needs_info"]: "FBCA04",
              L["agent_pr"]: "5319E7", L["fix"]: "D93F0B", L["needs_human"]: "B60205",
              L["skill_update"]: "C5DEF5", L["postman"]: "0B7285"}
    for name, color in colors.items():
        gh("label", "create", name, "--force", "--color", color)


def render(b: dict) -> str:
    src = "\n".join(f"- [{s['source_id']}]({s['url']}){' — ' + s['note'] if s.get('note') else ''}"
                    f"\n  <!-- source-id: {s['source_id']} -->" for s in b["sources"])
    pages = "\n".join(f"| `{p['path']}` | {p['action']} | {p.get('doc_type', '')} | {p['what']} |"
                      for p in b["pages"])
    facts = "\n".join(f"- {f['fact']}  \n  _evidence:_ {f['evidence']}" for f in b["facts"])
    tests = "\n".join(f"- [ ] {t}" for t in b["test_plan"]) or "- Prose only, no runnable checks"
    qs = "\n".join(f"- [ ] {q}" for q in b.get("open_questions", [])) or "None"
    uc = b["use_case"]
    flows = "\n".join(f"- `{f['name']}` on `{f['page']}`: {f['goal']}"
                       + (f" (screenshots: {', '.join(f.get('screenshots', []))})" if f.get('screenshots') else "")
                       for f in b.get("ui_flows", [])) or "None"
    return f"""{b['summary']}

**Change type:** `{b['change_type']}` · **Category:** `{b.get('doc_category', 'n/a')}` · **Confidence:** {b['confidence']:.2f} · **Changelog:** {'yes' if b.get('changelog') else 'no'} · **Postman:** {'yes' if b.get('postman') else 'no'}

### Sources
{src}

### Pages
| Path | Action | Doc type | What to change |
|---|---|---|---|
{pages}

### Verified facts (the only claims the executor may make)
{facts}

### Example to use
**Persona:** {uc['persona']}{' (from a real signal, anonymised)' if uc.get('from_real_signal') else ''}
{uc['scenario']}

### Dashboard flows (browser: capture screenshots + verify click-paths)
{flows}

### Test plan (for the reviewer)
{tests}

### Open questions{' — ask ' + b['ask'] if b.get('ask') else ''}
{qs}

<details><summary>Machine-readable brief</summary>

```json
{json.dumps(b, indent=2, ensure_ascii=False)}
```
</details>
"""


def main():
    path = RUN_DIR / "briefs.json"
    if not path.exists():
        print("planner produced no briefs.json — nothing to do")
        return
    plan = json.loads(path.read_text())
    ensure_labels()
    signals = {}
    for f in RUN_DIR.glob("signals-*.json"):
        for s in json.loads(f.read_text()):
            signals[s["source_id"]] = s

    created = []
    for b in plan.get("briefs", [])[: CFG["planner"]["max_briefs_per_run"]]:
        ready = b["confidence"] >= MIN_CONF and not b.get("open_questions")
        labels = [L["brief"], L["ready"] if ready else L["needs_info"]]
        url = gh("issue", "create", "--title", b["title"], "--body", render(b),
                 "--label", ",".join(labels)).strip()
        created.append({"url": url, "title": b["title"], "ready": ready})
        print(f"brief: {url} ({'ready' if ready else 'needs info'})")
        for s in b["sources"]:
            sig = signals.get(s["source_id"])
            if sig:
                msg = (f"Thanks — I've turned this into a docs brief: {url}"
                       if ready else
                       f"I've drafted a docs brief but need an answer first: {url}")
                reply_to_source(sig, msg)

    for m in plan.get("merged_into_existing", []):
        sig = signals.get(m["source_id"], {})
        gh("issue", "comment", str(m["issue"]), "--body",
           f"Related signal: {sig.get('url', m['source_id'])}\n\n{m.get('note', '')}\n\n"
           f"<!-- source-id: {m['source_id']} -->")

    ledger_lines = [f"- `{s['source_id']}` — {s['reason']}\n  <!-- source-id: {s['source_id']} -->"
                    for s in plan.get("skipped", [])]
    ledger_lines += [f"- `{m['source_id']}` — merged into #{m['issue']}\n  <!-- source-id: {m['source_id']} -->"
                     for m in plan.get("merged_into_existing", [])]
    if ledger_lines:
        n = ledger_issue(create=True)
        gh("issue", "comment", str(n), "--body",
           "**Planner run — skipped or merged signals**\n\n" + "\n".join(ledger_lines))

    (RUN_DIR / "created.json").write_text(json.dumps(created, indent=2))


if __name__ == "__main__":
    main()
