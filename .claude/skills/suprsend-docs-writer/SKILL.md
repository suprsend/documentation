---
name: suprsend-docs-writer
description: Expert documentation writer and reviewer for SuprSend's Mintlify-based docs. Use this skill whenever the user wants to write, generate, update, review, restructure, or optimize any SuprSend documentation — concept docs, implementation guides, quickstarts, API references, SDK integration docs, AI integration docs, or changelog entries — including converting a PRD, feature spec, Slack thread, or release notes into documentation, auditing an existing doc page for structure/visuals/clarity, or answering "how should this doc be structured". Trigger even if the user just says "document this feature", "write docs for X", "update the docs from this PRD", or "review this doc page".
---

# SuprSend Documentation Writer

This skill writes, updates and reviews SuprSend's Mintlify docs. Every page has to work for
three readers:

1. **The skimming human** gets the point from headings and first sentences in 30 seconds.
2. **The AI agent** can implement the feature from the page alone, without guessing.
3. **The stuck user** finds the answer to "why didn't this work" on the page.

## Three rules that override everything else

These rules win over every template, checklist or older rule in this skill and its
reference files.

1. **Write only what you can trace to a source.** A parameter, default, limit, error
   message, response field, UI label or behaviour goes on the page only if a source says
   so. If no source says it, leave it out and list it under Gaps. A doc with a gap is
   fixable. A doc with a confident wrong fact costs us support tickets and trust.
2. **Design the structure for this doc.** There is no default set of sections. Work out
   what this reader needs to know for this feature, in the order they need it, and build
   the page from that. Two concept or guide pages can and should look different.
   Reference pages (API, SDK methods, CLI) are the exception: match the layout of their
   sibling pages so readers find fields in the same place every time.
3. **Edit, don't overwrite.** When a page already exists, change only what the source
   says changed. Everything else stays as it is.

## Workflow

### Step 0 — Collect sources and build a fact sheet

Get the source material: PRD, spec, code diff, Slack thread, support thread, or the live
page (append `.md` to any docs URL; the whole site is at
`https://docs.suprsend.com/llms-full.txt`).

Before writing, list every fact the doc will need in a fact sheet:

| Fact | Source |
|---|---|
| `idempotency_key` is an optional string on trigger | `src/workflow.ts:88` |
| Max length is 255 characters | PRD §3.2 |
| Duplicate trigger within 24h returns the first execution | ? (not in sources) |

How much to trust each source, most trusted first: source code or OpenAPI spec →
behaviour you or the tester observed on staging → PRD/spec → engineer or PM in a Slack
thread → the existing docs page (it may be out of date) → nothing else. Your general
knowledge of how "notification systems usually work" is not a source.

Every row with `?` is a **gap**. Resolve gaps by asking the user (interactive), by
reading code, or by carrying them into the Gaps list (pipeline). Never fill a gap with a
plausible value.

In the docs pipeline, the brief's `facts[]` is the fact sheet. Human comments on the
brief issue add to it.

### Step 1 — Classify the doc type

The type decides the page's **purpose** and what does **not** belong on it. It does not
decide the sections.

| Type | Reader's question | Doesn't belong |
|---|---|---|
| **Concept** | "What is this and when do I use it?" | Setup steps, full param lists |
| **Quickstart** | "Get me to a working result in <10 min" | Edge cases, every option |
| **Implementation guide** | "How do I build this in my product?" | Marketing, concept re-explanation |
| **API reference** | "What exactly does this accept and return?" | Tutorials, opinions |
| **SDK integration** | "How do I do this in my language?" | Dashboard walkthroughs |
| **AI integration** | "How do I connect my agent/MCP/CLI?" | Long concept essays |
| **Changelog** | "What changed and why should I care?" | Setup steps, request bodies |

One page, one type. When content of another type is needed, link to that page. A single
PRD often fans out into a concept page, a guide, reference updates and a changelog entry.
Propose the fan-out before writing.

### Step 1.5 — Research how others explain it (new features and changelogs)

Search how competitors (Knock, Courier, Novu, MagicBell, Braze, Customer.io, OneSignal)
and pattern-owners (Stripe for reference, Linear/Resend for changelogs) explain the
same thing. Take away: gaps they have that we don't, words migrating users will search
for, and questions they had to answer that we should answer too. Never copy wording.
Never name competitors in published docs. Research shapes framing. It is never a source
for facts about SuprSend.

### Step 2 — Design the outline for this doc

Do this fresh every time. Don't start from a template.

1. **Name the reader.** Who they are (persona below), what they are trying to get done,
   and what they already know. "A backend dev at a freight SaaS who already triggers
   workflows and now sees duplicate emails when their job retries."
2. **List their questions in the order they'll ask them.** Get these from the feature
   and the source material, not from a template. For the reader above: *What is this? →
   Do I need it? → How do I add it? → What happens on a duplicate? → How long is the key
   remembered? → What if I send a different payload with the same key?*
3. **Turn each question into a section**, or a sentence if the answer is short. The
   heading is the answer's topic in the reader's words ("Retry safely with an
   idempotency key", not "Overview").
4. **Drop questions with no sourced answer** (they go to Gaps) and questions another page
   already answers (link to it).
5. **Size the page to the content.** A small change can be three short sections.
   - Prerequisites only if there are real ones.
   - Troubleshooting only if the sources give real errors or pitfalls.
   - Next steps only if there are real next pages.
   - A diagram only if there is a flow or relationship to see.
6. **Then check `references/doc-templates.md`.** Use it to catch a reader question you
   missed. Don't use it to copy headings or order.
7. **Interactive sessions:** for a new page or a restructure, show the user the outline
   (headings plus a one-line purpose each) and the Gaps before writing the full page.

Two outlines to show what "fresh" means:

- *Concept: Digest schedules.* What a digest is → How it differs from batching (table)
  → How users pick their own schedule → What happens to messages when the schedule
  changes → Where to set it up (link to guide).
- *Reference update: `idempotency_key` on the trigger API.* One new row in the existing
  params table → a short "Retries and duplicates" section with a request and the real
  duplicate response → nothing else. No new Overview, no Next steps: the page already has
  them.

### Step 3 — Write

Follow the writing rules below. Output `.mdx` files, one per page.

### Step 4 — Check before delivering

1. **Fact audit.** Go through the draft line by line. Every factual claim must map to a
   row in the fact sheet. If one doesn't, delete it or move it to Gaps.
2. **Overwrite audit** (updates only). Diff the result against the original. Every
   removed or changed line needs a reason from the sources.
3. Run `references/review-checklist.md`. Treat its section lists as prompts, not
   requirements. A missing section only matters if a reader question goes unanswered.

## Updating an existing page

Most doc work is updates. This is where overwriting happens, so be strict.

- **Read the whole live page first**, plus its siblings in the nav, so your text fits in.
- **Change only what the source says changed.** Add the new param row, fix the wrong
  default, add the new section. Leave the rest word for word: headings (other pages link
  to their anchors), examples, screenshots, custom components, frontmatter.
- **Don't tidy up unrelated text in the same edit.** If you spot other problems, list
  them as suggestions under "Also noticed". Don't fix them silently.
- **Never delete content unless a source says it is wrong or removed.** List every
  deletion with its reason.
- **If the page contradicts your source**, don't silently pick one. If the source is code
  or tested behaviour, update the page and call out the change. Otherwise flag it and ask.
- **Restructure only when asked**, or when the change can't fit the current structure.
  Propose the new outline first and wait.

## No invented information

Facts need a source: parameter names, types, required/optional, defaults, valid values,
limits, error codes and messages, response shapes, plan availability, versions, dashboard
labels and click paths, and behaviour ("retries 3 times", "fails open").

**Never make up:**
- Response JSON. Use a captured response or one built exactly from the code or OpenAPI
  schema. Otherwise leave the response out and add it to Gaps.
- Error strings, error codes, rate limits, quotas, plan gating.
- Dashboard labels, menu paths, image URLs. Take them from a real browser run on the
  staging dashboard (in the docs repo: `docs-ui-flows`). Without one, use a screenshot
  placeholder with a note on what to capture.
- Support for a route or SDK the source doesn't mention. Only document the routes the
  feature actually supports (dashboard, API, SDKs, MCP/CLI).

**When a fact is missing,** pick one:
1. Ask (interactive sessions).
2. Write around it: say what you do know and link where the reader can check.
3. Leave a visible marker Mintlify won't render, and list it in Gaps:
   `{/* TODO(verify): how long idempotency keys are stored — not in PRD or code */}`

**Words that give guessing away:** "typically", "usually", "should", "may", "generally"
when describing product behaviour. Verify the fact and state it plainly, or remove it.

Parameters: give type, required/optional, default and valid values **when the sources
give them**. A missing default goes to Gaps. Don't write "defaults to null" because it
seems likely.

## API reference and schema docs: complete, with many examples

API pages, and pages that document a JSON structure (workflow definitions, template
schemas, trigger payloads), are where AI readers and stuck users go for exact answers.
Keep the page short in prose, but complete in fields and examples.

**Describe every field.** List every request field (path, query, header, body) and every
response field, including nested objects and array items (`channels[].type`,
`recipients[].$preferred_language`). Each field gets: name, type, required/optional,
default, valid values or format, constraints, and a one-line plain description of what
it does for the reader. Use `<ParamField>` / `<ResponseField>` with `<Expandable>` for
nesting (see `mintlify-syntax.md`).

Get the fields from the OpenAPI spec, the code (request validators, types, serializers)
or a captured response, in that order. "Every field" means every field the source
defines, not fields that seem likely. If the source has a field but no explanation of
it, read the code to see what it does. If that still doesn't tell you, list the field
with its type and put the description in Gaps. Never write a vague description to fill
the space ("Additional options").

**Cover the variants with separate examples.** One happy-path example isn't enough when
an endpoint or structure can be used in several ways. Before writing, list the variants
the source supports and write one example for each:
- **Endpoints:** each way of calling it. Single vs multiple recipients, `distinct_id` vs
  inline user, with tenant, with idempotency key, with attachments, each supported
  channel override. Include at least one error response per documented error.
- **Workflows:** every node type at least once, in a combination a customer would really
  use. For example: Delay → Send (reminder), Batch → Send (comment roll-up), Digest
  (weekly summary), Branch on message status → fallback channel, Wait Until → Send,
  Fetch → Branch on the fetched value, Invoke Workflow, Update User Profile, and a
  multi-channel Send with Smart Delivery.
- **Templates:** each channel's schema, variants (tenant, language, plan), translations,
  and the Handlebars helpers the page covers.

Put a short coverage table at the top of the examples section so readers can jump
straight to their case:

| Example | Use case | Nodes / options |
|---|---|---|
| Quote expiry reminder | Routewise reminds a shipper before a quote expires | Delay → Send (email) |
| Comment roll-up | Proofly groups comments on an asset | Batch → Send (inbox + email) |

Each example uses a real persona scenario (see below), is complete (no `...` in required
positions), and has been checked: run on staging, or validated against the JSON schema.
If you can't check an example, mark it ` norun` and say why in Gaps. Use `<CodeGroup>` for
the same example in cURL / Node / Python, and `<Tabs>` or accordions to keep a long list
of variants scannable.

## Writing for humans: keep it simple

These rules are the whole voice for docs. Don't load or apply the `suprsend-brand-voice`
skill when writing or reviewing docs: it's for marketing copy.

Write like you're explaining it to a smart developer who is new to SuprSend and in a
hurry.

- **Lead with the answer.** The first sentence of the page and of each section says the
  main thing.
- **Short sentences**, around 20 words or fewer. One idea per sentence. Paragraphs of
  2–3 sentences.
- **Plain words.** use (not utilize/leverage), help (not facilitate), so/to (not in order
  to), start (not initiate), set up (not provision), about (not approximately).
- **No filler:** simply, just, easily, seamlessly, powerful, robust, in today's world,
  please note that, it is important to.
- **You and active voice, present tense.** "SuprSend retries the send", not "the send is
  retried".
- **Define a term on first use**, in half a sentence.
- **Explain only where it prevents a mistake.** "Use `snappy` compression. Athena can't
  read `lz4`." Put deeper explanation in an Accordion or on a linked page so the main
  path stays short.

Before: *"In order to facilitate robust delivery, SuprSend's idempotency mechanism can be
leveraged to ensure that duplicate workflow executions are typically avoided."*
After: *"Pass an `idempotency_key` when you trigger a workflow. If your job retries with
the same key, SuprSend won't send the notification twice."*

## Examples come from our customers' world

Every example is something a real SuprSend customer of that type would actually build.
No `foo`/`bar`, no `test_event`, no "Acme sends a notification".

**Pick the persona that the feature serves best:**

| Persona | Fictional product | Typical events | Good for |
|---|---|---|---|
| Multi-tenant B2B SaaS | *Routewise*, freight quoting for 400 logistics companies | `quote_requested`, `quote_expiring`, `shipment_delayed` | tenants, template variants, objects, Slack/Teams, preferences |
| Collaboration apps | *Proofly*, creative review and approval | `comment_added`, `approval_requested`, `mention_created` | batch, digest, In-App Inbox, smart delivery |
| Fintech | *Ledgerly* (investing app), *Verifio* (KYC API) | `kyc_document_rejected`, `sip_debit_failed`, `statement_ready` | fallbacks, broadcasts/lists, logs, idempotency, vendors |
| Marketplaces / B2B2C | *Classnest* (schools → parents), *Bookable* (creator bookings) | `session_booked`, `session_reminder`, `fee_due` | delays, schedules, translations, WhatsApp |
| Dev / AI-native teams | *Shipfast*, a 6-person dev-tools startup | `deploy_failed`, `invite_accepted` | quickstarts, CLI, MCP, schemas |

In the docs repo, `.docs-agent/context/customers.md` has the full personas and realistic
values. In the pipeline, use the brief's `use_case`.

**Rules:**
- **A customer question becomes the example.** If the change came from a Slack or support
  thread, use that customer's scenario, anonymised. That reader is the one most likely to
  search for it.
- **Say why they'd do it.** One line of context makes the example teach: "Routewise
  reminds the shipper 2 hours before a quote expires, because expired quotes are lost
  deals."
- **One persona per page**, used the whole way through: the same user, event and payload
  in the concept intro, the code and the response. Use Tabs only when the feature clearly
  serves different personas.
- **Realistic values that match the persona:** `usr_8f3k2m`, `priya.nair@routewise-demo.com`,
  `freightco-eu`, `₹12,500` or `$1,240.00`.
- **Never name real customers.**
- **Runnable code:** imports, client setup, real-looking values. Credentials are always
  the house placeholders: SDK samples `"_workspace_key_"`, `"_workspace_secret_"`; REST samples `Bearer __YOUR_API_KEY__`; management API `ServiceToken <SERVICE_TOKEN>`. In the pipeline,
  IDs that must already exist (user, workflow slug, tenant) use the staging fixtures in
  `.docs-agent/config.yml → reviewer.staging` so the tester can run them. Persona values
  go in the payload. Mark snippets that can't run with ` norun` in the fence info string.

Bad: `workflow: "order_placed", data: { foo: "bar" }`
Good: `workflow: "quote-expiring-reminder", data: { quote_id: "QT-20931", lane: "Rotterdam → Hamburg", expires_in_hours: 2 }`

## Visual cues: use them when they help

- `<Steps>` for a procedure of 3+ steps the reader follows in order.
- Mermaid for a flow or relationship the reader would otherwise hold in their head.
- `<Frame>` + a real screenshot at dashboard decision points, captured from the staging
  dashboard (in the docs repo, with a flow: see `docs-ui-flows`). If you can't capture
  one, leave `<!-- SCREENSHOT: Batch node settings panel open -->`. Never invent image
  URLs.
- `<Tabs>`/`<CodeGroup>` for the same task in several languages. Never repeat prose per
  language.
- `<Accordion>` for edge cases and troubleshooting, so the main path stays short.
- Tables for 3+ items that share attributes (params, limits, comparisons).
- Callouts rarely: about one per screen at most. `<Warning>` only for data loss,
  breaking changes or things you can't undo.

Syntax for every component is in `references/mintlify-syntax.md`. Read it before writing
MDX. Don't write components from memory.

## How readers implement (guides)

SuprSend users implement through the dashboard, the REST API, the SDKs (Node.js and
Python first), and AI tools (MCP server, CLI, Agent Skills). A guide covers **the routes
this feature supports, according to the sources**, as Tabs or signposted sections. If a
source doesn't confirm a route (e.g. no MCP tool for it yet), leave it out. Don't write a
plausible-looking command.

## Reviewing existing docs

Use `references/review-checklist.md` with four lenses:

1. **Facts.** Is any claim unsourced, stale, or contradicted by code? This comes first.
2. **Structure.** Right doc type? Does the order follow the reader's questions? Content
   that belongs on another page? A "missing section" only counts if a real reader
   question goes unanswered. Never flag a section just because a template has it.
3. **Visual.** Walls of text, missing diagrams at real flows, callout overuse.
4. **Text.** Hard words, long sentences, passive voice, filler, generic examples,
   terminology that doesn't match `references/suprsend-context.md`.

On API/SDK/schema pages, also check that every field the source defines is listed and
described, and that every supported variant has an example.

Deliver: a 2–3 sentence verdict → an issue table (Blocker / Should-fix / Polish) → the
before/after MDX for the top issues. Offer to apply them as a minimal edit, following
"Updating an existing page".

## Reference files

- `references/suprsend-context.md`: product vocabulary, primitives, terminology do/don't.
  Read it for terms. It is background, not a source for specific facts like limits or
  defaults.
- `references/mintlify-syntax.md`: component syntax.
- `references/doc-templates.md`: a **pattern library**. It shows what each doc type often
  covers. Its section lists, "never reorder" notes, "mandatory" and required sections are
  examples, not rules. Use it only at Step 2, point 6.
- `references/review-checklist.md`: review prompts. Its "required section" checks are
  replaced by the four lenses above.
- `references/learnings.md`: log of past feedback.

## Output

1. The `.mdx` file(s), kebab-case names, full frontmatter (`title`, one-sentence
   `description`, `sidebarTitle` if the title is long).
2. **For updates, a change summary:** added / changed / removed, with the source for each.
3. **Gaps:** every fact you couldn't verify, and who can answer it. Write "None" only when
   there are none.
4. **Also noticed** (optional): problems outside the scope of this change.
5. Suggested nav placement and cross-links for new pages. For new features, a changelog
   entry draft.

## Self-improvement loop

**In the automated docs pipeline** (inside the docs repo via GitHub Actions), the
`docs-learner` agent turns PR feedback into skill edits through a `skill-update` PR. Never
edit this skill from inside a docs PR. The steps below are for interactive sessions.

1. **Capture corrections as you go.** Every time the user rejects a structure, rewrites a
   sentence pattern, changes a term or says "always/never X", note the rule it implies.
2. **Classify.** Generalisable ("don't add Next steps to reference updates") → skill
   update. One-off (a fact about this feature) → fix the doc only. Unsure → ask "Apply
   this to all future docs, or just this one?"
3. **Wait until the feedback is final** (the user approved the revision or the session is
   wrapping up). Don't update the skill on mid-draft experiments.
4. **Apply.** Put each rule where it belongs: writing rules in this file, component usage
   in `mintlify-syntax.md`, product terms in `suprsend-context.md`, review criteria in
   `review-checklist.md`. Merge into the existing rule instead of appending exceptions.
   New feedback beats old rules. Log each learning with a date in `references/learnings.md`.
5. **Save it.** Propose the updated skill to the user so it persists into future
   sessions, and summarise in bullets what changed.

If `learnings.md` shows repeated feedback in one area, the main rule needs a deeper
rewrite: propose it.
