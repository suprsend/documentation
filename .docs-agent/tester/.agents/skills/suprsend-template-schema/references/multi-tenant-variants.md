# Multi-tenant Variants

Use a per-tenant variant when a template needs different content (subject line, copy, branding, attachments) for different tenants of the same workflow. Set the variant's `tenant_id` to the tenant slug; leave it `null` for the default fallback.

Selection: when a template is sent for a specific `tenant_id`, SuprSend prefers the variant matching that `tenant_id` over the `tenant_id: null` variant (for the same channel + locale + condition match). If no tenant-specific variant exists, the `null` variant is used.

For tenant *variables* (logo, colors, properties) that just need substituting into shared content, prefer using `{{$brand.<property>}}` inside a single variant.

## Reserved `$brand.*` keys

These keys live directly under `$brand.`. Anything not in this list is a custom property and must be referenced as `{{$brand.properties.<key>}}` — see [Custom tenant properties](#custom-tenant-properties) below.

| Variable | Renders |
| --- | --- |
| `{{$brand.brand_id}}` | Tenant slug / id |
| `{{$brand.brand_name}}` | Tenant display name. **The key is `brand_name`, not `name`.** |
| `{{$brand.logo}}` | Tenant logo URL |
| `{{$brand.primary_color}}` | Primary brand color (hex) |
| `{{$brand.secondary_color}}` | Secondary brand color (hex) |
| `{{$brand.tertiary_color}}` | Tertiary brand color (hex) |
| `{{$brand.timezone}}` | Tenant timezone (IANA, e.g. `America/Los_Angeles`) |
| `{{$brand.embedded_preference_url}}` | Brand-level embedded preference URL |
| `{{$brand.hosted_preference_domain}}` | Brand-level hosted preference domain |
| `{{$brand.blocked_channels}}` | List of channels blocked at the brand level |

### Social links

| Variable | Renders |
| --- | --- |
| `{{$brand.social_links.x}}` | X (formerly Twitter) profile URL |
| `{{$brand.social_links.twitter}}` | Twitter profile URL (legacy alias for `x`) |
| `{{$brand.social_links.facebook}}` | Facebook page URL |
| `{{$brand.social_links.instagram}}` | Instagram profile URL |
| `{{$brand.social_links.linkedin}}` | LinkedIn profile / company page URL |
| `{{$brand.social_links.youtube}}` | YouTube channel URL |
| `{{$brand.social_links.tiktok}}` | TikTok profile URL |
| `{{$brand.social_links.discord}}` | Discord invite / server URL |
| `{{$brand.social_links.telegram}}` | Telegram channel URL |
| `{{$brand.social_links.medium}}` | Medium publication URL |
| `{{$brand.social_links.website}}` | Tenant website URL |

> **Anything not in the reserved tables above is a custom property and must be referenced as `{{$brand.properties.<key>}}` — never `{{$brand.<key>}}` directly.** Common customer-added properties like `address`, `unsubscribe_url`, `support_url`, `support_email` are *not* reserved; they live under `$brand.properties.`. Authoring `{{$brand.support_url}}` directly will not resolve.

## Custom tenant properties

For any property not in the reserved list above, use `{{$brand.properties.<key>}}`:

- `{{$brand.properties.address}}`
- `{{$brand.properties.unsubscribe_url}}`
- `{{$brand.properties.support_url}}`
- `{{$brand.properties.support_email}}`

In JSONNET templates, the equivalent shapes are `data["$brand"].<reserved_key>` and `data["$brand"].properties.<custom_key>`.

## Per-recipient preference URLs (not under `$brand`)

These are generated per recipient at run-time and live at the top level — not nested under `$brand`:

- `{{$embedded_preference_url}}` — per-recipient embedded preference URL
- `{{$hosted_preference_url}}` — per-recipient hosted preference / unsubscribe URL

`{{$brand.embedded_preference_url}}` and `{{$brand.hosted_preference_domain}}` are *different* variables — they refer to the brand-level configuration, not the recipient-specific URL. Pick based on intent.

## Documentation

```
# Tenant Templates

> Learn how to use tenant components and variables in your notification templates.

## Overview

Use tenant properties in templates to dynamically render tenant-specific content. One template works for all tenants-SuprSend replaces variables with tenant-specific values at runtime.

## Email Template Design

Tenant variables in other channels are referred as `$brand.<property>` in templates. For email template designer, you get pre-built tenant component to automatically get the branded header, footer, and buttons for a tenant.


  **Find and add tenant component**
    Inside email template designer, find tenant component in the right side content menu and add it to your template.

    

    
  

  **Select relevant block type**
    Select relevant block type (header, footer, buttons) from the right panel.

    

    
  

  **Customize the selected block**
    Tenant blocks use the tenant's primary color and logo by default. Click any block to customize colors, padding, and styling from the right panel. To insert tenant variables anywhere in a block, use `{{$brand.<property>}}`. See the full list of [available variables](/docs/tenant-templates#available-variables).
  


## Customizing other channels templates

You can customize other channels using tenant variables as `{{$brand.<property>}}` in the template.

## Available Variables

Use `{{$brand.<property>}}` in handlebars templates and `data["$brand"].<property>` in JSONNET templates. Variables are replaced at runtime with the tenant’s properties (from the `tenant_id` passed when sending).

**Basic**

| Variable            | Description                     |
| ------------------- | ------------------------------- |
| `$brand.brand_name` | Display name for the tenant.    |
| `$brand.logo`       | URL of the tenant’s logo image. |

**Colors**

| Variable                 | Description                  |
| ------------------------ | ---------------------------- |
| `$brand.primary_color`   | Primary brand color (hex).   |
| `$brand.secondary_color` | Secondary brand color (hex). |
| `$brand.tertiary_color`  | Tertiary brand color (hex).  |

**Social links**

| Variable                        | Description                   |
| ------------------------------- | ----------------------------- |
| `$brand.social_links.website`   | Website URL.                  |
| `$brand.social_links.facebook`  | Facebook profile or page URL. |
| `$brand.social_links.twitter`   | Twitter/X profile URL.        |
| `$brand.social_links.instagram` | Instagram profile URL.        |

**Custom properties**

| Variable                  | Description                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------- |
| `$brand.properties.<key>` | Any custom property set on the tenant (for example `$brand.properties.support_email`). |
```
