# Learnings: docs-reviewer

Rules learned from human review of past runs. The docs-learner agent proposes additions
through a `skill-update` PR. Newest first. Format:

`- **YYYY-MM-DD** (PR #n) — what happened → rule now in effect`

Once a rule is absorbed into SKILL.md itself, the learner moves the entry to
"Absorbed" at the bottom so this file stays short.

## Active

- **2026-10-15** (local `docs/verify-claims-against-source`) — While reviewing
  claims the owner called out that the reviewer needs a clear tiebreaker when
  sources disagree. Several of the misstatements this review surfaced lived in a
  brief or an existing doc paragraph long before the diff touched them, and the
  reviewer was tempted to defer to the written word rather than open the
  authoritative code. → Rule now in SKILL.md step 3 "Facts vs code": the order of
  truth is **code > PRD/brief > existing docs**. When any two of these disagree,
  treat the current state of the authoritative source code as the final answer;
  a brief fact or an existing doc paragraph that doesn't match the code is a
  Blocker on the code's side, flagged with the file and line in code that proves
  it.

- **2026-10-15** (local `docs/verify-claims-against-source`) — Across one full-page
  audit the owner caught claims that past reviewers had missed because they only
  checked the diff and the brief's `facts[]`: `dismissed` status falsely listed on
  webpush/whatsapp/slack/ms_teams (code is mobile-only), member edit access framed
  as "everywhere except production" when `isSandboxEnv` in
  `suprsend-app-new/src/utils/index.js` is a whitelist of `staging`/`sandbox` only,
  a Segment "default channel mapping" claim that doesn't exist in
  `collector/SegmentHandler.js`, a `user.save → async_edit` rename that picked the
  wrong SDK method as the primary save (`users.edit` is the sync path across all
  four backend SDKs), OTel connector latency documented as "1–2 minutes" when it is
  sub-second, and an inactive-marking period claim ("15 days for both WhatsApp and
  email") that contradicts a sibling page. → Rule now in SKILL.md step 3 "Facts vs
  code": validate every behavioural claim on each changed page (not just the diff),
  and on neighbouring pages the diff references, against the authoritative source.
  Step 3 now also lists the authoritative repos so the reviewer knows where to look:
  `suprsend-api`, `kinesis-consumer`, `collector`, `suprsend-app-new`,
  `suprsend-inbox-api`, `mcp-server`, and the four SDK repos. Contradictions across
  docs now have to be flagged with the repo that would resolve them, not silently
  resolved by preferring one doc over another.

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
