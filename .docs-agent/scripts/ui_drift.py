"""Turn a weekly `run_flow.mjs --mode verify --all` run into docs briefs.

  python ui_drift.py        (reads .docs-agent/run/browser.json)

* A flow step failed → the dashboard no longer matches the documented click-path.
  Brief labelled needs-info: a human confirms what changed in the UI before the
  executor rewrites the steps.
* Every step passed but screenshots are stale/missing → brief labelled ready,
  category screenshot_refresh: the executor re-captures them.
Only one open brief per flow at a time.
"""
from __future__ import annotations

import datetime as dt
import json

from common import RUN_DIR, config, gh
from create_briefs import L, ensure_labels, render

RUN_URL = __import__("os").environ.get("RUN_URL", "")


def open_flow_briefs() -> set[str]:
    raw = gh("issue", "list", "--label", L["brief"], "--state", "open",
             "--limit", "200", "--json", "body")
    flows = set()
    for i in json.loads(raw):
        for line in (i.get("body") or "").splitlines():
            if "<!-- ui-flow: " in line:
                flows.add(line.split("<!-- ui-flow: ")[1].split(" -->")[0])
    return flows


def brief_for(r: dict) -> dict | None:
    pages = r["page"] if isinstance(r["page"], list) else [r["page"]]
    week = dt.date.today().isocalendar()
    sid = f"ui:{r['flow']}:{week[0]}-W{week[1]:02d}"
    evidence = f"Weekly browser run {RUN_URL} (artifact `ui-drift`)"
    if not r["ok"]:
        bad = next(s for s in r["steps"] if not s["ok"])
        return {
            "title": f"Dashboard changed: re-check steps in {pages[0]}",
            "change_type": "docs_bug", "doc_category": "implementation_guide",
            "summary": f"The documented flow `{r['flow']}` ({r.get('goal') or 'dashboard procedure'}) "
                       f"no longer works in the staging dashboard. Step {bad['i']} failed.",
            "sources": [{"source_id": sid, "url": RUN_URL or r["file"], "note": "weekly UI drift run"}],
            "pages": [{"path": p, "action": "update", "doc_type": "guide",
                       "what": "Update the click-path and screenshots to match the current UI"} for p in pages],
            "facts": [{"fact": f"Step {bad['i']} `{json.dumps(bad['step'])}` fails: {bad['error']}",
                       "evidence": f"{evidence}, failure screenshot {bad.get('failure_screenshot')}"}],
            "use_case": {"persona": "same as the current page", "scenario": "keep the page's existing example"},
            "test_plan": [f"Run flow {r['flow']} in capture mode; every step passes"],
            "open_questions": ["What changed in the dashboard here (renamed, moved, removed)? "
                               "Confirm the new path so the flow and doc steps can be updated."],
            "confidence": 0.5, "flow": r["flow"], "source_id": sid,
        }
    stale = [s for s in r["screenshots"] if s["status"] in ("stale", "missing")]
    if not stale:
        return None
    return {
        "title": f"Refresh screenshots in {pages[0]}",
        "change_type": "docs_bug", "doc_category": "screenshot_refresh",
        "summary": f"The flow `{r['flow']}` still works, but {len(stale)} screenshot(s) no longer "
                   "match the dashboard.",
        "sources": [{"source_id": sid, "url": RUN_URL or r["file"], "note": "weekly UI drift run"}],
        "pages": [{"path": p, "action": "update", "doc_type": "guide",
                   "what": "Re-capture screenshots with the flow; check alt text and any step "
                           "wording that mentions what's on screen"} for p in pages],
        "facts": [{"fact": f"`{s['out']}` differs by {s.get('diff', 1):.0%} ({s['status']})",
                   "evidence": evidence} for s in stale],
        "use_case": {"persona": "same as the current page", "scenario": "keep the page's existing example"},
        "test_plan": [f"Run flow {r['flow']} in capture mode and commit the new images"],
        "open_questions": [], "confidence": 0.9, "flow": r["flow"], "source_id": sid,
    }


def main():
    path = RUN_DIR / "browser.json"
    if not path.exists():
        print("no browser.json: the flow runner didn't finish (login state expired?). Nothing filed.")
        return
    results = json.loads(path.read_text())
    min_conf = config()["planner"]["auto_ready_min_confidence"]
    ensure_labels()
    already = open_flow_briefs()
    for r in results:
        if r["flow"] in already:
            continue
        b = brief_for(r)
        if not b:
            continue
        ready = not b["open_questions"] and b["confidence"] >= min_conf   # respects shadow mode
        body = render(b) + f"\n<!-- ui-flow: {b['flow']} -->\n"
        url = gh("issue", "create", "--title", b["title"], "--body", body, "--label",
                 ",".join([L["brief"], L["ready"] if ready else L["needs_info"]])).strip()
        print(f"{'ready' if ready else 'needs info'}: {url}")


if __name__ == "__main__":
    main()
