# Docs agents on your laptop

Run the whole pipeline locally (plan → write → test → learn) and push only the finished
PR. It uses Claude Code on your machine with the same skills as the GitHub version, so
nothing runs in GitHub Actions and nothing is pushed until you run `da ship`.

## One-time setup

```bash
cd ~/…/suprsend/documentation/documentation       # your clone
alias da="$PWD/.docs-agent/local/da"              # add to ~/.zshrc to keep it
da setup                                          # Vale, Mintlify CLI, SDKs, browser
open .docs-agent/local/.env                       # paste your keys (see env.example)
da doctor                                         # everything ✓ ?
```

You need Claude Code (`npm i -g @anthropic-ai/claude-code`, then run `claude` once to log in),
the GitHub CLI logged in (`gh auth login`), Node 20+ and Python 3.

## Inside Claude Code: `/doc-agent`

Open Claude Code in the docs repo (`claude`) and give it whatever you have:

```
/doc-agent The batch page doesn't explain what happens on retries
/doc-agent https://github.com/suprsend/suprsend-node-sdk/pull/112
/doc-agent https://github.com/suprsend/suprsend-go        ← latest merged PR
/doc-agent https://suprsend.slack.com/archives/C09BPA6J5QF/p1790000000000000
/doc-agent here's a thread from the community: <paste>
/doc-agent continue                                        ← pick up where you left off
```

It runs the planner, shows you the brief and asks before writing; then the executor edits the
files on a `docs/…` branch, the reviewer tests the change on staging (samples, dashboard flows,
rendered pages), and the executor fixes what fails. You see the diff and the review, ask for
changes in plain words (or edit yourself), and when you're happy the learner updates the
skills. It pushes and opens the PR only when you say "ship".

The agents are in `.claude/agents/` (docs-planner, docs-executor, docs-reviewer, docs-postman,
docs-learner); the orchestrator is `.claude/skills/doc-agent/SKILL.md`. To stop Claude Code asking
permission for every `da`/git step, merge `claude-settings.example.json` into
`.claude/settings.local.json`.

## The two ways in (terminal)

**1. Automation finds the work.**
```bash
da plan              # new commits in the 16 code repos + Slack (+ email) since last run → briefs
da briefs            # b001  ready  … "Document idempotency_key on trigger"
da show b001         # read it; edit the .md file to answer open questions, then: da brief ready b001
da write b001        # executor writes it on docs/b001-…, then da review runs automatically
```
Run `da schedule` for a cron line that runs `da plan` every 2 hours while your laptop is on.

**2. You spot something (old page, unclear section, missing example).**

Either let the agents do it:
```bash
da brief new "The batch page doesn't explain what happens on retries" --page docs/batch.mdx
da write b002
```
or do it yourself:
```bash
git checkout -b fix/batch-retries origin/main
# edit, commit (git commit -am "…")
da review
```

## Iterate, then ship

```bash
da review                              # samples on staging, dashboard flows, rendered pages,
                                       # Vale, links, facts → verdict. Agent commits get auto-fixed
                                       # up to 2 rounds; your own commits never are
da revise "use the Routewise example"  # ask for a change (this is how the learner learns fastest)
# …or edit and commit yourself, then da review again
da ship                                # learner updates skills from your edits (separate commit),
                                       # pushes, opens the PR with the review in its body,
                                       # posts it in #documentation
```

`da ship` refuses if the last review wasn't a pass or you committed after it. `--force`
overrides, `--draft` opens a draft, `--no-learn` skips learning.

## Keeping skills in step with GitHub

`main` on GitHub is the one copy of the skills. The GitHub workflows and your laptop both read it.

- **GitHub → you:** `da sync` shows what's newer on main; `da sync --apply` merges main into your
  branch. `/doc-agent` checks this before every run, and `da attach --new` always branches from a
  fresh `origin/main`.
- **You → GitHub:** skill edits (from the learner or your own) never ride in a docs PR.
  `da skills-pr` opens a `skill-update` PR from main with just those files, without switching your
  branch. `/doc-agent` and `da ship` run it after the learner. `da ship` refuses a docs branch
  that touches skill files.
- **Both edited the same lines:** `da skills-pr` stops and names the files. Run `da sync --apply`
  and redo the edit, or `da skills-pr --ours` to keep yours.

Your other skills (product-marketing-writer and so on) are never included.

## Also

| Command | Does |
|---|---|
| `da status` | branch, brief, last verdict |
| `da ui-check [--briefs]` | clicks through every saved dashboard flow; `--briefs` files briefs for broken ones |
| `da postman` / `da postman --publish` | update the Postman collection on a branch / upload it after merge |
| `da weekly` | learner consolidation + autonomy report on a `skills/…` branch |

State (briefs, reviews, feedback, metrics) lives in `.docs-agent/local/state/`, which is
gitignored. Back it up if you care about the history.
