# Learnings: docs-reviewer

Rules learned from human review of past runs. The docs-learner agent proposes additions
through a `skill-update` PR. Newest first. Format:

`- **YYYY-MM-DD** (PR #n) — what happened → rule now in effect`

Once a rule is absorbed into SKILL.md itself, the learner moves the entry to
"Absorbed" at the bottom so this file stays short.

## Active

- **2026-10-01** (local `docs/postman-sync-full`) — Round 1 of the postman full
  reconcile shipped four live staging `ServiceToken SS.ST.*` values in saved
  responses. The reviewer caught them, but only because they happened to grep
  for `SS.ST.`; `postman_sync.py check` reported clean because it only inspected
  top-level `request.header`. → Rule now in SKILL.md step 5c "Postman secret
  sweep": every PR touching `postman/collection.json` gets an independent sweep
  of `response[*].header` and `response[*].originalRequest.header` for literal
  `Bearer <token>` / `ServiceToken <token>` values and for `SS.ST./SS.WS./SS.API.`
  prefixes anywhere in the file. Any hit is a blocker. Don't rely on the sync
  script alone.

## Absorbed
