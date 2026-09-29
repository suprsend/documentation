# Learnings: docs-postman

Rules learned from human review of past runs. The docs-learner agent proposes additions
through a `skill-update` PR. Newest first. Format:

`- **YYYY-MM-DD** (PR #n) — what happened → rule now in effect`

Once a rule is absorbed into SKILL.md itself, the learner moves the entry to
"Absorbed" at the bottom so this file stays short.

## Active

- **2026-09-29** (PR #252) — `postman/collection.json` from PR #251 passed newman but the
  auto-publish job's `PUT /collections/{uid}` returned HTTP 400 `malformedRequestError`
  for two reasons: (a) request/response/folder/item `id` fields were human-readable
  placeholders instead of real UUIDs, and (b) top-level `variable[].type` used
  environment-scope values `"default"`/`"secret"` instead of the collection-scope enum.
  → Rule now in effect (see SKILL.md "Postman schema gotchas"): always generate
  `uuid.uuid4()` for every id (regex
  `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`); restrict top-level
  `variable[].type` to `string | boolean | any | number`; treat newman success as
  necessary but not sufficient — also push via `postman_sync.py push` before merging.

## Absorbed
