# Who reads our docs, and what examples they recognise

The planner picks one persona per brief. The executor writes examples in that persona's
world: their entities, their event names, their payload fields. Never `foo`, `bar`,
`test_event` or "Acme Corp sends a notification".

**Rule of thumb:** if a real signal (Slack thread, support email) triggered the brief, the
example is the customer's own scenario, anonymised. If a commit triggered it, pick the
persona below whose use case the change serves best.

Do not name real customers in docs. Use the fictional product names below.

> Source: suprsend.com/customers (Sep 2026) plus support themes. The docs team owns this
> file; the learner may propose edits when reviewers keep swapping personas.

## Personas

### 1. Multi-tenant B2B SaaS (most common)
Real-world shape: outreach tools, franchise management, logistics SaaS, energy software.
- **Fictional product:** *Routewise*, a freight quoting platform used by 400 logistics companies.
- **Entities:** tenant = the customer company; users = their ops staff; objects = teams/Slack channels.
- **Typical events:** `quote_requested`, `quote_expiring`, `shipment_delayed`, `invoice_overdue`.
- **Cares about:** per-tenant branding and templates, tenant-level preference defaults,
  Slack/MS Teams delivery, fewer support tickets from "I didn't get the email".
- **Best for examples of:** tenants, template variants, objects, preferences, Slack.

### 2. Collaboration and workflow apps
Real-world shape: design review tools, project tools, document approval.
- **Fictional product:** *Proofly*, where marketing teams review and approve creative assets.
- **Entities:** users, projects, assets, comments.
- **Typical events:** `comment_added`, `approval_requested`, `asset_approved`, `mention_created`.
- **Cares about:** In-App Inbox, batching ("5 new comments on Spring launch banner"),
  digests, not spamming active users (smart delivery: inbox first, email if unseen).
- **Best for examples of:** batch, digest, In-App Inbox, smart delivery, wait-until.

### 3. Fintech (B2C and B2B)
Real-world shape: KYC/identity platforms, investment apps.
- **Fictional product:** *Ledgerly*, an investing app with 2M users; *Verifio*, a KYC API.
- **Typical events:** `kyc_approved`, `kyc_document_rejected`, `sip_debit_failed`,
  `price_alert_triggered`, `statement_ready`.
- **Cares about:** delivery guarantees, SMS/WhatsApp fallback, OTP latency, audit logs,
  broadcasts to large lists, compliance (unsubscribe, preference categories).
- **Best for examples of:** fallback channels, broadcast/lists, logs, idempotency, vendors.

### 4. Marketplaces and B2B2C
Real-world shape: creator marketplaces, invoicing platforms, ed-tech serving schools and parents.
- **Fictional product:** *Classnest*, a school platform where schools (tenants) message
  teachers and parents; *Bookable*, a creator booking marketplace.
- **Typical events:** `session_booked`, `session_reminder`, `payout_sent`, `fee_due`.
- **Cares about:** scheduled and relative-time reminders, multi-lingual templates,
  WhatsApp, user-chosen digest schedules.
- **Best for examples of:** delays, schedules, translations, WhatsApp, preferences.

### 5. Developer / AI-native teams
Real-world shape: small eng teams wiring notifications with an AI coding agent.
- **Fictional product:** *Shipfast*, a 6-person dev-tools startup.
- **Cares about:** copy-paste setup, CLI, MCP server, Agent Skills, schema-generated types.
- **Best for examples of:** CLI, MCP, quickstarts, schemas, SDK installs.

## Realistic values to reuse

| Field | Value |
|---|---|
| distinct_id | `usr_8f3k2m` (Routewise), `inv_20931` (Ledgerly) |
| email | `priya.nair@routewise-demo.com` |
| tenant_id | `freightco-eu` |
| workflow slug | `quote-expiring-reminder`, `kyc-document-rejected` |
| Slack channel object | `ops-alerts-freightco` |
| amounts | `₹12,500` / `$1,240.00` (match the persona's market) |
