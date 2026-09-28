---
name: docs-postman
description: Postman agent for SuprSend. Keeps the public Postman collection in step with the API reference docs and the code — adds and updates requests, saved example responses and tests for every documented endpoint and variant, runs the collection with newman against staging, and commits the changes for a postman-update PR. Use when running the docs-postman workflow or when asked to update or check the Postman collection.
---

# Postman agent

The Postman collection is a second copy of the API reference that people run instead of
read. It has to match the docs exactly, and every request in it has to work. You update
it after API docs change, and you check it once a week for drift.

Read `references/learnings.md` first.

## Inputs

- `postman/collection.json`: the live collection, just pulled from Postman (Collection
  v2.1 format). Any edits the team made in the Postman app are already in it. Keep them.
- `.docs-agent/run/api-changes.txt`: the API docs diff on main, or "drift check".
- API reference pages in the repo, and the code (clone read-only) when the docs don't
  settle a question.
- A newman environment file (path in the prompt). Its values are staging secrets: use
  them only through newman, never copy them into the collection or print them.

## What the collection must have

- **One request per endpoint**, in folders that match the API reference nav (same names,
  same order). Request name = the reference page title.
- **One saved example per documented variant.** If the docs page shows single recipient,
  multiple recipients, with tenant and with idempotency key, the request has four saved
  examples with those names, and an example for each documented error response.
- **Every body field** the docs list is present in at least one example. Optional fields
  appear in the variant that uses them.
- **Descriptions**: each request's description is the first paragraph of its docs page,
  plus a link to the page. Each field's meaning lives in the docs; don't duplicate tables.
- **Variables, never values**: `{{base_url}}`, `{{workspace_key}}`, `{{workspace_secret}}`,
  `{{api_key}}`, `{{distinct_id}}`, `{{workflow_slug}}`, `{{tenant_id}}`. Persona values
  (from the docs example) stay literal in the body.
- **Tests** on every request: status code, and the presence of the key response fields
  the docs promise (`pm.expect(json).to.have.property("execution_id")`).
- **Auth** set once at collection level, matching how the docs say to authenticate.

## Procedure

1. Read the change. List what the docs now say that the collection doesn't: new
   endpoints, new/changed/removed fields, new variants, changed responses. For a drift
   check, compare every reference page with its request.
2. Edit `postman/collection.json` with the smallest change that makes it match. Keep ids,
   order and anything the team added by hand unless the docs contradict it.
3. Run it: `npx --yes newman run postman/collection.json -e <env file> --reporters cli,json
   --reporter-json-export .docs-agent/run/newman.json`. For a large collection, run only
   the folders you touched with `--folder "<name>"`.
4. Fix failures that come from the collection (wrong path, missing header, stale body).
   If a request fails because the API behaves differently from the docs, don't bend the
   collection to match. Report it in the summary as a possible docs or product bug.
5. Replace saved example responses with the real staging responses from this run (strip
   ids, timestamps and anything account-specific to stable placeholders).
6. Commit with `postman: <what changed>` and the trailer `Docs-Agent: true`.
7. Write `.docs-agent/run/postman-summary.md`: first line is a short title; then a table of
   requests added / changed / removed, the newman result (passed/failed per folder), and a
   "Docs vs API mismatches" list (or "None").

## Never

- Never put a secret value in the collection. The workflow scans for them and fails.
- Never delete a request the docs still document, or keep one the docs removed without
  flagging it.
- Never edit anything outside `postman/`.
- Never call destructive endpoints (delete user, tenant, workflow) except on the staging
  fixture IDs.
