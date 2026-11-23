# Learnings: docs-postman

Rules learned from human review of past runs. The docs-learner agent proposes additions
through a `skill-update` PR. Newest first. Format:

`- **YYYY-MM-DD** (PR #n) — what happened → rule now in effect`

Once a rule is absorbed into SKILL.md itself, the learner moves the entry to
"Absorbed" at the bottom so this file stays short.

## Active

_None yet._

## Absorbed

- **2026-10-01** (local `docs/postman-sync-full`) — Live tokens in saved-response headers, `""` for array/object bodies, empty `raw` despite openapi examples, description text as `status`. → Sanitise saved responses, body generator rules, reason-phrase `status`, expanded `postman_sync.py check`, squash before ship (SKILL.md "What the collection must have", Procedure step 6).
- **2026-09-29** (PR #252) — Publish failed with `malformedRequestError`: placeholder ids and environment-scope `variable[].type`. → Real `uuid.uuid4()` ids, collection-scope type enum, push via `postman_sync.py push` before merge (SKILL.md "Postman schema gotchas").
