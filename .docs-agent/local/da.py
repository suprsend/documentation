#!/usr/bin/env python3
"""da: run the SuprSend docs agents on your laptop, then push one finished PR.

Everything the GitHub Actions pipeline does, run locally with Claude Code:

  da setup                     install the local tools (once)
  da doctor                    check tools, logins and secrets

  da plan                      look for new commits / Slack threads / emails → local briefs
  da brief new "request"       turn your own idea ("the batch page is confusing") into a brief
  da briefs | da show b003     list / read briefs
  da write b003                executor writes the brief on a new branch, then reviews it

  (or just edit docs yourself on any branch)

  da review                    test the current branch: samples on staging, browser, render,
                               Vale, links, facts. Auto-fixes agent commits up to 2 rounds
  da revise "make the example use Slack"    ask the executor for a change (logged for learning)
  da learn                     learner studies your edits/requests → skill edits (uncommitted)
  da skills-pr                 your skill edits → their own skill-update PR from main
  da sync [--apply]            what's newer on main / merge it in
  da ship                      learn + push + open the PR (+ Slack post)

  da ui-check                  run every dashboard flow (UI drift)
  da postman [--publish]       update / publish the Postman collection
  da weekly                    learner consolidation + autonomy report (skills branch)
  da status                    where am I: branch, brief, last review
  da schedule                  print a cron line to run `da plan` automatically

Secrets come from .docs-agent/local/.env (copy env.example). Claude Code must be installed
and logged in (`claude` on your PATH); GitHub access uses your `gh` login.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT = HERE.parent
ROOT = AGENT.parent
SCRIPTS = AGENT / "scripts"
RUN = AGENT / "run"
STATE = HERE / "state"
BRIEFS = STATE / "briefs"
REVIEWS = STATE / "reviews"
FEEDBACK = STATE / "feedback"
METRICS = STATE / "metrics"
TRAILER = "Docs-Agent: true"

# Tools each agent may use locally. Nobody but `da ship` pushes or opens PRs.
PLANNER_TOOLS = ("Read,Write,Glob,Grep,Bash(git clone --depth 50 https://github.com/suprsend/:*),"
                 "Bash(git -C /tmp/src/:*),Bash(grep:*),Bash(ls:*)")
EXEC_TOOLS = ("Read,Write,Edit,Glob,Grep,Bash(git add:*),Bash(git commit:*),Bash(git status:*),"
              "Bash(git diff:*),Bash(git log:*),Bash(git clone --depth 50 https://github.com/suprsend/:*),"
              "Bash(npx mintlify:*),Bash(vale:*),Bash(node .docs-agent/browser/run_flow.mjs:*),"
              "Bash(grep:*),Bash(ls:*),Bash(find:*)")
REVIEW_TOOLS = ("Read,Write,Glob,Grep,Bash(curl:*),Bash(node:*),Bash(python3:*),"
                "Bash(git clone --depth 50 https://github.com/suprsend/:*),Bash(git diff:*),"
                "Bash(git log:*),Bash(git show:*),Bash(grep:*),Bash(ls:*),Bash(cat:*)")
LEARN_TOOLS = ("Read,Write,Edit,Glob,Grep,Bash(git add:*),Bash(git commit:*),Bash(git diff:*),"
               "Bash(git log:*),Bash(python3:*),Bash(grep:*),Bash(ls:*)")
POSTMAN_TOOLS = ("Read,Write,Edit,Glob,Grep,Bash(git add:*),Bash(git commit:*),Bash(git diff:*),"
                 "Bash(git status:*),Bash(git clone --depth 50 https://github.com/suprsend/:*),"
                 "Bash(npx --yes newman run:*),Bash(grep:*),Bash(ls:*)")

LOCAL_RULES = (
    "LOCAL MODE: you are running on the docs owner's laptop, not in GitHub Actions. "
    "There are no GitHub issues or PRs for this step: inputs and outputs are files, as stated. "
    "Never run git push, gh, or post anywhere. Commit only when told to."
)


# ---------------------------------------------------------------- helpers

def say(msg: str):
    print(f"\033[1m» {msg}\033[0m", flush=True)


def die(msg: str, code: int = 1):
    print(f"\033[31m✗ {msg}\033[0m", file=sys.stderr)
    sys.exit(code)


def load_env():
    env_file = HERE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if v.startswith("@"):                       # KEY=@path/to/file → file contents
                p = Path(v[1:]).expanduser()
                v = p.read_text().strip() if p.exists() else ""
            os.environ.setdefault(k.strip(), v)
    os.environ["DOCS_AGENT_MODE"] = "local"
    sys.path.insert(0, str(SCRIPTS))


def run(cmd: list[str] | str, check: bool = True, capture: bool = False, cwd: Path = ROOT,
        env: dict | None = None) -> subprocess.CompletedProcess:
    shell = isinstance(cmd, str)
    p = subprocess.run(cmd, shell=shell, cwd=cwd, text=True, env={**os.environ, **(env or {})},
                       capture_output=capture)
    if check and p.returncode != 0:
        if capture:
            sys.stderr.write((p.stdout or "") + (p.stderr or ""))
        die(f"command failed ({p.returncode}): {cmd if shell else ' '.join(cmd)}")
    return p


def out(cmd: list[str], cwd: Path = ROOT) -> str:
    return run(cmd, capture=True, cwd=cwd).stdout.strip()


def git(*args: str) -> str:
    return out(["git", *args])


def cfg() -> dict:
    import yaml
    return yaml.safe_load((AGENT / "config.yml").read_text())


def branch() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD")


def base_ref(args) -> str:
    base = getattr(args, "base", None) or f"origin/{cfg()['docs']['base_branch']}"
    run(["git", "fetch", "-q", "origin", base.split("/", 1)[-1]], check=False)
    return base


def slug(text: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:n].strip("-") or "change"


def claude(prompt: str, tools: str, max_turns: int = 60, system: str = LOCAL_RULES) -> int:
    if not shutil.which("claude"):
        die("Claude Code isn't installed or not on PATH. Install: npm i -g @anthropic-ai/claude-code, then run `claude` once to log in.")
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--allowedTools", tools,
           "--max-turns", str(max_turns), "--append-system-prompt", system]
    if os.environ.get("DOCS_AGENT_MODEL"):
        cmd += ["--model", os.environ["DOCS_AGENT_MODEL"]]
    return subprocess.run(cmd, cwd=ROOT).returncode


def changed_pages(base: str) -> list[str]:
    names = git("diff", "--name-only", "--diff-filter=AM", f"{base}...HEAD", "--", "*.mdx", "*.md").split()
    return [n for n in names if not n.startswith(".")]


def agent_commits(base: str) -> list[dict]:
    log = git("log", "--no-merges", "--format=%H%x1f%an%x1f%s%x1f%b%x1e", f"{base}..HEAD")
    commits = []
    for rec in filter(None, (r.strip() for r in log.split("\x1e"))):
        sha, author, subject, body = (rec.split("\x1f") + ["", "", "", ""])[:4]
        commits.append({"sha": sha, "author": author, "subject": subject,
                        "agent": TRAILER in body or TRAILER in subject})
    return list(reversed(commits))          # oldest first


def dirty() -> bool:
    return bool(git("status", "--porcelain", "--untracked-files=no"))


# ---------------------------------------------------------------- briefs

def brief_path(bid: str, ext: str = "json") -> Path:
    return BRIEFS / f"{bid}.{ext}"


def load_brief(bid: str) -> dict:
    p = brief_path(bid)
    if not p.exists():
        die(f"no brief {bid}. `da briefs` lists them.")
    return json.loads(p.read_text())


def save_brief(b: dict):
    from create_briefs import render
    BRIEFS.mkdir(parents=True, exist_ok=True)
    brief_path(b["id"]).write_text(json.dumps(b, indent=2, ensure_ascii=False))
    header = f"<!-- {b['id']} · status: {b['status']} · branch: {b.get('branch') or '-'} -->\n# {b['title']}\n\n"
    brief_path(b["id"], "md").write_text(header + render(b))


def next_id() -> str:
    BRIEFS.mkdir(parents=True, exist_ok=True)
    nums = [int(p.stem[1:]) for p in BRIEFS.glob("b*.json") if p.stem[1:].isdigit()]
    return f"b{(max(nums) + 1) if nums else 1:03d}"


def brief_for_branch(br: str) -> dict | None:
    for p in BRIEFS.glob("b*.json"):
        b = json.loads(p.read_text())
        if b.get("branch") == br:
            return b
    return None


def _plan_problems(plan: dict) -> list[str]:
    """Required-field check (no jsonschema dependency): enough to keep render() safe."""
    schema = json.loads((ROOT / ".docs-agent/schemas/brief.schema.json").read_text())
    item = schema["properties"]["briefs"]["items"] if "briefs" in schema.get("properties", {}) else schema
    out = []
    for i, b in enumerate(plan.get("briefs", [])):
        out += [f"briefs[{i}] missing '{k}'" for k in item.get("required", []) if k not in b]
        for sub in ("pages", "sources"):
            req = item["properties"].get(sub, {}).get("items", {}).get("required", [])
            for j, x in enumerate(b.get(sub, []) or []):
                out += [f"briefs[{i}].{sub}[{j}] missing '{k}'" for k in req if k not in x]
    return out


def store_plan(origin: str) -> list[dict]:
    """run/briefs.json (planner output) → local briefs + ledger."""
    from common import remember_sources
    path = RUN / "briefs.json"
    if not path.exists():
        say("planner wrote no briefs.json")
        return []
    try:
        plan = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        die(f"run/briefs.json is not valid JSON ({e}). Ask the planner to fix it.")
    problems = _plan_problems(plan)
    if problems:
        die("run/briefs.json doesn't match .docs-agent/schemas/brief.schema.json:\n  - "
            + "\n  - ".join(problems) + "\nAsk the planner to fix these and run save-plan again.")
    c = cfg()
    created, ledger = [], {}
    for b in plan.get("briefs", [])[: c["planner"]["max_briefs_per_run"]]:
        b["id"] = next_id()
        b["origin"] = origin
        b["created"] = dt.datetime.now().isoformat(timespec="minutes")
        # Locally you are the approver: a brief is ready unless it has open questions.
        b["status"] = "needs-info" if b.get("open_questions") else "ready"
        b.setdefault("branch", None)
        save_brief(b)
        created.append(b)
        for s in b.get("sources", []):
            ledger[s["source_id"]] = f"brief {b['id']}"
    for s in plan.get("skipped", []):
        ledger[s["source_id"]] = f"skipped: {s.get('reason', '')}"
    for m in plan.get("merged_into_existing", []):
        target = m.get("brief") or m.get("issue")
        ledger[m["source_id"]] = f"merged into {target}"
        if isinstance(target, str) and brief_path(target).exists():
            b = load_brief(target)
            b.setdefault("related", []).append({"source_id": m["source_id"], "note": m.get("note", "")})
            save_brief(b)
    remember_sources(ledger)
    return created


def print_briefs(briefs: list[dict]):
    if not briefs:
        print("  (none)")
    for b in briefs:
        print(f"  {b['id']}  {b['status']:<11} {b.get('doc_category', ''):<20} {b['title']}")


# ---------------------------------------------------------------- commands

def cmd_setup(args):
    say("Python deps"); run([sys.executable, "-m", "pip", "install", "--quiet", "pyyaml", "vale",
                             "-r", str(AGENT / "tester" / "requirements.txt")])
    say("Docs tooling (repo package.json: Mintlify CLI)"); run(["npm", "ci", "--silent", "--no-audit", "--no-fund"])
    say("Vale styles"); run(["vale", "sync"], check=False)
    say("SDKs for sample runs"); run(["npm", "install", "--silent"], cwd=AGENT / "tester")
    say("Browser (Playwright + Chromium)"); run(["npm", "install", "--silent"], cwd=AGENT / "browser")
    run(["npx", "playwright", "install", "chromium"], cwd=AGENT / "browser")
    if not (HERE / ".env").exists():
        shutil.copy(HERE / "env.example", HERE / ".env")
        say(f"Created {HERE / '.env'}; fill in your keys.")
    say("Done. Next: `da doctor`.")


def cmd_doctor(args):
    ok = True
    def check(label, good, hint=""):
        nonlocal ok
        ok &= bool(good)
        print(f"  {'✓' if good else '✗'} {label}" + ("" if good else f"  → {hint}"))
    check("claude (Claude Code CLI)", shutil.which("claude"), "npm i -g @anthropic-ai/claude-code; run `claude` once to log in")
    check("gh logged in", run(["gh", "auth", "status"], check=False, capture=True).returncode == 0, "gh auth login")
    check("node", shutil.which("node"), "install Node 20+")
    check("vale", shutil.which("vale"), "da setup")
    check("browser deps", (AGENT / "browser" / "node_modules").exists(), "da setup")
    check("Mintlify CLI", (ROOT / "node_modules" / ".bin" / "mintlify").exists(), "da setup")
    check(".env present", (HERE / ".env").exists(), "cp .docs-agent/local/env.example .docs-agent/local/.env")
    for key, need in [("SLACK_INTERNAL_BOT_TOKEN", "Slack signals + PR posts"),
                      ("SLACK_COMMUNITY_BOT_TOKEN", "community Slack signals"),
                      ("SUPRSEND_STAGING_API_KEY", "running REST samples"),
                      ("SUPRSEND_STAGING_WORKSPACE_KEY", "running SDK samples"),
                      ("SUPRSEND_STAGING_WORKSPACE_SECRET", "running SDK samples"),
                      ("SUPRSEND_STAGING_SERVICE_TOKEN", "management API samples"),
                      ("DASHBOARD_STORAGE_STATE", "browser flows / screenshots"),
                      ("POSTMAN_API_KEY", "da postman"),
                      ("GMAIL_REFRESH_TOKEN", "support email (optional)")]:
        print(f"  {'✓' if os.environ.get(key) else '·'} {key}" + ("" if os.environ.get(key) else f"  (needed for {need})"))
    print("\nAll required checks passed." if ok else "\nFix the ✗ items above.")


def cmd_plan(args):
    RUN.mkdir(parents=True, exist_ok=True)
    for f in RUN.glob("signals-*.json"):
        f.unlink()
    (RUN / "briefs.json").unlink(missing_ok=True)
    say("Collecting commits from watched repos")
    run([sys.executable, str(SCRIPTS / "collect_commits.py")], check=False)
    if not args.no_slack and (os.environ.get("SLACK_INTERNAL_BOT_TOKEN") or os.environ.get("SLACK_COMMUNITY_BOT_TOKEN")):
        say("Collecting Slack threads"); run([sys.executable, str(SCRIPTS / "collect_slack.py")], check=False)
    if os.environ.get("GMAIL_REFRESH_TOKEN"):
        say("Collecting support email"); run([sys.executable, str(SCRIPTS / "collect_gmail.py")], check=False)
    n = sum(len(json.loads(f.read_text())) for f in RUN.glob("signals-*.json"))
    if not n:
        say("Nothing new since last time."); return
    say(f"{n} new signal(s). Planning")
    claude(
        "You are the docs planner. Read and follow .claude/skills/docs-planner/SKILL.md.\n"
        "New signals: .docs-agent/run/signals-*.json.\n"
        "Open briefs are local files, not GitHub issues: .docs-agent/local/state/briefs/*.json "
        "(status not 'shipped'/'dropped'). To merge a signal into one, put its id in "
        "merged_into_existing[].brief (e.g. \"b004\") instead of issue.\n"
        "Write .docs-agent/run/briefs.json (schema .docs-agent/schemas/brief.schema.json).",
        PLANNER_TOOLS, 60)
    created = store_plan("plan")
    if created and not args.no_slack:
        _reply_sources(created)
    if not args.no_mark_seen and os.environ.get("GMAIL_REFRESH_TOKEN"):
        run([sys.executable, str(SCRIPTS / "collect_gmail.py"), "--mark-seen"], check=False)
    say(f"{len(created)} new brief(s):"); print_briefs(created)
    if created:
        print("\nRead one: da show <id>   Write it: da write <id>")


def _reply_sources(created: list[dict]):
    try:
        from notify_slack import reply_to_source
        sigs = {}
        for f in RUN.glob("signals-*.json"):
            for s in json.loads(f.read_text()):
                sigs[s["source_id"]] = s
        for b in created:
            for s in b.get("sources", []):
                if s["source_id"] in sigs:
                    reply_to_source(sigs[s["source_id"]], f"Thanks, this is now a docs brief: {b['title']}")
    except Exception as e:
        print(f"(slack reply skipped: {e})")


def cmd_brief(args):
    if args.action == "new":
        text = " ".join(args.text).strip() or die("say what you want changed, e.g. da brief new \"the batch page doesn't explain retries\"")
        pages = args.page or []
        if args.no_plan:
            b = {"id": next_id(), "origin": "manual", "status": "ready", "title": text[:90],
                 "change_type": "clarification", "doc_category": args.category or "clarification",
                 "summary": text, "sources": [{"source_id": f"manual:{int(time.time())}", "url": "local"}],
                 "pages": [{"path": p, "action": "update", "doc_type": "guide", "what": text} for p in pages],
                 "facts": [], "use_case": {"persona": "pick from .docs-agent/context/customers.md", "scenario": ""},
                 "test_plan": [], "open_questions": [], "confidence": 1.0, "branch": None,
                 "created": dt.datetime.now().isoformat(timespec="minutes")}
            save_brief(b); say(f"brief {b['id']} created (no planning)"); return
        RUN.mkdir(parents=True, exist_ok=True)
        for f in RUN.glob("signals-*.json"):
            f.unlink()
        who = run(["git", "config", "user.name"], check=False, capture=True).stdout.strip()
        (RUN / "signals-manual.json").write_text(json.dumps([{
            "source_id": f"manual:{int(time.time())}", "type": "manual_request", "url": "local",
            "requested_by": who, "request": text, "pages": pages}], indent=2))
        say("Planning your request")
        claude(
            "You are the docs planner. Read and follow .claude/skills/docs-planner/SKILL.md.\n"
            "The only signal is a MANUAL REQUEST from the docs owner in .docs-agent/run/signals-manual.json. "
            "It may be about improving existing docs rather than a product change. It always needs docs: "
            "never skip it. Its text is authoritative for intent; you still verify every fact you list, "
            "find every page it affects (start from the pages given, if any), and pick the persona and example.\n"
            "Write .docs-agent/run/briefs.json (schema .docs-agent/schemas/brief.schema.json).",
            PLANNER_TOOLS, 50)
        created = store_plan("manual")
        say("Brief:"); print_briefs(created)
        if created:
            print(f"\nRead it: da show {created[0]['id']}   Write it: da write {created[0]['id']}")
    elif args.action == "drop":
        b = load_brief(args.text[0]); b["status"] = "dropped"; save_brief(b); say(f"{b['id']} dropped")
    elif args.action == "ready":
        b = load_brief(args.text[0]); b["status"] = "ready"; save_brief(b); say(f"{b['id']} marked ready")


def cmd_briefs(args):
    items = sorted((json.loads(p.read_text()) for p in BRIEFS.glob("b*.json")), key=lambda b: b["id"])
    if not args.all:
        items = [b for b in items if b["status"] not in ("shipped", "dropped")]
    print_briefs(items)


def cmd_show(args):
    p = brief_path(args.id, "md")
    print(p.read_text() if p.exists() else f"no brief {args.id}")


def cmd_write(args):
    b = load_brief(args.id)
    if b["status"] == "needs-info" and not args.force:
        die(f"{b['id']} has open questions. Answer them in {brief_path(b['id'], 'md')} "
            f"(edit the file) and run `da brief ready {b['id']}`, or pass --force.")
    if not args.here:
        if dirty():
            die("you have uncommitted changes. Commit or stash them, or use --here to work on this branch.")
        base = base_ref(args)
        br = b.get("branch") or f"docs/{b['id']}-{slug(b['title'])}"
        exists = run(["git", "rev-parse", "--verify", "--quiet", br], check=False, capture=True).returncode == 0
        run(["git", "checkout", "-q", br] if exists else ["git", "checkout", "-q", "-b", br, base])
    b["branch"] = branch(); b["status"] = "writing"; save_brief(b)
    say(f"Executor writing {b['id']} on {b['branch']}")
    rc = claude(
        "You are the docs executor. Read and follow .claude/skills/docs-executor/SKILL.md, Mode A, "
        "with these local changes:\n"
        f"- The brief is the file .docs-agent/local/state/briefs/{b['id']}.md (not a GitHub issue). "
        "Answers the owner wrote into that file override the brief.\n"
        "- You are already on the right branch. Skip the branch, push and PR steps.\n"
        f"- Commit with the trailer lines 'Docs-Agent: true' and 'Refs: {b['id']}'.\n"
        "- Load .claude/skills/suprsend-docs-writer/SKILL.md and the lane skill for each page "
        "(docs-reference-writer / docs-guide-writer), and docs-ui-flows if there are dashboard steps.\n"
        "- When done, write .docs-agent/run/executor-summary.md: what changed, the example used, "
        "and where you were unsure.",
        EXEC_TOOLS, 80)
    b["status"] = "written" if rc == 0 else "writing"; save_brief(b)
    if rc != 0:
        die("executor stopped with an error; see output above. Re-run `da write` to continue.")
    if (RUN / "executor-summary.md").exists():
        print((RUN / "executor-summary.md").read_text())
    if not args.no_review:
        cmd_review(argparse.Namespace(base=getattr(args, "base", None), no_autofix=False, skip=""))


# ---------- review

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_checks(base: str, skip: set[str]):
    RUN.mkdir(parents=True, exist_ok=True)
    for f in ["snippets.json", "browser.json", "browser-changed-flows.json", "render.json",
              "vale.json", "broken-links.txt", "review.json", "review.md"]:
        (RUN / f).unlink(missing_ok=True)
    pages = changed_pages(base)
    mdx = [p for p in pages if p.endswith(".mdx")]
    if "vale" not in skip and mdx and shutil.which("vale"):
        say("Vale")
        p = run(["vale", "--output=JSON", *mdx], check=False, capture=True)
        (RUN / "vale.json").write_text(p.stdout or "{}")
    if "links" not in skip:
        say("Link check")
        p = run(["npx", "mintlify", "broken-links"], check=False, capture=True)
        (RUN / "broken-links.txt").write_text((p.stdout or "") + (p.stderr or ""))
    if "samples" not in skip:
        say("Running code samples against staging")
        run([sys.executable, str(SCRIPTS / "run_snippets.py"), "--base", base], check=False)
    if "browser" not in skip and (AGENT / "browser" / "node_modules").exists():
        flows = [f for f in git("diff", "--name-only", "--diff-filter=AM", f"{base}...HEAD", "--",
                                ".docs-agent/flows").split() if f.endswith((".yml", ".yaml"))]
        if flows:
            say("Dashboard flows changed on this branch")
            run(["node", ".docs-agent/browser/run_flow.mjs", "--mode", "verify", *flows], check=False)
            if (RUN / "browser.json").exists():
                (RUN / "browser.json").rename(RUN / "browser-changed-flows.json")
        if pages:
            say("Dashboard flows for changed pages")
            run(["node", ".docs-agent/browser/run_flow.mjs", "--mode", "verify", "--page", *pages], check=False)
    if "render" not in skip and (AGENT / "browser" / "node_modules").exists():
        spec_pages = run([sys.executable, str(SCRIPTS / "openapi_pages.py"), base], check=False,
                         capture=True).stdout.split()
        targets = sorted(set(pages + spec_pages))
        if targets:
            port = _free_port()
            say(f"Rendering {len(targets)} page(s) in a local Mintlify preview (port {port})")
            log = open(RUN / "mint-dev.log", "w")
            dev = subprocess.Popen(["npx", "mintlify", "dev", "--port", str(port)], cwd=ROOT,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                for _ in range(90):
                    if run(["curl", "-sf", f"http://localhost:{port}"], check=False, capture=True).returncode == 0:
                        break
                    time.sleep(2)
                run(["node", ".docs-agent/browser/render_check.mjs", "--base", f"http://localhost:{port}", *targets],
                    check=False)
            finally:
                os.killpg(dev.pid, signal.SIGTERM)


def review_once(base: str, b: dict | None, round_no: int) -> dict:
    brief_line = (f"The brief is .docs-agent/local/state/briefs/{b['id']}.md." if b else
                  "There is no brief: this is the owner's own change. Judge it on the diff, the facts "
                  "(check them against source code) and the docs-writer rules.")
    claude(
        "You are the docs reviewer and tester. Read and follow .claude/skills/docs-reviewer/SKILL.md, "
        "with these local changes:\n"
        f"- There is no PR. The change is `git diff {base}...HEAD` on the current branch. {brief_line}\n"
        "- Check results: .docs-agent/run/snippets.json, vale.json, broken-links.txt, browser.json, "
        "browser-changed-flows.json, render.json; screenshots under .docs-agent/run/browser/ and "
        ".docs-agent/run/render/ (open them with Read). Staging API base: $SUPRSEND_API_BASE.\n"
        "- Write .docs-agent/run/review.json, and write the comment you would have posted to "
        ".docs-agent/run/review.md instead of posting it.",
        REVIEW_TOOLS, 60)
    review = json.loads((RUN / "review.json").read_text()) if (RUN / "review.json").exists() else \
        {"verdict": "needs_human", "summary": "reviewer produced no review.json"}
    dest = REVIEWS / slug(branch(), 80) / f"round-{round_no}"
    dest.mkdir(parents=True, exist_ok=True)
    for f in ["review.json", "review.md", "snippets.json", "browser.json", "render.json", "vale.json"]:
        if (RUN / f).exists():
            shutil.copy(RUN / f, dest / f)
    return review


def cmd_review(args):
    os.environ.setdefault("SUPRSEND_API_BASE", cfg()["reviewer"]["staging"]["api_base"])
    base = base_ref(args)
    if dirty():
        die("commit your changes first; the review tests committed work (git add -A && git commit).")
    if not git("log", "--oneline", f"{base}..HEAD"):
        die(f"no commits on this branch compared with {base}.")
    b = brief_for_branch(branch())
    skip = set(filter(None, (args.skip or "").split(",")))
    max_rounds = cfg()["reviewer"]["max_rounds"]
    round_no = len(list((REVIEWS / slug(branch(), 80)).glob("round-*"))) + 1 if (REVIEWS / slug(branch(), 80)).exists() else 1
    while True:
        run_checks(base, skip)
        say(f"Reviewer (round {round_no})")
        review = review_once(base, b, round_no)
        print("\n" + ((RUN / "review.md").read_text() if (RUN / "review.md").exists() else json.dumps(review, indent=2)))
        verdict = review.get("verdict")
        say(f"verdict: {verdict}")
        commits = agent_commits(base)
        last_is_agent = bool(commits) and commits[-1]["agent"]
        if verdict != "fix" or args.no_autofix or not last_is_agent or round_no > max_rounds:
            if verdict == "fix" and not last_is_agent:
                print("Your own commit is last, so no auto-fix: apply the findings yourself, or `da revise \"…\"`.")
            elif verdict == "pass":
                print("Ready. Ship it with: da ship")
            break
        say("Executor fixing the findings")
        _executor_revise(".docs-agent/run/review.md has the reviewer's findings. Fix every Blocker and Should-fix.")
        round_no += 1


def _executor_revise(instruction: str):
    claude(
        "You are the docs executor. Read and follow .claude/skills/docs-executor/SKILL.md, Mode B, with "
        "these local changes: there is no PR; the change is the current branch. Instruction:\n"
        f"{instruction}\n"
        "Commit with the trailer 'Docs-Agent: true'. Don't push. Then write what you changed (and what "
        "you didn't and why) to .docs-agent/run/executor-summary.md.",
        EXEC_TOOLS, 60)
    if (RUN / "executor-summary.md").exists():
        print((RUN / "executor-summary.md").read_text())


def cmd_revise(args):
    text = " ".join(args.text).strip() or die('say what to change, e.g. da revise "use the Routewise example"')
    if dirty():
        die("commit your own edits first so the learner can tell them apart from the agent's.")
    FEEDBACK.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK / f"{slug(branch(), 80)}.jsonl", "a") as f:
        f.write(json.dumps({"type": "request", "text": text, "at": dt.datetime.now().isoformat(timespec="seconds")}) + "\n")
    say("Executor applying your request")
    _executor_revise(f"The docs owner asked: \"{text}\". Do exactly that.")
    if not args.no_review:
        cmd_review(argparse.Namespace(base=getattr(args, "base", None), no_autofix=True, skip=args.skip or ""))


# ---------- learn

def build_feedback(base: str) -> tuple[dict, dict]:
    br = branch()
    commits = agent_commits(base)
    b = brief_for_branch(br)
    human = [c for c in commits if not c["agent"]]
    human_diff = ""
    for c in human:
        human_diff += f"### commit {c['sha'][:10]} by {c['author']}: {c['subject']}\n"
        human_diff += out(["git", "show", "--format=", "--stat", "--patch", c["sha"]])[:20000] + "\n"
    added = deleted = 0
    for line in git("diff", "--numstat", f"{base}...HEAD").splitlines():
        a, d, *_ = line.split("\t")
        if a.isdigit() and d.isdigit():
            added += int(a); deleted += int(d)
    human_lines = 0
    for c in human:
        for line in out(["git", "show", "--numstat", "--format=", c["sha"]]).splitlines():
            a, d, *_ = line.split("\t")
            if a.isdigit() and d.isdigit():
                human_lines += int(a) + int(d)
    reqs = []
    fb = FEEDBACK / f"{slug(br, 80)}.jsonl"
    if fb.exists():
        reqs = [json.loads(l) for l in fb.read_text().splitlines() if l.strip()]
    rounds = sorted((REVIEWS / slug(br, 80)).glob("round-*")) if (REVIEWS / slug(br, 80)).exists() else []
    last_review = (rounds[-1] / "review.md").read_text()[:6000] if rounds and (rounds[-1] / "review.md").exists() else None
    written_by_human = not any(c["agent"] for c in commits)
    feedback = {
        "branch": br, "local": True,
        "written_by_human": written_by_human,
        "human_diff_full": out(["git", "diff", f"{base}...HEAD"])[:80000] if written_by_human else None,
        "brief": {"id": b["id"], "title": b["title"], "json": b} if b else None,
        "human_edit_diff": human_diff[:60000],
        "change_requests": [{"who": "owner", "text": r["text"], "at": r["at"]} for r in reqs if r["type"] == "request"],
        "review_comments": [], "review_verdicts": [],
        "agent_review_rounds": len(rounds),
        "agent_review_last": last_review,
    }
    metrics = {"branch": br, "date": dt.date.today().isoformat(),
               "category": "local" if written_by_human else ((b or {}).get("doc_category") or "unknown"),
               "merged": True, "human_commits": len(human),
               "human_edit_ratio": round(human_lines / max(added + deleted, 1), 3),
               "change_requests": len(feedback["change_requests"]), "review_comments": 0,
               "agent_review_rounds": len(rounds), "hours_to_close": 0}
    return feedback, metrics


def cmd_learn(args):
    base = base_ref(args)
    if dirty():
        die("commit your edits first; the learner learns from commits.")
    feedback, metrics = build_feedback(base)
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "feedback.json").write_text(json.dumps(feedback, indent=2, ensure_ascii=False))
    (RUN / "metrics-line.json").write_text(json.dumps(metrics))
    METRICS.mkdir(parents=True, exist_ok=True)
    (METRICS / f"{slug(branch(), 80)}.json").write_text(json.dumps(metrics, indent=2))
    if not feedback["human_edit_diff"] and not feedback["change_requests"] and not feedback["written_by_human"]:
        say("No human edits or requests on this branch: nothing to learn."); return
    say("Learner studying your edits and requests")
    claude(
        "You are the docs learner. Read and follow .claude/skills/docs-learner/SKILL.md, Mode A, with "
        "these local changes: feedback is .docs-agent/run/feedback.json (from the current branch, not a "
        "closed PR); metrics are already saved. Make your skill edits in .claude/skills/ and "
        ".docs-agent/context/ directly and DON'T commit them: `da skills-pr` turns them into their own "
        "skill-update PR so the docs PR stays docs-only. "
        "Finally write a short summary (rules added/changed, candidates, ignored) to "
        ".docs-agent/run/learn-summary.md.",
        LEARN_TOOLS, 50)
    if (RUN / "learn-summary.md").exists():
        print((RUN / "learn-summary.md").read_text())
    say("Check the skill edits (git diff), then `da skills-pr` to open them as their own PR.")


# ---------- ship

def cmd_ship(args):
    c = cfg()
    base = base_ref(args)
    br = branch()
    if br in (c["docs"]["base_branch"], "master"):
        die("you're on the base branch. Ship from a feature branch.")
    if dirty():
        die("commit your changes first.")
    rounds = sorted((REVIEWS / slug(br, 80)).glob("round-*")) if (REVIEWS / slug(br, 80)).exists() else []
    last = json.loads((rounds[-1] / "review.json").read_text()) if rounds and (rounds[-1] / "review.json").exists() else None
    head_reviewed = bool(rounds) and rounds[-1].stat().st_mtime >= float(git("log", "-1", "--format=%ct"))
    if not args.force:
        if not last:
            die("not reviewed yet. Run `da review` (or pass --force).")
        if last.get("verdict") != "pass":
            die(f"last review verdict is '{last.get('verdict')}'. Fix it and `da review` again, or --force.")
        if not head_reviewed:
            die("you've committed since the last review. Run `da review` again, or --force.")
    touched = [f for f in git("diff", "--name-only", f"{base}...HEAD").splitlines() if _is_agent_file(f)]
    if touched:
        die("this branch changes agent files (skills/agents/.docs-agent), which go in their own PR:\n  "
            + "\n  ".join(touched[:15]) + "\nRun `da skills-pr` to move them there, then ship again.")
    if not args.no_learn:
        cmd_learn(args)
        if _agent_changes(base_ref(args))["local"]:
            cmd_skills_pr(argparse.Namespace(ours=False, title=f"skills: learned from {br}",
                                             body_file=str(RUN / "learn-summary.md"), keep=False))
    b = brief_for_branch(br)
    title = args.title or (b["title"] if b else git("log", "-1", "--format=%s", f"{base}..HEAD") or br)
    review_md = (rounds[-1] / "review.md").read_text() if rounds and (rounds[-1] / "review.md").exists() else "_Not reviewed._"
    closes = f"Closes #{b['github_issue']}\n\n" if b and b.get("github_issue") else ""
    body = (closes +
            (f"## Why\n{b['summary']}\n\n" if b else "") +
            "## What changed\n```\n" + git("diff", "--stat", f"{base}...HEAD") + "\n```\n\n"
            "## Local review (da review)\n" + review_md + "\n\n"
            f"_Written and tested locally with the docs agents. Brief: {b['id'] if b else 'none (manual change)'}._\n")
    say(f"Pushing {br}")
    run(["git", "push", "-q", "-u", "origin", "HEAD"])
    cmd = ["gh", "pr", "create", "--base", c["docs"]["base_branch"], "--title", title, "--body", body]
    for r in c["docs"].get("reviewers", []):
        if r and not r.startswith("TODO"):
            cmd += ["--reviewer", r]
    for lbl in (c.get("local", {}) or {}).get("pr_labels", []):
        cmd += ["--label", lbl]
    if args.draft:
        cmd.append("--draft")
    url = out(cmd)
    say(f"PR: {url}")
    if b:
        b["status"] = "shipped"; b["pr"] = url; save_brief(b)
    try:
        from notify_slack import announce
        announce(int(url.rstrip("/").split("/")[-1]), "tested")
    except Exception as e:
        print(f"(slack post skipped: {e})")


# ---------- ui-check / postman / schedule / status

def cmd_ui_check(args):
    run(["node", ".docs-agent/browser/run_flow.mjs", "--mode", "verify", "--all"], check=False)
    path = RUN / "browser.json"
    if not path.exists():
        die("no results (login state expired? check DASHBOARD_STORAGE_STATE)")
    results = json.loads(path.read_text())
    bad = [r for r in results if not r["ok"] or any(s["status"] in ("stale", "missing") for s in r["screenshots"])]
    say(f"{len(results)} flow(s), {len(bad)} need attention")
    if args.briefs and bad:
        from ui_drift import brief_for
        for r in bad:
            bb = brief_for(r)
            if bb:
                bb.update(id=next_id(), origin="ui-check", status="needs-info" if bb["open_questions"] else "ready",
                          branch=None, created=dt.datetime.now().isoformat(timespec="minutes"))
                save_brief(bb); print(f"  brief {bb['id']}: {bb['title']}")


def cmd_postman(args):
    if args.publish:
        run([sys.executable, str(SCRIPTS / "postman_sync.py"), "check"])
        run([sys.executable, str(SCRIPTS / "postman_sync.py"), "push"]); return
    if dirty():
        die("commit or stash your changes first.")
    base = base_ref(args)
    run(["git", "checkout", "-q", "-b", f"postman/{dt.date.today().isoformat()}-{int(time.time()) % 10000}", base])
    run([sys.executable, str(SCRIPTS / "postman_sync.py"), "pull"])
    run(["git", "add", "postman/"]); run(["git", "commit", "-qm", "postman: sync latest from the Postman app", "-m", TRAILER], check=False)
    envfile = STATE / "staging.env.json"; STATE.mkdir(parents=True, exist_ok=True)
    run([sys.executable, str(SCRIPTS / "postman_sync.py"), "env", str(envfile)])
    diff = run(["git", "diff", f"{base}", "--", "reference", "openapi.yaml"], check=False, capture=True).stdout
    (RUN / "api-changes.txt").write_text(diff[:80000] or "Drift check: compare the whole collection with the docs.")
    claude(
        "You are the Postman agent. Read and follow .claude/skills/docs-postman/SKILL.md.\n"
        f"Collection: postman/collection.json. What changed: .docs-agent/run/api-changes.txt. "
        f"Newman environment: {envfile} (never print or copy its values). Commit on the current branch; "
        "write .docs-agent/run/postman-summary.md.", POSTMAN_TOOLS, 60)
    run([sys.executable, str(SCRIPTS / "postman_sync.py"), "check"])
    say("Review the branch, then `da ship --force` (Postman changes have no docs review). After merge: da postman --publish")


def cmd_weekly(args):
    """Learner Mode B locally: consolidate learnings + autonomy report, on a skills branch."""
    if dirty():
        die("commit or stash your changes first.")
    base = base_ref(args)
    run(["git", "checkout", "-q", "-b", f"skills/weekly-{dt.date.today().isoformat()}", base])
    rep = run([sys.executable, str(SCRIPTS / "autonomy_report.py")], check=False, capture=True).stdout
    (RUN / "autonomy.md").write_text(rep)
    print(rep)
    claude(
        "You are the docs learner. Read and follow .claude/skills/docs-learner/SKILL.md, Mode B (weekly "
        "consolidation), locally: the autonomy table is in .docs-agent/run/autonomy.md. Commit skill edits "
        "on the current branch with the trailer 'Docs-Agent: true'. Write the digest to "
        ".docs-agent/run/digest.md. Don't open a PR.", LEARN_TOOLS, 50)
    if (RUN / "digest.md").exists():
        print((RUN / "digest.md").read_text())
    say("Review the branch; ship it with `da ship --force --no-learn` if there are skill changes.")


def cmd_schedule(args):
    da = HERE / "da"
    print("Add this with `crontab -e` to run the planner every 2 hours on weekdays (laptop must be awake):\n")
    print(f"17 9-19/2 * * 1-5 cd {ROOT} && {da} plan >> {STATE}/plan.log 2>&1")
    print("\nBriefs appear in `da briefs`; nothing is written, pushed or posted beyond Slack thread replies.")


def cmd_status(args):
    br = branch()
    b = brief_for_branch(br)
    rounds = sorted((REVIEWS / slug(br, 80)).glob("round-*")) if (REVIEWS / slug(br, 80)).exists() else []
    last = json.loads((rounds[-1] / "review.json").read_text()) if rounds and (rounds[-1] / "review.json").exists() else {}
    print(f"branch:  {br}\nbrief:   {b['id'] + ' ' + b['title'] if b else '-'}\n"
          f"reviews: {len(rounds)} (last verdict: {last.get('verdict', '-')})")
    open_b = [json.loads(p.read_text()) for p in BRIEFS.glob("b*.json")]
    open_b = [x for x in open_b if x["status"] not in ("shipped", "dropped")]
    print(f"open briefs: {len(open_b)}  (da briefs)")


# ---------- helpers for the /doc-agent orchestrator (Claude Code)

def _gh_json(*a) -> dict | list:
    return json.loads(out(["gh", *a]))


def _signal_from_url(url: str, max_diff: int = 60000) -> dict:
    """GitHub PR / commit / compare / repo URL, or Slack permalink → one signal."""
    m = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", url)
    if m:
        repo, n = m.groups()
        pr = _gh_json("pr", "view", n, "--repo", repo, "--json",
                      "title,body,url,state,mergedAt,files,commits,labels")
        diff = run(["gh", "pr", "diff", n, "--repo", repo], check=False, capture=True).stdout
        return {"source_id": f"pr:{repo}#{n}", "type": "commit", "repo": repo, "url": pr["url"],
                "pull_requests": [{"number": int(n), "title": pr["title"], "body": (pr.get("body") or "")[:6000],
                                   "url": pr["url"], "merged": bool(pr.get("mergedAt"))}],
                "commits": [{"sha": c["oid"][:12], "message": c.get("messageHeadline", "")} for c in pr.get("commits", [])],
                "files": [f["path"] for f in pr.get("files", [])], "diff": diff[:max_diff]}
    m = re.match(r"https?://github\.com/([^/]+/[^/]+)/commit/([0-9a-f]{7,40})", url)
    if m:
        repo, sha = m.groups()
        c = _gh_json("api", f"repos/{repo}/commits/{sha}")
        diff = "".join(f"--- {f['filename']}\n{f.get('patch') or ''}\n" for f in c.get("files", []))
        return {"source_id": f"commit:{repo}@{sha[:12]}", "type": "commit", "repo": repo, "url": url,
                "commits": [{"sha": sha[:12], "message": c["commit"]["message"][:2000]}],
                "files": [f["filename"] for f in c.get("files", [])], "diff": diff[:max_diff]}
    m = re.match(r"https?://github\.com/([^/]+/[^/]+)/compare/([^.]+)\.\.\.?(.+)$", url)
    if m:
        repo, a, b = m.groups()
        c = _gh_json("api", f"repos/{repo}/compare/{a}...{b}")
        diff = "".join(f"--- {f['filename']}\n{f.get('patch') or ''}\n" for f in c.get("files", []))
        return {"source_id": f"commit:{repo}@{b[:12]}", "type": "commit", "repo": repo, "url": url,
                "commits": [{"sha": x["sha"][:12], "message": x["commit"]["message"][:2000]} for x in c.get("commits", [])],
                "files": [f["filename"] for f in c.get("files", [])], "diff": diff[:max_diff]}
    m = re.match(r"https?://github\.com/([^/]+/[^/#?]+)/?$", url)
    if m:  # a repo: take its most recently merged PR
        repo = m.group(1)
        prs = _gh_json("pr", "list", "--repo", repo, "--state", "merged", "--limit", "1", "--json", "url")
        if not prs:
            die(f"{repo} has no merged PRs; pass a PR, commit or compare URL instead.")
        return _signal_from_url(prs[0]["url"], max_diff)
    m = re.match(r"https?://[^/]*slack\.com/archives/([A-Z0-9]+)/p(\d{10})(\d{6})", url)
    if m:
        ch, sec, frac = m.groups()
        ts = f"{sec}.{frac}"
        tm = re.search(r"thread_ts=(\d+\.\d+)", url)
        root = tm.group(1) if tm else ts
        from common import http_json, redact
        for ws in cfg()["slack"]["workspaces"]:
            token = os.environ.get(ws["token_secret"])
            if not token:
                continue
            r = http_json("https://slack.com/api/conversations.replies", headers={"Authorization": f"Bearer {token}"},
                          params={"channel": ch, "ts": root, "limit": 200})
            if r.get("ok"):
                external = ws.get("external") or any(c.get("id") == ch and c.get("external") for c in ws.get("channels", []))
                thread = [{"who": "community member" if external else (m_.get("user") or m_.get("username") or "bot"),
                           "text": redact(m_.get("text", "")) if external else m_.get("text", "")}
                          for m_ in r.get("messages", [])]
                return {"source_id": f"slack:{ws['name']}:{ch}:{root}", "type": "slack", "workspace": ws["name"],
                        "channel": ch, "thread_ts": root, "url": url, "reply_in_thread": False, "thread": thread}
        die("couldn't read that Slack thread with the tokens in .env (bot not in the channel?). Paste the thread text instead.")
    die(f"don't know how to read {url}. Paste the content instead.")


def cmd_intake(args):
    """Turn whatever the user gave the /doc-agent into run/signals-intake.json."""
    RUN.mkdir(parents=True, exist_ok=True)
    for f in RUN.glob("signals-*.json"):
        f.unlink()
    (RUN / "briefs.json").unlink(missing_ok=True)
    from common import redact
    sigs, now = [], int(time.time())
    for i, url in enumerate(args.url or []):
        sigs.append(_signal_from_url(url))
    if args.text:
        sigs.append({"source_id": f"manual:{now}", "type": "manual_request", "url": "local",
                     "request": " ".join(args.text), "pages": args.page or []})
    for path in args.file or []:
        text = Path(path).read_text()
        kind = "pasted_thread" if args.kind == "thread" else "manual_request"
        sigs.append({"source_id": f"{kind}:{now}:{Path(path).name}", "type": kind, "url": "local",
                     "request": redact(text) if args.redact else text, "pages": args.page or []})
    if not sigs:
        die("nothing to take in: pass text, --url or --file")
    (RUN / "signals-intake.json").write_text(json.dumps(sigs, indent=2, ensure_ascii=False))
    print(json.dumps([{"source_id": s["source_id"], "type": s["type"], "files": len(s.get("files", [])),
                       "diff_chars": len(s.get("diff", "")), "thread_msgs": len(s.get("thread", []))} for s in sigs], indent=2))


def cmd_save_plan(args):
    created = store_plan(args.origin)
    print(json.dumps([{"id": b["id"], "status": b["status"], "title": b["title"],
                       "md": str(brief_path(b["id"], "md").relative_to(ROOT))} for b in created], indent=2))


def cmd_attach(args):
    """Attach a brief to a branch (so review/learn/ship find it). --new creates/checks out
    docs/<id>-<slug> from the base; without it the current branch is used."""
    b = load_brief(args.id)
    if args.new:
        if dirty():
            die("you have uncommitted changes. Commit or stash them first, or attach without --new.")
        br = b.get("branch") or f"docs/{b['id']}-{slug(b['title'])}"
        exists = run(["git", "rev-parse", "--verify", "--quiet", br], check=False, capture=True).returncode == 0
        run(["git", "checkout", "-q", br] if exists else ["git", "checkout", "-q", "-b", br, base_ref(args)])
    if branch() == cfg()["docs"]["base_branch"]:
        die(f"you're on {branch()}. Use `da attach {b['id']} --new` to make a docs branch.")
    b["branch"] = branch(); b["status"] = "writing"; save_brief(b)
    print(json.dumps({"id": b["id"], "branch": b["branch"], "base": base_ref(args),
                      "brief_md": str(brief_path(b["id"], "md").relative_to(ROOT))}))


def cmd_check(args):
    os.environ.setdefault("SUPRSEND_API_BASE", cfg()["reviewer"]["staging"]["api_base"])
    base = base_ref(args)
    run_checks(base, set(filter(None, (args.skip or "").split(","))))
    summary = {}
    for f in ["snippets.json", "browser.json", "render.json"]:
        p = RUN / f
        if p.exists():
            data = json.loads(p.read_text())
            if f == "snippets.json":
                ran = [r for r in data if r.get("kind") == "executed"]
                summary[f] = f"{len(ran)} run, {sum(1 for r in ran if r.get('exit_code') != 0)} failed"
            elif f == "browser.json":
                summary[f] = f"{len(data)} flow(s), {sum(1 for r in data if not r['ok'])} failed"
            else:
                summary[f] = f"{len(data)} render(s), {sum(1 for r in data if not r['ok'])} with problems"
    if (RUN / "vale.json").exists():
        try:
            v = json.loads((RUN / "vale.json").read_text() or "{}")
            summary["vale.json"] = f"{sum(len(x) for x in v.values())} issue(s)"
        except json.JSONDecodeError:
            pass
    print(json.dumps({"base": base, "changed_pages": changed_pages(base), "results": summary}, indent=2))


def cmd_record_review(args):
    """Store the reviewer's run/review.json + review.md as the next round for this branch."""
    dest_root = REVIEWS / slug(branch(), 80)
    n = len(list(dest_root.glob("round-*"))) + 1 if dest_root.exists() else 1
    dest = dest_root / f"round-{n}"; dest.mkdir(parents=True, exist_ok=True)
    for f in ["review.json", "review.md", "snippets.json", "browser.json", "render.json", "vale.json"]:
        if (RUN / f).exists():
            shutil.copy(RUN / f, dest / f)
    review = json.loads((RUN / "review.json").read_text()) if (RUN / "review.json").exists() else {}
    commits = agent_commits(base_ref(args))
    print(json.dumps({"round": n, "verdict": review.get("verdict"),
                      "last_commit_is_agent": bool(commits) and commits[-1]["agent"],
                      "max_rounds": cfg()["reviewer"]["max_rounds"]}))


def cmd_log_request(args):
    FEEDBACK.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK / f"{slug(branch(), 80)}.jsonl", "a") as f:
        f.write(json.dumps({"type": "request", "text": " ".join(args.text),
                            "at": dt.datetime.now().isoformat(timespec="seconds")}) + "\n")
    print("logged")


def cmd_feedback(args):
    base = base_ref(args)
    feedback, metrics = build_feedback(base)
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "feedback.json").write_text(json.dumps(feedback, indent=2, ensure_ascii=False))
    (RUN / "metrics-line.json").write_text(json.dumps(metrics))
    METRICS.mkdir(parents=True, exist_ok=True)
    (METRICS / f"{slug(branch(), 80)}.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({"human_commits": metrics["human_commits"], "requests": metrics["change_requests"],
                      "written_by_human": feedback["written_by_human"],
                      "anything_to_learn": bool(feedback["human_edit_diff"] or feedback["change_requests"]
                                                or feedback["written_by_human"])}))


def cmd_env(args):
    """Run a command with .env loaded (for subagents testing on staging). Values never printed."""
    cmd = [c for c in args.command if c != "--"]
    if not cmd:
        die("usage: da env -- <command> [args]")
    os.environ.setdefault("SUPRSEND_API_BASE", cfg()["reviewer"]["staging"]["api_base"])
    sys.exit(subprocess.run(cmd if len(cmd) > 1 else cmd[0], shell=len(cmd) == 1, cwd=ROOT).returncode)


def cmd_postman_prep(args):
    """Pull the live collection onto the current branch and write the newman env file."""
    run([sys.executable, str(SCRIPTS / "postman_sync.py"), "pull"])
    run(["git", "add", "postman/"])
    run(["git", "commit", "-qm", "postman: sync latest from the Postman app", "-m", TRAILER], check=False)
    envfile = STATE / "staging.env.json"; STATE.mkdir(parents=True, exist_ok=True)
    run([sys.executable, str(SCRIPTS / "postman_sync.py"), "env", str(envfile)])
    diff = run(["git", "diff", base_ref(args), "--", "reference", "openapi.yaml"], check=False, capture=True).stdout
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "api-changes.txt").write_text(diff[:80000] or "Drift check: compare the whole collection with the docs.")
    print(json.dumps({"collection": "postman/collection.json", "env_file": str(envfile.relative_to(ROOT)),
                      "changes": ".docs-agent/run/api-changes.txt"}))


# ---------- keeping skills in step with GitHub (main is the source of truth)

AGENT_PATHS = [".claude/agents", ".claude/skills", ".docs-agent", ".github/workflows/docs-",
               ".github/actions/docs-agent-setup"]
AGENT_SKIP = [".docs-agent/local/state/", ".docs-agent/local/.env", ".docs-agent/run/",
              "node_modules/", "__pycache__/", ".docs-agent/metrics/"]


def _is_agent_file(f: str) -> bool:
    managed = cfg().get("local", {}).get("managed_skills") or ["docs-*", "doc-agent", "suprsend-docs-writer"]
    if any(x in f for x in AGENT_SKIP) or not any(f.startswith(p) for p in AGENT_PATHS):
        return False
    if f.startswith(".claude/skills/"):
        import fnmatch
        return any(fnmatch.fnmatch(f.split("/")[2], m) for m in managed)
    if f.startswith(".claude/agents/"):
        return Path(f).name.startswith("docs-")
    return True


def _blob(ref: str | None, f: str) -> bytes | None:
    if ref is None:
        p = ROOT / f
        return p.read_bytes() if p.is_file() else None
    r = subprocess.run(["git", "show", f"{ref}:{f}"], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def _agent_changes(main: str) -> dict:
    """Compare this working tree with main for agent files. behind: main changed it;
    local: you changed it; both: changed on both sides since this branch left main."""
    mb = git("merge-base", "HEAD", main) or None
    files = set(git("ls-files", "-co", "--exclude-standard").splitlines()) | \
        set(git("ls-tree", "-r", "--name-only", main).splitlines())
    res = {"main": main, "behind": [], "local": [], "both": []}
    for f in sorted(x for x in files if _is_agent_file(x)):
        wt, m = _blob(None, f), _blob(main, f)
        if wt == m:
            continue
        base = _blob(mb, f) if mb else None
        res["behind" if base == wt else "local" if base == m else "both"].append(f)
    return res


def cmd_sync(args):
    main = base_ref(args)
    ch = _agent_changes(main)
    uncommitted = [f for f in ch["local"] + ch["both"]
                   if _blob("HEAD", f) != _blob(None, f)]
    print(json.dumps({**ch, "uncommitted_local": uncommitted, "branch": branch()}, indent=2))
    if not args.apply or not (ch["behind"] or ch["both"]):
        return
    if dirty():
        die("commit or stash your changes before syncing.")
    if branch() == cfg()["docs"]["base_branch"]:
        run(["git", "pull", "-q", "--ff-only", "origin", branch()])
    else:
        r = run(["git", "merge", "--no-edit", "-q", main], check=False)
        if r.returncode != 0:
            die("merge had conflicts. Resolve them (or `git merge --abort`), then commit.")
    say("Synced with main. Restart Claude Code if files in .claude/agents changed.")


def cmd_skills_pr(args):
    """Put your local agent-file changes on their own skills/… branch from main and open a PR,
    without switching your branch. Then take them off this branch (they return when the PR merges)."""
    import tempfile
    main = base_ref(args)
    ch = _agent_changes(main)
    todo = ch["local"] + ch["both"]
    if not todo:
        say("No local skill/agent changes to push."); return
    mb = git("merge-base", "HEAD", main) or None
    wt_dir = Path(tempfile.mkdtemp(prefix="da-skills-"))
    title = args.title or "skills: changes from local runs"
    br = f"skills/{dt.date.today().isoformat()}-{slug(title, 30)}-{int(time.time()) % 10000}"
    run(["git", "worktree", "add", "-q", "-b", br, str(wt_dir), main])
    conflicts, url = [], None
    try:
        for f in todo:
            mine, theirs = _blob(None, f), _blob(main, f)
            if f in ch["both"] and not args.ours and theirs is not None and mine is not None:
                base = (_blob(mb, f) if mb else None) or b""
                tmp = Path(tempfile.mkdtemp())
                (tmp / "m").write_bytes(mine); (tmp / "b").write_bytes(base); (tmp / "t").write_bytes(theirs)
                r = subprocess.run(["git", "merge-file", "-p", str(tmp / "m"), str(tmp / "b"), str(tmp / "t")],
                                   capture_output=True)
                if r.returncode != 0:
                    conflicts.append(f); continue
                mine = r.stdout
            dest = wt_dir / f
            if mine is None:
                dest.unlink(missing_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(mine)
        if conflicts:
            die("these files changed on main too and the edits overlap:\n  " + "\n  ".join(conflicts)
                + "\nRun `da sync --apply` to bring main's version in and redo your edit, "
                  "or `da skills-pr --ours` to keep yours.")
        body = Path(args.body_file).read_text() if args.body_file and Path(args.body_file).exists() \
            else "Skill/agent changes made while running the docs agents locally."
        run(["git", "-C", str(wt_dir), "add", "-A"])
        run(["git", "-C", str(wt_dir), "commit", "-qm", title, "-m", TRAILER])
        run(["git", "-C", str(wt_dir), "push", "-q", "-u", "origin", br])
        url = out(["gh", "pr", "create", "--base", cfg()["docs"]["base_branch"], "--head", br,
                   "--title", title, "--body", body, "--label", cfg()["docs"]["labels"].get("skill_update", "skill-update")])
        say(f"Skill PR: {url}")
    finally:
        run(["git", "worktree", "remove", "--force", str(wt_dir)], check=False)
        if url is None:
            run(["git", "branch", "-q", "-D", br], check=False)
    if args.keep:
        return
    # Take them off this branch so the docs PR stays docs-only. They're safe in the skills PR.
    committed = [f for f in todo if _blob("HEAD", f) != (_blob(mb, f) if mb else None)]
    for f in todo:
        head = _blob("HEAD", f)
        target = (_blob(mb, f) if mb else None) if f in committed else head
        p = ROOT / f
        if target is None:
            p.unlink(missing_ok=True)
        else:
            p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(target)
    if committed:
        run(["git", "add", "-A", "--"] + committed)
        run(["git", "commit", "-qm", f"skills: moved to {url}", "-m", TRAILER])
    say("Removed them from this branch; `da sync --apply` brings them back once the PR is merged.")


# ---------------------------------------------------------------- main

def main():
    load_env()
    ap = argparse.ArgumentParser(prog="da", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup").set_defaults(fn=cmd_setup)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    p = sub.add_parser("plan"); p.add_argument("--no-slack", action="store_true")
    p.add_argument("--no-mark-seen", action="store_true"); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("brief"); p.add_argument("action", choices=["new", "drop", "ready"])
    p.add_argument("text", nargs="*"); p.add_argument("--page", action="append")
    p.add_argument("--category"); p.add_argument("--no-plan", action="store_true"); p.set_defaults(fn=cmd_brief)
    p = sub.add_parser("briefs"); p.add_argument("--all", action="store_true"); p.set_defaults(fn=cmd_briefs)
    p = sub.add_parser("show"); p.add_argument("id"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("write"); p.add_argument("id"); p.add_argument("--here", action="store_true")
    p.add_argument("--force", action="store_true"); p.add_argument("--no-review", action="store_true")
    p.add_argument("--base"); p.set_defaults(fn=cmd_write)
    p = sub.add_parser("review"); p.add_argument("--base"); p.add_argument("--no-autofix", action="store_true")
    p.add_argument("--skip", help="comma list: vale,links,samples,browser,render"); p.set_defaults(fn=cmd_review)
    p = sub.add_parser("revise"); p.add_argument("text", nargs="+"); p.add_argument("--no-review", action="store_true")
    p.add_argument("--skip"); p.add_argument("--base"); p.set_defaults(fn=cmd_revise)
    p = sub.add_parser("learn"); p.add_argument("--base"); p.set_defaults(fn=cmd_learn)
    p = sub.add_parser("ship"); p.add_argument("--base"); p.add_argument("--title"); p.add_argument("--draft", action="store_true")
    p.add_argument("--force", action="store_true"); p.add_argument("--no-learn", action="store_true"); p.set_defaults(fn=cmd_ship)
    p = sub.add_parser("ui-check"); p.add_argument("--briefs", action="store_true"); p.set_defaults(fn=cmd_ui_check)
    p = sub.add_parser("postman"); p.add_argument("--publish", action="store_true"); p.add_argument("--base")
    p.set_defaults(fn=cmd_postman)
    p = sub.add_parser("weekly"); p.add_argument("--base"); p.set_defaults(fn=cmd_weekly)
    sub.add_parser("schedule").set_defaults(fn=cmd_schedule)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    # used by the /doc-agent skill inside Claude Code
    p = sub.add_parser("intake"); p.add_argument("text", nargs="*"); p.add_argument("--url", action="append")
    p.add_argument("--file", action="append"); p.add_argument("--page", action="append")
    p.add_argument("--kind", choices=["request", "thread"], default="request")
    p.add_argument("--redact", action="store_true"); p.set_defaults(fn=cmd_intake)
    p = sub.add_parser("save-plan"); p.add_argument("--origin", default="manual"); p.set_defaults(fn=cmd_save_plan)
    p = sub.add_parser("attach"); p.add_argument("id"); p.add_argument("--new", action="store_true")
    p.add_argument("--base"); p.set_defaults(fn=cmd_attach)
    p = sub.add_parser("check"); p.add_argument("--base"); p.add_argument("--skip"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("record-review"); p.add_argument("--base"); p.set_defaults(fn=cmd_record_review)
    p = sub.add_parser("log-request"); p.add_argument("text", nargs="+"); p.set_defaults(fn=cmd_log_request)
    p = sub.add_parser("sync"); p.add_argument("--apply", action="store_true"); p.add_argument("--base")
    p.set_defaults(fn=cmd_sync)
    p = sub.add_parser("skills-pr"); p.add_argument("--ours", action="store_true"); p.add_argument("--title")
    p.add_argument("--body-file"); p.add_argument("--keep", action="store_true"); p.add_argument("--base")
    p.set_defaults(fn=cmd_skills_pr)
    p = sub.add_parser("env"); p.add_argument("command", nargs=argparse.REMAINDER); p.set_defaults(fn=cmd_env)
    p = sub.add_parser("postman-prep"); p.add_argument("--base"); p.set_defaults(fn=cmd_postman_prep)
    p = sub.add_parser("feedback"); p.add_argument("--base"); p.set_defaults(fn=cmd_feedback)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
