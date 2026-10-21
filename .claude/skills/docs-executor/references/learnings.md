# Learnings: docs-executor

Rules learned from human review of past runs. The docs-learner agent proposes additions
through a `skill-update` PR. Newest first. Format:

`- **YYYY-MM-DD** (PR #n) — what happened → rule now in effect`

Once a rule is absorbed into SKILL.md itself, the learner moves the entry to
"Absorbed" at the bottom so this file stays short.

## Active

_None yet._

## Absorbed
- **2026-10-21** (PR #286) — An `<!-- SCREENSHOT -->` placeholder (prescribed by the skills) made MDX fail and blanked the page; old kebab-menu screenshots and click-paths were reused though the dashboard had changed. → `{/* */}` placeholders, compile every changed `.mdx`, treat existing screenshots as unverified on a rewrite (SKILL.md 4b, 6).
