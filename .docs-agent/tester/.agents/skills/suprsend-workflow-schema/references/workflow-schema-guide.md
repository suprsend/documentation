# Workflow Schema Guide

Create, understand, and modify SuprSend workflows using the JSON schema.

**Schema URL:** `https://schema.suprsend.com/workflow/v1/schema.json`

## Workflow Structure

A workflow JSON has top-level metadata and a `tree` containing an array of `nodes`. Nodes execute sequentially in the order they appear in the array.

```json
{
  "$schema": "https://schema.suprsend.com/workflow/v1/schema.json",
  "name": "payment-reminder",
  "description": "Send payment reminder with escalation",
  "category": "billing",
  "trigger_type": "event",
  "trigger_events": ["payment_due"],
  "tree": {
    "nodes": [
      { "node_type": "delay", "properties": { "delay_type": "fixed", "value": "1h" } },
      { "node_type": "send_email", "properties": { "template": "payment-reminder-email" } }
    ]
  }
}
```

## Top-Level Properties

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| $schema | string | No |  |
| name | string | Yes | Workflow name |
| description | string | null | No | Workflow description |
| category | string | Yes | Preference category slug |
| trigger_type | string | Yes | trigger type |
| trigger_events | array | null | No | Array of event names that can trigger this workflow |
| tags | array | null | No | optional tags for workflow |
| ratelimit | object | null | No | ratelimit for a workflow/recipient. [count=2 in window=30d] |
| conditions | array | null | No | trigger workflow only if these conditions satisfy |
| override_recipients_type | string | null | No | override recipients using trigger payload. (applicable only if trigger_type=event) |
| override_recipients_user_expr | string | null | No | a jq-expression to evaluate new recipients of type user (if override_recipients_type=user) |
| override_recipients_single_object_fields_expr | object | null | No | overrides original recipient with an object. object-type and id are evaluated using jq-expr (if override_recipients_type=single_object_fields) |
| override_actor_user_expr | string | null | No | a jq-expression to evaluate actor. (applicable only if trigger_type=event) |
| override_tenant_expr | string | null | No | a jq-expression to evaluate tenant. (applicable only if trigger_type=event) |
| tree | object | Yes |  |

### Required fields

- `name`, `category`, `trigger_type`, `tree`
- When `trigger_type` is `"event"`, `trigger_events` is also required

### Trigger type values

- `event`
- `api`

### Recipient overrides

For `trigger_type=event` workflows, the workflow's recipient, actor, and tenant can be re-derived from the event payload at trigger time. This is the standard pattern when the user who initiates the event is not the one who should receive the notification (for example: `comment_added` events where the actor commented and the recipient is the resource owner). See the [Override Recipient docs page](https://docs.suprsend.com/docs/override-recipient-list) for the full reference.

| Field | When to use |
| --- | --- |
| `override_recipients_type: "user"` + `override_recipients_user_expr` | Re-point recipient to a user identified by a jq-expression against the event payload (e.g., `.recipient` or `.resource.owner_id`). |
| `override_recipients_type: "single_object_fields"` + `override_recipients_single_object_fields_expr` | Re-point recipient to an object (object_type + id) identified by jq-expressions. |
| `override_actor_user_expr` | Re-derive the actor from event payload. |
| `override_tenant_expr` | Re-derive the tenant from event payload. |

**Constraint:** All `override_*` fields apply only when `trigger_type=event`. They are ignored on API-triggered workflows.

**Scope:** These fields re-point the *entire* workflow run. They cannot send some nodes to recipient A and others to recipient B in the same run — for that, use [`invokeworkflow`](node-invoke-workflow.md).

#### Example: notify the resource owner, not the commenter

```json
{
  "$schema": "https://schema.suprsend.com/workflow/v1/schema.json",
  "name": "comment-added-owner-notice",
  "category": "collaboration",
  "trigger_type": "event",
  "trigger_events": ["comment_added"],
  "override_recipients_type": "user",
  "override_recipients_user_expr": ".resource.owner_id",
  "override_actor_user_expr": ".commenter_id",
  "tree": {
    "nodes": [
      { "node_type": "send_email", "properties": { "template": "comment-added-owner" } }
    ]
  }
}
```

## Node Types

Every node in the `tree.nodes` array has a `node_type` field. Valid types:

- `delay`
- `timewindow`
- `batch`
- `digest`
- `httpapi_webhook`
- `httpapi_fetch`
- `send_multi_channel`
- `send_smart_channel_routing`
- `send_mobile_push`
- `send_email`
- `send_sms`
- `send_whatsapp`
- `send_inbox`
- `send_webpush`
- `send_slack`
- `send_ms_teams`
- `transform`
- `invokeworkflow`
- `userupdate`
- `subscriberlistoperation_adduser`
- `subscriberlistoperation_removeuser`
- `objectoperation_addsubscription`
- `objectoperation_removesubscription`
- `branch`
- `branch_waituntil`

### Common node fields

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| node_type | string | Yes | The type of the Node |
| name | string | null | No | The name of the Node |
| description | string | null | No | Node Description |
| ref | string | null | No | ref of the Node. Must be unique within a workflow across all nodes and branches |
| properties | object | null | Yes |  |
| branches | array | No |  |

## How Nodes Connect

- Nodes in the `tree.nodes` array execute **sequentially** from first to last.
- **Branch nodes** (`branch`, `branch_waituntil`) contain a `branches` array. Each branch has its own `nodes` array for the sub-workflow within that branch.
- After all branches of a branch node complete, execution continues with the next node in the parent array.
- Every workflow must include at least one **delivery node** (`send_*`) or HTTP API node.

## Common Workflow Patterns

### Simple: delay then send

```json
{
  "tree": {
    "nodes": [
      { "node_type": "delay", "properties": { "delay_type": "fixed", "value": "1h" } },
      { "node_type": "send_email", "properties": { "template": "reminder-email" } }
    ]
  }
}
```

### Batch + transform + send (aggregate notifications)

```json
{
  "tree": {
    "nodes": [
      { "node_type": "batch", "properties": { "mode": "accumulate_all", "window_type": "fixed", "fixed_window": "1h" } },
      { "node_type": "transform", "properties": { "variables": [{ "key": "summary", "value_lang": "handlebars", "value": "You have  new updates" }] } },
      { "node_type": "send_multi_channel", "properties": { "template": "activity-digest", "channels": ["email", "inbox"] } }
    ]
  }
}
```

### Conditional branching (route by user segment)

```json
{
  "tree": {
    "nodes": [
      {
        "node_type": "branch",
        "properties": {},
        "branches": [
          {
            "name": "VIP users", "is_default": false,
            "conditions": [{ "type": "expression_v1", "expression_v1": { "op": "AND", "args": [{ "variable_ns": "$recipient", "variable": "plan", "op": "==", "value": "enterprise" }] } }],
            "nodes": [{ "node_type": "send_smart_channel_routing", "properties": { "template": "vip-alert", "success": "seen" } }]
          },
          {
            "name": "Default", "is_default": true,
            "conditions": [{ "type": "expression_v1", "expression_v1": { "op": "AND", "args": [] } }],
            "nodes": [{ "node_type": "send_email", "properties": { "template": "standard-alert" } }]
          }
        ]
      }
    ]
  }
}
```

### Wait-until reminder loop (send if user hasn't acted)

```json
{
  "tree": {
    "nodes": [
      { "node_type": "send_email", "properties": { "template": "payment-due" } },
      {
        "node_type": "branch_waituntil",
        "properties": {},
        "branches": [
          {
            "name": "Payment received", "is_default": false,
            "conditions": [{ "type": "future_event", "event_name": "payment_completed", "event_conditions": [] }],
            "nodes": []
          },
          {
            "name": "Timeout", "is_default": true,
            "conditions": [{ "type": "delay", "delay_properties": { "delay_type": "fixed", "value": "2d" } }],
            "nodes": [{ "node_type": "send_email", "properties": { "template": "payment-overdue" } }]
          }
        ]
      }
    ]
  }
}
```

## Duration Format

Used across delay, batch, digest, and ratelimit properties.

Pattern: `^(\d+[dhms])+$`

Examples: `30s`, `5m`, `1h30m`, `2d`, `1d12h30m`

## Condition Expressions

Conditions use the `expression_v1` format with an AND/OR operator and comparison args:

```json
{
  "type": "expression_v1",
  "expression_v1": {
    "op": "AND",
    "args": [
      { "variable": "amount", "op": ">=", "value": "100" },
      { "variable_ns": "$recipient", "variable": "plan", "op": "==", "value": "premium" }
    ]
  }
}
```

### Variable namespaces

| Namespace | Data Source |
|---|---|
| *(empty string)* | Input payload — data from trigger event properties |
| `$actor` | Properties of the user who performed the action |
| `$recipient` | Properties of the user receiving the notification |
| `$brand` | Properties of the tenant/brand |
| `$organization` | Organization-level properties |
| `$future_event` | Properties of a future event (used in wait-until conditions) |

### Comparison operators

- `==`
- `!=`
- `>`
- `>=`
- `<`
- `<=`
- `EMPTY`
- `NON_EMPTY`
- `CONTAINS`
- `NOT_CONTAINS`
- `ARRAY_INTERSECTS`
- `NOT_ARRAY_INTERSECTS`
- `DATETIME_EQUALS`
- `DATETIME_LT`
- `DATETIME_GT`

## Validation Rules

- Every workflow must have `name`, `category`, `trigger_type`, and `tree`
- `tree.nodes` must contain at least one delivery node (`send_*`) or HTTP API node
- Branch nodes must have exactly one default branch (`is_default: true`) as the last item
- `branch_waituntil` must have exactly 2 branches: one condition branch and one timeout (default) branch
- Node `ref` values must be unique across the entire workflow (nodes and branches)

## Schema References

| Schema | URL |
|---|---|
| Main workflow | `https://schema.suprsend.com/workflow/v1/schema.json` |
| Tree / nodes | `https://schema.suprsend.com/workflow/v1/tree_schema.json` |
| Fragments | `https://schema.suprsend.com/workflow/v1/fragment_schema.json` |
| Send nodes | `https://schema.suprsend.com/workflow/v1/node_send_schema.json` |
| Branch nodes | `https://schema.suprsend.com/workflow/v1/node_branch_schema.json` |
| Batch node | `https://schema.suprsend.com/workflow/v1/node_batch_schema.json` |
| Digest node | `https://schema.suprsend.com/workflow/v1/node_digest_schema.json` |
| Time window | `https://schema.suprsend.com/workflow/v1/node_timewindow_schema.json` |
| HTTP API nodes | `https://schema.suprsend.com/workflow/v1/node_httpapi_schema.json` |
| Other functions | `https://schema.suprsend.com/workflow/v1/node_other_funcs_schema.json` |
| List operations | `https://schema.suprsend.com/workflow/v1/node_subscriberlistoperation_schema.json` |
| Object operations | `https://schema.suprsend.com/workflow/v1/node_objectoperation_schema.json` |
