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
