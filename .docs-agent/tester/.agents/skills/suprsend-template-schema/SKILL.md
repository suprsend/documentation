---
name: suprsend-template-schema
description: "JSON schema for authoring or editing SuprSend template variants (channel + locale + tenant + content). Loads the variant envelope, per-channel content schemas, and Handlebars/JSONNET syntax references needed to write valid template JSON. Covers all 9 channels: email, sms, whatsapp, inbox, slack, ms_teams, androidpush, iospush, webpush. Use ONLY when the user wants the agent to create, modify, or edit a template variant (e.g. \"build an SMS variant\", \"add a French locale\", \"create a tenant-specific welcome email\"). Do NOT load for documentation, lookup, or conceptual questions (\"what is a variant\", \"how does templating work\", \"explain WhatsApp templates\") — load suprsend-docs-support for those."
metadata:
  author: "suprsend"
  category: "templates"
---

SuprSend templates define the content of a notification — the subject and body of an email, the text of an SMS, the layout of an in-app inbox message, and so on. Templates are channel-aware and locale-aware.

Internally, every template is modeled as a collection of **variants**. A variant pairs a channel, locale, optional tenant, and optional condition with channel-specific content. Even a simple template with no multi-tenant or multi-language requirements is just one variant — usually `tenant_id: null`, `locale: "en"`, `conditions: null`. Adding more locales, more tenants, or conditional content means adding more variants under the same template.

Each variant validates against `https://schema.suprsend.com/template/v2/variant_schema.json`. The `content` object inside a variant validates against a channel-specific schema selected by the `channel` field.


For a complete guide on the variant envelope and how variants compose into a template, see [Template Schema Guide](references/template-schema-guide.md).

## Channels

A variant's `channel` field selects which content schema applies. Pick the reference for the channel you are authoring.

| Channel | Variant `channel` | Reference |
|---|---|---|
| Email | `email` | [Email content schema](references/channel-email.md) |
| SMS | `sms` | [SMS content schema](references/channel-sms.md) |
| WhatsApp | `whatsapp` | [WhatsApp content schema](references/channel-whatsapp.md) |
| In-app Inbox | `inbox` | [Inbox content schema](references/channel-inbox.md) |
| Slack | `slack` | [Slack content schema](references/channel-slack.md) |
| Microsoft Teams | `ms_teams` | [MS Teams content schema](references/channel-ms-teams.md) |
| Android Push | `androidpush` | [Android push content schema](references/channel-androidpush.md) |
| iOS Push | `iospush` | [iOS push content schema](references/channel-iospush.md) |
| Web Push | `webpush` | [Web push content schema](references/channel-webpush.md) |

## Brand variables

Templates can reference tenant/brand properties. There are three shapes — use the right one for each case:

### 1. Reserved `$brand.*` keys

These are the only keys valid directly under `$brand.`. Any other key under `$brand.` will not resolve and will break preview rendering — put it under `$brand.properties.` instead (see below).

| Variable | Renders |
| --- | --- |
| `{{$brand.brand_id}}` | Tenant slug / id |
| `{{$brand.brand_name}}` | Tenant display name. **The key is `brand_name`, not `name`.** |
| `{{$brand.logo}}` | Tenant logo URL |
| `{{$brand.primary_color}}` | Primary brand color |
| `{{$brand.secondary_color}}` | Secondary brand color |
| `{{$brand.tertiary_color}}` | Tertiary brand color |
| `{{$brand.timezone}}` | Tenant timezone |
| `{{$brand.embedded_preference_url}}` | Brand-level embedded preference URL |
| `{{$brand.hosted_preference_domain}}` | Brand-level hosted preference domain |
| `{{$brand.blocked_channels}}` | List of channels blocked at the brand level |
| `{{$brand.social_links.<network>}}` | Brand social link. Built-in `<network>` keys: `x`, `twitter`, `facebook`, `instagram`, `linkedin`, `youtube`, `tiktok`, `discord`, `telegram`, `medium`, `website` |

### 2. Custom tenant properties — `$brand.properties.<key>`

Any property the customer adds on the tenant object that is **not** in the reserved list above is a custom property, and the correct shape is `{{$brand.properties.<key>}}`. Common examples:

- `{{$brand.properties.address}}`
- `{{$brand.properties.unsubscribe_url}}`
- `{{$brand.properties.support_url}}`
- `{{$brand.properties.support_email}}`

If you don't recognise the key from the reserved list, default to `$brand.properties.<key>`.

### 3. Per-recipient preference URLs (top-level `$`, not under `$brand`)

These are generated per recipient at run-time. They are top-level, not nested under `$brand`:

- `{{$embedded_preference_url}}`
- `{{$hosted_preference_url}}`

Do not write `{{$brand.$hosted_preference_url}}` or `{{$brand.embedded_preference_url}}` when you mean the per-recipient URL — those are different variables (the `$brand.embedded_preference_url` form refers to the brand-level config, not the recipient-specific URL).

### Common anti-patterns — never emit these

| Wrong | Correct |
| --- | --- |
| `{{$brand.name}}` | `{{$brand.brand_name}}` |
| `{{$brand.support_url}}` | `{{$brand.properties.support_url}}` |
| `{{$brand.unsubscribe_url}}` | `{{$brand.properties.unsubscribe_url}}` |
| `{{$brand.address}}` | `{{$brand.properties.address}}` |
| `{{$brand.$hosted_preference_url}}` | `{{$hosted_preference_url}}` (per-recipient) *or* `{{$brand.hosted_preference_domain}}` (brand config) — pick based on intent |

For the full multi-tenant variant model and per-tenant overrides, see [Multi-tenant Variants](references/multi-tenant-variants.md).

## Authoring Variants

Every variant must specify `channel`, `id`, `tenant_id`, `locale`, and `conditions` — even when not using multi-tenant or conditional features (use `null` where applicable). The `content` object is validated against the channel-specific schema.

Minimum shape:

```json
{
  "$schema": "https://schema.suprsend.com/template/v2/variant_schema.json",
  "channel": "email",
  "id": "default-en",
  "tenant_id": null,
  "locale": "en",
  "conditions": null,
  "content": { /* channel-specific — see channel reference */ }
}
```

See the [Template Schema Guide](references/template-schema-guide.md) for the variant envelope, selection rules, and complete examples.

For multi-variant patterns, see:

- [Multi-tenant Variants](references/multi-tenant-variants.md) — different content per tenant/brand
- [Multi-lingual Variants](references/multi-lingual-variants.md) — translation keys vs. per-locale variants

For the template syntax used inside content fields, see:

- [Handlebars Helpers](references/handlebars-helpers.md) — variables, conditionals, comparisons, date/array helpers. Default for every channel.
- [JSONNET Syntax](references/jsonnet-syntax.md) — alternative for Slack `body_block` and MS Teams `body_card` when `templating_language: "jsonnet"`.

## Related skills

- **`suprsend-workflow-schema`** — workflow delivery nodes (`send_email`, `send_multi_channel`, etc.) reference variants by `template` slug. Use it for the workflow shape that wraps these variants.
- **`suprsend-cli`** — `suprsend template push` / `pull` / `commit` / `get` / `list` are the commands that move variant JSON between your editor and a SuprSend workspace.
