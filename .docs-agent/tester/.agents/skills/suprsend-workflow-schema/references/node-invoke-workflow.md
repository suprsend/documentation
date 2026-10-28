# Invoke Workflow Node

**Schema `node_type`:** `invokeworkflow`

## When to use

Use `invokeworkflow` to trigger a workflow from within another workflow. The two primary use cases are:

1. **Multi-recipient flows** — the parent workflow sends to recipient A, and at one or more points needs to also notify recipient B (e.g., a buyer-triggered order workflow that also alerts the seller; a comment workflow that also notifies the resource owner). The invoked workflow runs in parallel for the second recipient, so the parent keeps running for the first.
2. **Escalation** — if a team member doesn't take action within a window, invoke a separate workflow with the manager as recipient.

`invokeworkflow` is **required** (not `override_recipients_*`) when:

- The workflow is `trigger_type=api` — overrides are event-only.
- The same run needs to send to multiple distinct recipients — overrides re-point the whole run, not individual nodes.
- A digest / batch needs to aggregate across a key other than the parent's trigger recipient — see [Digest](node-digest.md).

## Documentation

# Invoke Workflow

> Trigger another workflow as a step in running workflow.

Use this node to trigger a workflow from within another workflow. It is typically used when the recipient list or data context changes between workflow steps. A common example is escalation workflows, where if a team member doesn't take action, the workflow escalates to notify their manager.

The payload for the triggered workflow is dynamically computed using data from the current workflow run. All fields support variables in [JSONNET](https://jsonnet.org/ref/language.html) format.


## Constructing Workflow Payload

### Recipient

Recipient refers to the recipient of the target workflow. It can be:

* The current workflow's **recipient** or **actor**

* Any key from the node's **input data**, including data added or modified during the workflow run (for example from fetch or webhook nodes).

> **Note:**
  📘 Please note Data modifications after a batch or digest node will not affect the invoke node's variables, which means `$batched...` variables will not be available in this node's input.


You can refer to input data variables in JSONNET format, prefixed by `data` key. The same format is followed for adding variable in actor and data field as well. Following data types are available in workflow:

| Data Type     | Referring in JSONNET                        | Description                                                                                                                                                                                                                          |
| ------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Input Payload | pass as `data.<property_key>`               | This includes the data from your trigger payload and any data modified or added by nodes such as data transform, or webhook/fetch nodes before the invoke node.                                                                      |
| Actor         | pass as `data["$actor"].<property_key>`     | Actor properties. In case of event trigger, `distinct_id` works both as actor and recipient and for inline workflow trigger, it is the `distinct_id` in actor object.                                                                |
| Recipient     | pass as `data["$recipient"].<property_key>` | Recipient properties. It is the `distinct_id` in your event trigger or the key value defined in [override recipient](/docs/override-recipient-list) field. For inline workflow trigger, it is the `distinct_id` in recipient object. |
| Tenant        | pass as`data["$brand"].<property_key>`      | Tenant properties corresponding to the tenant_id passed in workflow trigger.                                                                                                                                                        |

### Actor

The actor defines the user who performed the action in the target workflow. It can be:

* The current workflow's **actor** or **recipient**.

* Any key from the node's **input data**, referred in the same format as in the [recipient](/docs/invoke-workflow#recipient) field.

### Data

This defines the data context for the target workflow, which is used to render templates and workflow variables. By default, data from the current workflow run is passed.

* To exclude the current workflow data, uncheck the `Append current workflow execution data` option.

* Additional data can be provided in the data JSON field, using the node's input data in JSONNET format, referred in the same format as in the [recipient](/docs/invoke-workflow#recipient) field.

#### Merge strategy

We use a shallow merge strategy to combine extra input data (defined in data JSON field) with the current workflow execution data. If the same key exists in both, the value from data JSON field will override the value in existing workflow data.

***

## Schema Properties

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| workflow | string | Yes | slug of workflow to invoke |
| actor_selection | string | null | No | where to pick actor from for invoke-workflow payload |
| actor_expression | string | No | if actor_selection=expression, a JSONNET expression to derive actor at runtime |
| recipient_selection | string | Yes | where to pick recipient from for invoke-workflow payload |
| recipient_expression | string | No | if recipient_selection=expression, a JSONNET expression to derive recipient at runtime |
| data | string | null | No | JSONNET expression to derive data field for invoke-workflow payload |
| append_current_run_data | boolean | No | should current workflow-run data be merged with the data field |

### Recipient selection values

- `recipient`
- `actor`
- `expression`

### Actor selection values

- `null`
- ``
- `recipient`
- `actor`
- `expression`

## Example: escalation

```json
{
  "node_type": "invokeworkflow",
  "properties": {
    "workflow": "escalation-workflow",
    "recipient_selection": "expression",
    "recipient_expression": "data.manager_id",
    "actor_selection": "recipient",
    "append_current_run_data": true
  }
}
```

## Example: notify a different recipient mid-flow

The parent workflow keeps running for the original (buyer) recipient. The `order-seller-alert` workflow runs independently with `seller_id` as its recipient.

```json
{
  "node_type": "invokeworkflow",
  "name": "Notify Order Seller",
  "properties": {
    "workflow": "order-seller-alert",
    "recipient_selection": "expression",
    "recipient_expression": "data.seller_id",
    "append_current_run_data": true
  }
}
```
