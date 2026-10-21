# Learnings: docs-planner

Rules learned from human review of past runs. The docs-learner agent proposes additions
through a `skill-update` PR. Newest first. Format:

`- **YYYY-MM-DD** (PR #n) — what happened → rule now in effect`

Once a rule is absorbed into SKILL.md itself, the learner moves the entry to
"Absorbed" at the bottom so this file stays short.

## Active

_None yet._

## Absorbed

- **2026-10-21** (PR #284) — One-click unsubscribe was planned as a new page, but it is a setting on preference categories, so the owner moved it into the existing concept, setup and user-preferences pages. The plan also missed that the field is on the preference category Management API (get, create/update, commit). → Default to existing pages and plan both options as an open question when unsure (SKILL.md step 5). For any new or changed field, check every Hub and Management API endpoint that carries the object, even when the signal only mentions the CLI or dashboard (SKILL.md step 4).
- **2026-10-21** (PR #284) — The pages sent readers to another page just to see what the recipient's inbox looks like. → Plan the screenshot inline; keep cross-page links to one "read more" (Brief quality bar).
