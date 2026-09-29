# SuprSend Context — vocabulary, architecture, and docs conventions

Read this so new pages sound like the rest of docs.suprsend.com and use the correct primitives. When in doubt about current product details, fetch `https://docs.suprsend.com/llms-full.txt` or the specific page at `<url>.md`.

## What SuprSend is

Notification infrastructure: one API to trigger multi-channel notifications (email, SMS, WhatsApp, push (iOS/Android/web), Slack, MS Teams, In-App Inbox) with workflow orchestration, templates, user preferences, and analytics. Positioned developer-first: API + SDKs + CLI + MCP + AI agents.

## Core primitives (use these exact terms)

- **Workflow** — the orchestration unit. Nodes: Send/multi-channel, Smart Delivery, Delay (fixed/dynamic/relative), Batch, Digest, Wait Until, Branch (conditions incl. message status, datetime, array operators), Fetch (HTTP call mid-workflow), Invoke Workflow, Update User Profile, Add/Remove user in list, Update object subscription. Triggered by API call or Event. Versioned: edits are drafts until **committed**.
- **Template** — per-channel content, edited in the dashboard. Templates 2.0: **variants** (conditions on tenant/language/plan/trigger data; evaluated top-to-bottom, first match wins, default fallback), multi-lingual via **translations** (`{{t "key"}}` Handlebars helper, locale fallbacks, pluralization), Handlebars helpers (incl. `jsonParse`, `jsonPath`) and JSONNET for advanced channels. Draft → commit → version history → rollback.
- **User** — recipient with `distinct_id`, channels, properties. (Formerly "subscriber" — always say **user** now.) User merge API for identity consolidation.
- **Object** — non-user entity (team, Slack channel, shared inbox) with its own channels/preferences and **subscriptions** (users or nested objects subscribe to it; fan-out depth configurable). Use for reusable topic subscriptions and group notifications.
- **List** — user segment for **Broadcast** (one-shot, high throughput). Lists vs Objects is a recurring disambiguation — link `/docs/lists` vs `/docs/objects`.
- **Tenant** — customer/brand scoping for B2B: per-tenant branding, template variants, preference defaults.
- **Preferences** — categories (with channel-level defaults, opt-in/opt-out), user preference center (hosted page, embeddable SDK components), preference **tags**, per-category **digest schedule** (Instant/Daily/Weekly, user-chosen) and **condition properties** (thresholds/roles resolved at send time).
- **Workspace / environments** — staging vs production; sandbox restricts sends to **verified channels**; **Test Mode** redirects non-test traffic to a catch-all channel.
- **Schema** — JSON Schema validating workflow trigger payloads at the API layer; `suprsend schema generate-types` emits TS/Python/Go/Java/Kotlin/Swift/Dart types.
- **Vendors** — per-channel provider integrations (SES, SendGrid, Twilio, ACL Sinch, Mailjet, Bird, Pinnacle...). Vendor pages follow a fixed pattern: prerequisites → dashboard form field table → webhook/callback setup for delivery tracking.
- **Logs & analytics** — Requests → Workflow executions → Messages (end-to-end trace); message statuses: `triggered, sent, delivered, seen, clicked, dismissed, read/unread, archived`; Analytics 2.0, CSV export, observability connectors (Datadog, New Relic, OTEL — Enterprise plan), S3 v2 data export.

## AI surface (first-class personas in docs)

- **MCP server**: `npx suprsend start-mcp-server` (needs `SUPRSEND_SERVICE_TOKEN`); scoped tokens, `--tools` read-only flag, no destructive deletes.
- **CLI**: `brew install --cask suprsend/tap/suprsend` or `npx suprsend`; `pull/push/commit/sync --from staging --to production`, `workflow disable/enable`, `schema generate-types`.
- **Agent Skills**: `npx skills add suprsend/skills` (workflow-schema, cli, template-schema, docs-support skills).
- **SuprSend Agent** (dashboard) and **Slack Agent** (@SuprSend): build/debug/analyze by prompt.
- Docs are LLM-optimized: `/llms.txt`, `/llms-full.txt`, every page at `.md`.

## SDKs

Backend: Node.js (`@suprsend/node-sdk`), Python (`suprsend-py-sdk`), Go, Java. Frontend: Web (`@suprsend/web-sdk`, JWT auth, camelCase methods), React (`@suprsend/react`), React Native, Flutter, iOS (Swift), Android. Inbox SDKs: `@suprsend/react-inbox`, `@suprsend/web-inbox` (drop-in popover, full-screen, side-sheet feeds; bring-your-own-toast).

## Docs site conventions

- Structure: **Docs** (concepts + guides at `/docs/...`) and **API Reference** (`/reference/...`), plus Changelog at `/changelog/overview`.
- House style: second person, benefit-aware but not salesy; bold **dashboard click paths** (go to **Vendors → Email → Amazon SES**); dashboard deep links like `https://app.suprsend.com/en/staging/...` where helpful; `📘 Learn more in the [X documentation](/docs/x)` pattern in changelog entries; em-dash/arrow bullets (`**Bold lead** → payoff`) common in changelogs.
- Support email: support@suprsend.com — link it only as a last resort; the doc's job is to make it unnecessary.
- Plan gating: say "Requires the Enterprise plan" explicitly when true.
- Common cross-link hubs: /docs/workflows, /docs/templates, /docs/users, /docs/tenants, /docs/objects, /docs/lists, /docs/user-preferences, /docs/notification-category, /reference/cli-intro, /reference/mcp-overview.

## Competitive landscape (for the research step, not for publishing)

Direct: **Knock, Courier, Novu, MagicBell** (notification infra); **Braze, Customer.io, OneSignal, Iterable** (engagement platforms). Adjacent pattern-owners worth checking per topic: Hightouch/Segment (audiences/segmentation), Stripe (API reference craft), Linear/Resend/Vercel (changelog voice), Twilio/SendGrid (channel docs). Use them to sharpen framing per SKILL.md Step 1.5; never name them in published docs unless writing an explicit migration guide.

## Terminology dos and don'ts

| Say | Not |
|---|---|
| user | subscriber |
| trigger a workflow | fire/invoke a notification |
| commit (a template/workflow version) | publish/save-live |
| In-App Inbox | notification center/feed (unless referring to the feed component) |
| preference category | notification category (except the legacy page slug) |
| workspace | project/account (workspace = env-scoped) |
