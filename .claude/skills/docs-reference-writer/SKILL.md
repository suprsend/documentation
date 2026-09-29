---
name: docs-reference-writer
description: "Specialist writing lane for SuprSend reference docs — REST API reference, SDK method pages, CLI/MCP command reference, and schema docs (workflow JSON, template schemas, trigger payloads). Used by the docs executor for any brief page whose doc_type is api_reference, sdk, cli, mcp or schema. Focus is completeness and exactness: every field described, every variant exampled, every example verified."
---

# Reference writer

Reference pages answer "what exactly does this accept and return?". Readers (and AI
agents) come here for exact answers, not explanations. Completeness and correctness
matter more than prose. The shared rules in `suprsend-docs-writer` still apply: trace every
fact to a source, edit without overwriting, plain words, persona-based examples.

Read `references/learnings.md` first.

## Where reference content lives in suprsend/documentation

- **REST API reference is generated from `openapi.yaml`.** Each `reference/*.mdx` page is
  mostly frontmatter (`openapi: "POST /v1/user/{distinct_id}/"`). Field descriptions,
  types, defaults, enums, request examples and responses all live in the spec. So "describe
  every field" and "one example per variant" mean editing `openapi.yaml`:
  - every property gets a `description` (plus `default`, `enum`, `format`, `example` when
    the source gives them), nested objects and array `items` included;
  - variants go in the request body's named `examples` (one per way of calling it) and
    error responses under their status codes;
  - SDK snippets go in `x-codeSamples` (Node, Python, Go, Java at least, from the SDK code);
  - extra prose before the generated content goes in `x-mint.content`.
  Only hand-write MDX for what the spec can't express. Validate with
  `npx mintlify openapi-check openapi.yaml`.
- **Workflow node pages** (`reference/workflow-nodes/*`) and template/schema pages: the
  source of truth is `github.com/suprsend/schema`. Clone it and take node fields, types and
  enums from the JSON schema.
- **SDK pages** (`docs/*-sdk*`, e.g. `docs/node-trigger-workflow-from-api`): the source is the
  SDK repo in `config.yml → code_repos`.
- Placeholders are the house ones: `"_workspace_key_"`, `"_workspace_secret_"`,
  `Bearer __YOUR_API_KEY__`, `ServiceToken <SERVICE_TOKEN>`.

## Sources, in order

1. OpenAPI spec (if the API repo has one), request validators, types/interfaces, SDK
   method signatures, CLI flag definitions. Clone the repo and read them.
2. Captured responses: the reviewer's `snippets.json` from earlier runs, or a staging call
   you can see in the brief.
3. The brief's `facts[]`.
4. The existing page (may be stale: check it against 1).

## Procedure

1. **Extract the field inventory from code.** For the endpoint/method/structure, list
   every request field (path, query, header, body, nested) and every response field with
   type, required, default, enum/format, constraints. Write it down before touching the
   page. Fields the code has but the page doesn't = additions. Fields the page has but the
   code doesn't = flag as possibly removed (don't delete without the brief saying so).
2. **Describe each field** in one plain line: what it does for the reader, not a restated
   name. "Your ID for the user. Use the same ID you use in your own database." not "The
   distinct ID." No source explains it and code doesn't make it clear → Gaps.
3. **List the variants** the source supports (ways to call it; for workflows every node
   type in realistic combinations; for templates every channel/variant option). Write
   one example per variant plus one error example per documented error. Put a coverage
   table at the top of the examples section.
4. **Build examples** from the brief's persona. Same user, event and payload across
   cURL / Node / Python tabs. IDs that must exist use the staging fixtures. Each example
   must be runnable or schema-valid.
5. **Keep structure predictable.** Reference pages are the one place where consistency
   across pages beats a fresh outline: match the layout of sibling reference pages in the
   same nav group (read two of them). Don't add concept explanations; link to the guide.
6. **Postman.** If you add or change an endpoint, a request field or an example, set a
   line in the PR body: `Postman: needs update (<endpoint>)`. The Postman agent picks it
   up after merge.

## Never

- Never guess a type, default or enum from a field name.
- Never paste a response you didn't capture or build exactly from the schema.
- Never drop an existing field because it's missing from your inventory. Flag it.
