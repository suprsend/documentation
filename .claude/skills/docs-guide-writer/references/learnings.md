# Learnings: docs-guide-writer

Rules learned from human review of past runs. The docs-learner agent proposes additions
through a `skill-update` PR. Newest first. Format:

`- **YYYY-MM-DD** (PR #n) — what happened → rule now in effect`

Once a rule is absorbed into SKILL.md itself, the learner moves the entry to
"Absorbed" at the bottom so this file stays short.

## Active

_None yet._

## Absorbed

- **2026-10-21** (PR #284) — Too many "see X" links between pages, including one whose only purpose was showing the Gmail Unsubscribe header. → Put a screenshot inline when the reader only needs to see it; one "read more" link per topic (SKILL.md step 4). New pages only when existing pages have no home for the content (SKILL.md, Never).
- **2026-10-21** (PR #286) — Owner asked for: durations tied to large lists, concrete benefit wording, no repeated sentences, generic "you" examples instead of a named persona in prose, "channel" not "address". → `suprsend-docs-writer` writing and examples rules.
- **2026-10-21** (PR #286) — Changelog was dated today instead of the release date and needed a moment-led hook plus the trade-off. → SKILL.md step 8.
