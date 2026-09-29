# Review Checklist — for auditing existing docs and self-reviewing drafts

Run all three lenses. Score each item pass/fail; every fail becomes a row in the issue table.

## Lens 0 — Facts (run first)

- [ ] Every claim (param, default, limit, error string, response field, UI label, behaviour) traces to a source: code, OpenAPI, tested behaviour, PRD or an engineer's thread. Unsourced claim = Blocker.
- [ ] No hedging words about product behaviour ("typically", "usually", "should", "may").
- [ ] Response JSON is captured or built exactly from the schema, not invented.
- [ ] Updates: nothing outside the change's scope was rewritten or deleted. Unexplained deletion = Blocker.
- [ ] Gaps are listed, not papered over.

## Lens 1 — Structural

- [ ] **Single doc type.** The page is identifiably one of: concept / quickstart / implementation guide / API reference / SDK / AI integration / changelog. Mixed content (setup steps inside a concept, essays inside a reference) = blocker; the fix is usually "move to page X and link."
- [ ] **Purpose fulfilled.** Concept answers "what/when/why"; guide gets the feature live; reference is complete and neutral; quickstart reaches a working result; changelog states user benefit only.
- [ ] Section order follows the reader's questions. A section is "missing" only if a real reader question goes unanswered, never because a template has it. Sections with no sourced content (empty Troubleshooting, generic Next steps) are an issue.
- [ ] Opens with a 1–3 sentence "what this page covers / what you'll have" — no preamble.
- [ ] All personas covered where required (guides: dashboard + API + SDK + AI/MCP).
- [ ] Disambiguation from neighboring concepts present where confusion is likely (Lists vs Objects, Batch vs Digest, Broadcast vs Workflow).
- [ ] Cross-links: concept ↔ guide ↔ reference ↔ changelog all point at each other; Next steps cards exist and go to the genuinely-next pages.
- [ ] Frontmatter complete: title (right grammatical form for the type — noun for concepts, verb phrase for guides), one-sentence `description`.

## Lens 2 — Visual

- [ ] No wall of text: any 3+ sequential actions are `<Steps>`; any 3+ parallel facts with shared attributes are a table.
- [ ] A flow/lifecycle/architecture that the reader must hold in their head has a Mermaid diagram.
- [ ] Screenshots (or placeholders) exist at every dashboard decision point; all wrapped in `<Frame>` with alt text.
- [ ] Multi-language / multi-persona code uses `<CodeGroup>`/`<Tabs>` — prose is never repeated per language.
- [ ] Edge cases / advanced config / troubleshooting are in Accordions, not inflating the main path.
- [ ] Callout discipline: ≤ ~1 per screen; `<Warning>` reserved for genuinely dangerous things; no callout used as a paragraph style.
- [ ] Heading hierarchy is clean (## then ###, no skips); headings are short and scannable in the TOC.

## Lens 3 — Textual (human readability + AI completeness)

Human side:
- [ ] Second person, active voice, present tense throughout.
- [ ] No filler ("simply", "just", "in order to", "please note that", marketing adjectives in non-changelog pages).
- [ ] Paragraphs ≤ 4 sentences; one idea each.
- [ ] Jargon defined on first use or wrapped in `<Tooltip>`; terminology matches `suprsend-context.md` (user not subscriber, commit not publish...).

AI side (the completeness audit):
- [ ] Every code example runnable as-is: imports, client init, realistic values from a real customer persona (not generic `order_placed`/Acme). No `foo`, `<your-value-here>` without an adjacent explanation of the format, or elided "..." in required positions.
- [ ] API/schema pages: every request and response field the source defines is listed, nested fields included, each with type, required/optional, default, valid values and a plain one-line description. Values the source doesn't give are in Gaps, not guessed.
- [ ] Every variant the endpoint or structure supports has its own example (recipients, tenant, idempotency, channel overrides; every workflow node type in a real combination; every template channel/variant), with a coverage table at the top. Each example was run or schema-validated.
- [ ] Requests AND responses shown, including at least one error response with the exact error string.
- [ ] All behavioral branches stated ("if X then Y, otherwise Z"), no "handles this appropriately".
- [ ] Limits, quotas, and plan gating stated with numbers.

Support-deflection audit:
- [ ] Could a user hit an error following this page and not find it named here? List the missing errors.
- [ ] Are the 3 most likely "why didn't it work" questions answered on-page?

## Output format for reviews

1. **Verdict** — 2–3 sentences: what the page does well, the single biggest problem, and whether it's the right doc type at all.
2. **Issue table:**

| # | Severity | Lens | Location | Issue | Fix |
|---|---|---|---|---|---|
| 1 | Blocker | Structural | "Setup" section | Implementation steps inside a concept page | Move to /docs/x-implementation, replace with a Card link |

Severities: **Blocker** (wrong type, missing/incorrect syntax info, broken examples) → **Should-fix** (missing sections, walls of text, incomplete params) → **Polish** (voice, filler, callout overuse).

3. **Rewrites** — for the top 3–5 issues, show the actual before/after MDX. Never only describe a fix that you could demonstrate.
4. **Offer** to apply everything and output the revised page.

## Optimization loop (when asked to "keep improving" a doc)

Prioritize by reader impact: (1) correctness of syntax/code, (2) missing content that causes support tickets, (3) structure/type purity, (4) visuals, (5) prose polish. Re-run the checklist after each pass; stop when a pass produces only Polish-level findings.
