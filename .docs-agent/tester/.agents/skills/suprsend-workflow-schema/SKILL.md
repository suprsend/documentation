---
name: suprsend-workflow-schema
description: "JSON schema for authoring or editing SuprSend workflow definitions. Loads the schemas and examples needed to write valid workflow JSON. Use ONLY when the user wants the agent to create, modify, or edit a workflow (e.g. \"build a workflow that sends a welcome email\", \"add a 1h delay before the SMS step\", \"wire a branch on user plan\"). Do NOT load for documentation, lookup, or conceptual questions (\"how does batching work\", \"what is the batch node\", \"explain delivery nodes\") — load suprsend-docs-support for those."
metadata:
  author: "suprsend"
  category: "workflows"
---

SuprSend workflows define notification logic as a sequence of nodes. Each workflow requires a trigger (event or API) and at least one delivery node. Between trigger and delivery, you can add function, branch, and data nodes to build sophisticated notification journeys.

Workflows are defined as JSON conforming to the schema at `https://schema.suprsend.com/workflow/v1/schema.json`.

## Recipient model

A workflow runs for exactly one recipient — the `distinct_id` from the API trigger, or from the event's `distinct_id` (or its `override_recipients_*` override). Every delivery node in the workflow sends to that recipient. **Delivery nodes have no per-node recipient field.**

If a workflow needs to send to someone other than the trigger recipient, use one of these patterns:

| Need | Use | Notes |
| --- | --- | --- |
| Re-point the *entire* workflow to a different recipient based on event payload (e.g., approval flows where the actor should receive resolution updates instead of the approver) | `override_recipients_type` + `override_recipients_user_expr` (or `override_recipients_single_object_fields_expr`) at the workflow root | **Event-triggered workflows only** (`trigger_type=event`). Not available for `trigger_type=api`. See [Workflow Schema Guide](references/workflow-schema-guide.md) → Recipient overrides. |
| Send to a different recipient *mid-flow*, while continuing the parent flow for the original recipient (e.g., a buyer-triggered order workflow that also alerts the seller at one step) | `invokeworkflow` node with `recipient_selection: "expression"` and `recipient_expression` pointing at the new recipient | Works for both `event` and `api` triggers. The invoked workflow runs in parallel with its own recipient. See [Invoke Workflow](references/node-invoke-workflow.md). |
| Aggregate across recipients different from the workflow's trigger recipient (e.g., one digest per seller across many buyer-triggered orders) | A separate workflow triggered with the digest key as its recipient, invoked from the parent via `invokeworkflow` | Digest nodes batch on `(recipient, workflow_slug)`. A digest inside a buyer-triggered workflow will always batch per-buyer. See [Digest](references/node-digest.md). |

If a generated workflow sends to multiple distinct recipients across nodes and uses neither `override_recipients_*` nor `invokeworkflow`, it is wrong — every send will route to the trigger recipient.


For a complete guide on creating workflows using the JSON schema, see [Workflow Schema Guide](references/workflow-schema-guide.md).

## Minimum workflow

```json
{
  "$schema": "https://schema.suprsend.com/workflow/v1/schema.json",
  "name": "welcome-email",
  "category": "onboarding",
  "trigger_type": "event",
  "trigger_events": ["user_signed_up"],
  "tree": {
    "nodes": [
      { "node_type": "send_email", "properties": { "template": "welcome-email" } }
    ]
  }
}
```

A workflow needs `name`, `category`, `trigger_type`, and `tree` with at least one delivery node. The `properties.template` field on a delivery node refers to the template slug authored separately.

## Workflow Nodes

### Delivery Nodes

Send notifications to users. Every workflow must end with at least one delivery or HTTP API node.

| Node Type | Schema `node_type` | Description |
|---|---|---|
| Single Channel | `send_email`, `send_sms`, `send_whatsapp`, `send_inbox`, `send_mobile_push`, `send_webpush`, `send_slack`, `send_ms_teams` | Send via one channel |
| Multi-Channel | `send_multi_channel` | Send across multiple channels simultaneously |
| Smart Channel Routing | `send_smart_channel_routing` | Send sequentially across channels with delays until engagement |

See [Delivery Nodes Reference](references/node-delivery.md) for configuration details and schema.

### Function Nodes

Control timing and aggregation of notifications.

| Node Type | Schema `node_type` | Description |
|---|---|---|
| Delay | `delay` | Pause workflow for a fixed, dynamic, or relative duration |
| Batch | `batch` | Aggregate multiple triggers into one notification |
| Digest | `digest` | Send batched summary on a recurring schedule |
| Time Window | `timewindow` | Deliver only within specified day/time ranges |

See: [Delay](references/node-delay.md), [Batch](references/node-batch.md), [Digest](references/node-digest.md), [Time Window](references/node-timewindow.md)

### Branch Nodes

Route notifications through different paths based on conditions.

| Node Type | Schema `node_type` | Description |
|---|---|---|
| Branch | `branch` | If/else routing based on conditions |
| Wait Until | `branch_waituntil` | Pause until condition is met or timeout expires |

> When a branch is a terminal exit (rejection, timeout, no-response, failure), set `is_terminal: true` on the branch object. Without it, the workflow continues past the branch construct for that path — post-approval sends will fire for users who rejected, post-completion sends will fire for users who timed out. See [Branch](references/node-branch.md) → Terminating the workflow on a branch and [Wait Until](references/node-wait-until.md) → Terminating on timeout.

See: [Branch](references/node-branch.md), [Wait Until](references/node-wait-until.md)

### Data Nodes

Fetch, transform, or update data during workflow execution.

| Node Type | Schema `node_type` | Description |
|---|---|---|
| Fetch | `httpapi_fetch` | GET data from an external API |
| Webhook | `httpapi_webhook` | Call external API (GET/POST/PUT/PATCH/DELETE) |
| Data Transform | `transform` | Generate or modify variables using Handlebars or JSONNET |
| Invoke Workflow | `invokeworkflow` | Trigger another workflow as a step |
| Update User Profile | `userupdate` | Modify recipient or actor profile properties |

See: [Fetch](references/node-fetch.md), [Webhook](references/node-webhook.md), [Transform](references/node-transform.md), [Invoke Workflow](references/node-invoke-workflow.md), [User Update](references/node-user-update.md)

### List & Object Nodes

Manage user list memberships and object subscriptions.

| Node Type | Schema `node_type` | Description |
|---|---|---|
| Add User to List | `subscriberlistoperation_adduser` | Add recipient/actor to a list |
| Remove User from List | `subscriberlistoperation_removeuser` | Remove recipient/actor from a list |
| Subscribe to Object | `objectoperation_addsubscription` | Add user to an object subscription |
| Unsubscribe from Object | `objectoperation_removesubscription` | Remove user from an object subscription |

See: [List Operations](references/node-list-operations.md), [Object Operations](references/node-object-operations.md)

## Related skills

- **`suprsend-template-schema`** — delivery nodes reference templates by `template` slug. Use it to author the template content (variants per channel/locale/tenant) that the workflow sends.
- **`suprsend-cli`** — `suprsend workflow push` / `pull` / `commit` / `enable` / `disable` are the commands that move workflow JSON between your editor and a SuprSend workspace.
