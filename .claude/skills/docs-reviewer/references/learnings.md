# Learnings: docs-reviewer

Rules learned from human review of past runs. The docs-learner agent proposes additions
through a `skill-update` PR. Newest first. Format:

`- **YYYY-MM-DD** (PR #n) — what happened → rule now in effect`

Once a rule is absorbed into SKILL.md itself, the learner moves the entry to
"Absorbed" at the bottom so this file stays short.

## Active

_None yet._

## Absorbed

- **2026-10-21** (PR #286) — Review caught brief claims that contradicted code (fixed 2h `prep_lead`, timestamps in dashboard timezone not UTC, static lists not waited for) and SDK rows for an undeclared field. → Check brief-sourced behaviour against code, and check SDK request schemas before accepting SDK doc changes.
- **2026-10-15** (local `docs/verify-claims-against-source`) — Reviewer deferred to briefs and existing docs when sources disagreed. → Order of truth code > PRD/brief > existing docs (SKILL.md step 3).
- **2026-10-15** (local `docs/verify-claims-against-source`) — Full-page audit found stale claims past reviews missed because only the diff was checked. → Verify every claim on each changed page and referenced neighbours against the listed authoritative repos; flag doc-vs-doc contradictions with the repo that resolves them (SKILL.md step 3).
- **2026-10-01** (local `docs/postman-sync-full`) — Live staging `ServiceToken` values in saved responses slipped past `postman_sync.py check`. → Independent Postman secret sweep of saved-response headers and `SS.ST./SS.WS./SS.API.` prefixes (SKILL.md step 5c).
