# Slack Content Schema

For variants with `channel: "slack"`.

**Schema URL:** `https://schema.suprsend.com/template/v2/channel/slack_schema.json`

## Fields

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| $schema | string | No |  |
| templating_language | string | No |  |
| body_type | string | Yes |  |
| body_text | string | No | message body if body_type='text' |
| body_block | string | No | message body if body_type='block' |

`body_type` is required. When `body_type` is `text`, `body_text` is required. When `body_type` is `block`, `body_block` is required.

### `templating_language` values

- `handlebars`
- `jsonnet`

- `handlebars` — string interpolation in `body_text` / `body_block` content.
- `jsonnet` — evaluate `body_block` as a Jsonnet expression that produces the Slack `blocks` JSON.

### `body_type` values

- `text`
- `block`

- `text` — `body_text` is a plain message string.
- `block` — `body_block` is a JSON string conforming to Slack's [Block Kit](https://api.slack.com/block-kit) spec.

## Default mode: JSONNET (Block Kit)

**For all new Slack templates, generate JSONNET by default.** Block Kit is Slack's native rich format — text mode wastes channel capabilities.

Use Text mode ONLY when:

- User explicitly asks for "plain text" or "simple text"
- Notification is a true one-liner with no CTA
- Migrating an existing text template

Use JSONNET if ANY of these are present:

- CTA / action link → button block
- 2+ sections → section blocks + divider
- Key-value data → fields array
- Recipient/tenant personalization
- Batched/digest events → rich_text_list

### Critical format rule

JSONNET output MUST be wrapped in `{ "blocks": [...] }`. The bare-array format `[{...}, {...}]` will fail — Slack's API rejects unwrapped arrays.

✅ Correct:

```jsonnet
{
  "blocks": [
    { "type": "section", "text": { "type": "mrkdwn", "text": "Hello" } }
  ]
}
```

❌ Incorrect:

```jsonnet
[
  { "type": "section", "text": { "type": "mrkdwn", "text": "Hello" } }
]
```

## Co-pilot output rules

When generating JSONNET for Slack, ALWAYS output:

1. The JSONNET template wrapped in `{ "blocks": [...] }`
2. Mock data JSON in a separate code block
3. The variant config: `{ "templating_language": "jsonnet", "body_type": "block" }`

NEVER output bare-array format `[ {...} ]`.

NEVER mix Handlebars `{{ }}` and JSONNET in the same template.

## Examples

### Plain text message

```json
{
  "body_type": "text",
  "body_text": "Build failed for {{ repo }} on branch {{ branch }} — {{ commit.author }} broke main"
}
```

### Block Kit message

```json
{
  "body_type": "block",
  "body_block": "{\"blocks\":[{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"*Build failed* in {{ repo }}\"}},{\"type\":\"actions\",\"elements\":[{\"type\":\"button\",\"text\":{\"type\":\"plain_text\",\"text\":\"View logs\"},\"url\":\"{{ build.log_url }}\"}]}]}"
}
```

### Jsonnet-templated blocks

```json
{
  "templating_language": "jsonnet",
  "body_type": "block",
  "body_block": "{ \"blocks\": [ { \"type\": \"section\", \"text\": { \"type\": \"mrkdwn\", \"text\": \"*Build failed* in \" + data.repo } }, { \"type\": \"actions\", \"elements\": [ { \"type\": \"button\", \"text\": { \"type\": \"plain_text\", \"text\": \"View logs\" }, \"url\": data.build.log_url } ] } ] }"
}
```

## Documentation

```
# Slack

> Design Slack notification templates using the Text editor for simple messages or the JSONNET editor for rich Block Kit layouts.

The Slack editor supports two modes: a **Text** editor for simple messages, and a **JSONNET** editor for rich [Block Kit](https://api.slack.com/block-kit) layouts with buttons, images, and structured sections.


> **Note:**
  To send Slack notifications, you need a Slack vendor integrated with SuprSend. See [Slack vendor integration](/docs/slack) for setup.


## Slack fields

**Text mode** - a single text field. Supports [Handlebars](/docs/handlebars-helpers) variables (`{{variable_name}}`). Use triple braces `{{{url}}}` for URLs with special characters.

**JSONNET mode** - a code editor that outputs [Slack Block Kit](https://api.slack.com/block-kit) JSON. Variables use `data.key` syntax (not Handlebars). Design visually in the [Block Kit Builder](https://app.slack.com/block-kit-builder/) first, then adapt the JSON into JSONNET. See the full [JSONNET reference](/docs/jsonnet-templates) for syntax, examples, and debugging.

> **Warning:**
  Slack JSONNET templates must be wrapped in `{"blocks": [...]}`. A bare array of blocks will not render - see the [JSONNET reference](/docs/jsonnet-templates#slack-block-kit-examples) for the correct shape.


<Tip>
  **AI prompt - convert text to Block Kit:** *"Convert this Slack notification into Block Kit JSON: \[paste message]. Variables: \[list]. Return valid JSON I can adapt into JSONNET for SuprSend (replacing values with data.key)."*
</Tip>

<Tip>
  **AI prompt - debug JSONNET:** *"Fix this JSONNET error from the SuprSend Slack editor. Error: \[paste error]. Code: \[paste JSONNET]. Variables are accessed as data.key or data\['\$special_key']."*
</Tip>

<Info>
  You can switch between Text and JSONNET at any time. Content is saved independently for each mode.
</Info>

## Adding dynamic content

**In Text mode** - type `{{` for auto-suggestions. Standard Handlebars syntax:

* `{{order_id}}` - top-level variable
* `{{order.address.city}}` - nested variable
* `{{{tracking_url}}}` - URL (avoid escaping)
* `{{$recipient.name}}` - recipient property
* `{{$brand.brand_name}}` - tenant property

**In JSONNET mode** - variables use `data.key` syntax. See [JSONNET variable reference](/docs/jsonnet-templates#variable-syntax) for the full table.

For conditionals, loops, and helpers in Text mode, see [Handlebars Helpers](/docs/handlebars-helpers).

> **Warning:**
  If a variable cannot be rendered at send time (missing or mismatched data), SuprSend discards the Slack notification for that user. Other channels in the same template group are still sent.


## Preview and test

**Text mode** - the right panel shows a Slack message preview. It does not update automatically - **refresh the page** to see the latest changes.

**JSONNET mode** - preview is not available in the editor. Click **View on Slack Builder** to render and validate your Block Kit output in Slack's [Block Kit Builder](https://app.slack.com/block-kit-builder/).

Click **Test** in the top-right corner to send a real Slack message. This uses the **live version** - commit your changes before testing. See [Testing a Template](/docs/templates#test) for the full guide.

## Commit

Click **Commit** in the top bar to publish the current draft as a new live version. Add an optional description for versioning.

## Common patterns


  ### Thread-aware notifications
    Slack automatically threads messages sent to the same channel with the same `thread_ts`. Pass a consistent `thread_ts` in your trigger payload to keep related messages threaded.
  

  ### Mentioning users
    Use `<@SLACK_USER_ID>` to @mention a user. Pass the ID as a variable: `<@{{assignee_slack_id}}>`.
  

  ### Linking to resources
    Slack uses `<URL|display text>` syntax. In JSONNET: `"*<" + data.url + "|" + data.title + ">*"`.
  

  ### Emoji
    Use `:emoji_name:` syntax (for example, `:white_check_mark:`, `:warning:`).
  


## Frequently asked questions


  ### Text or JSONNET - which should I use?
    **Default to JSONNET.** Use Text only for one-liner alerts with no CTA; use JSONNET for everything else.
  

  ### How do I validate my Block Kit JSON?
    **JSONNET is not valid JSON — you cannot paste it directly into Block Kit Builder.** Use one of these:

  1. Click **Load Preview** in the SuprSend JSONNET editor.
  2. For external review: replace every `data.key` with its mock value, resolve all `+` concatenations, ensure output is wrapped in `{ "blocks": [...] }`, then paste into Block Kit Builder.

  Slack silently drops invalid blocks — always validate before committing.
  

  ### Why isn't my Slack template rendering?
    The most common reason is missing the `{"blocks": [...]}` wrapper. The SuprSend JSONNET editor only accepts the object form - a bare array (`[{...}]`) will not work. Wrap all your blocks inside a top-level object with a `blocks` key.
  

  ### What's the message length limit?
    Slack truncates messages over 4000 characters. For batched notifications with many items, show the top 5-10 and add a "View all" button.
  

  ### What formatting does Slack support?
    Slack uses `mrkdwn`, not standard Markdown. Bold: `*text*`, italic: `_text_`, strikethrough: `~text~`, code: triple backticks.
  

  ### What happens if a variable is missing at send time?
    SuprSend discards the Slack notification for that user. Other channels in the same template group are still sent.
```
