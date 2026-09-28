"""Collect commits pushed to main in watched code repos.

Two modes:
  * dispatch  – SOURCE_REPO, BEFORE, AFTER env vars come from the code repo's
                notify-docs workflow (repository_dispatch). Exact push range.
  * sweep     – no env vars: look back `slack.lookback_hours` on every watched
                repo. Safety net for missed dispatches; dedupe keeps it cheap.

Output: run/signals-commits.json — one signal per push/range, with commit
messages, linked PR titles/bodies and a truncated diff limited to watch_paths.
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import os

from common import config, gh, known_source_ids, write_signals

CFG = config()
REPOS = {r["repo"]: r for r in CFG["code_repos"]}
FILTERS = CFG.get("commit_filters", {})
SKIP = [m.lower() for m in FILTERS.get("skip_markers", [])]
IGNORE = FILTERS.get("ignore_paths", [])
MAX_DIFF = int(FILTERS.get("max_diff_chars", 60000))


def _match(path: str, p: str) -> bool:
    if p.endswith("/"):
        return path.startswith(p) or f"/{p}" in f"/{path}"
    return fnmatch.fnmatch(path, p) or fnmatch.fnmatch(os.path.basename(path), p)


def watched(path: str, patterns: list[str]) -> bool:
    if any(_match(path, p) for p in IGNORE):
        return False
    for p in patterns:
        if p == "*":
            return True
        if p.endswith("/") and path.startswith(p):
            return True
        if fnmatch.fnmatch(path, p) or fnmatch.fnmatch(os.path.basename(path), p):
            return True
    return False


def pr_for_commit(repo: str, sha: str) -> dict | None:
    try:
        prs = json.loads(gh("api", f"repos/{repo}/commits/{sha}/pulls"))
    except Exception:
        return None
    if not prs:
        return None
    p = prs[0]
    return {"number": p["number"], "title": p["title"], "url": p["html_url"],
            "body": (p.get("body") or "")[:4000],
            "labels": [l["name"] for l in p.get("labels", [])]}


def build_signal(repo: str, commits: list[dict], files: list[dict],
                 before: str, after: str) -> dict | None:
    meta = REPOS.get(repo, {"watch_paths": ["*"], "area": repo})
    def skipped(msg: str) -> bool:
        first = msg.strip().splitlines()[0].lower() if msg.strip() else ""
        # "[skip docs]"-style markers count anywhere; prefixes like "ci:" only at the
        # start of the subject, so a squash-merge listing "* ci: fix lint" isn't dropped.
        return any((m in msg.lower()) if m.startswith("[") else first.startswith(m) for m in SKIP)
    commits = [c for c in commits if not skipped(c["commit"]["message"])]
    files = [f for f in files if watched(f["filename"], meta.get("watch_paths", ["*"]))]
    if not commits or not files:
        return None

    diff, used = [], 0
    for f in files:
        patch = f.get("patch") or ""
        chunk = f"--- {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})\n{patch}\n"
        if used + len(chunk) > MAX_DIFF:
            diff.append(f"--- {f['filename']} (diff truncated)\n")
            continue
        diff.append(chunk)
        used += len(chunk)

    prs, seen = [], set()
    for c in commits:
        pr = pr_for_commit(repo, c["sha"])
        if pr and pr["number"] not in seen:
            seen.add(pr["number"])
            prs.append(pr)

    return {
        "source_id": f"commit:{repo}@{after[:12]}",
        "type": "commit",
        "repo": repo,
        "area": meta.get("area"),
        "range": f"{before[:12]}...{after[:12]}",
        "url": f"https://github.com/{repo}/compare/{before}...{after}",
        "commits": [{"sha": c["sha"][:12], "author": c["commit"]["author"]["name"],
                     "message": c["commit"]["message"][:2000]} for c in commits],
        "pull_requests": prs,
        "files": [f["filename"] for f in files],
        "diff": "".join(diff),
    }


def compare(repo: str, before: str, after: str) -> dict | None:
    data = json.loads(gh("api", f"repos/{repo}/compare/{before}...{after}"))
    return build_signal(repo, data.get("commits", []), data.get("files", []), before, after)


def sweep(hours: int) -> list[dict]:
    since = (dt.datetime.utcnow() - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for repo in REPOS:
        try:
            commits = json.loads(gh("api", f"repos/{repo}/commits?since={since}&per_page=100"))  # default branch
        except Exception as e:
            print(f"warn: {repo}: {e}")
            continue
        if not commits:
            continue
        after = commits[0]["sha"]
        parent = commits[-1]["parents"][0]["sha"] if commits[-1]["parents"] else after
        sig = compare(repo, parent, after)
        if sig:
            out.append(sig)
    return out


def main():
    repo, before, after = (os.environ.get(k) for k in ("SOURCE_REPO", "BEFORE", "AFTER"))
    if repo and before and after:
        if set(before) == {"0"}:            # branch creation push
            before = f"{after}~1"
        sig = compare(repo, before, after)
        signals = [sig] if sig else []
    else:
        signals = sweep(int(FILTERS.get("sweep_lookback_hours", 26)))

    known = known_source_ids()
    signals = [s for s in signals if s["source_id"] not in known]
    write_signals("commits", signals)


if __name__ == "__main__":
    main()
