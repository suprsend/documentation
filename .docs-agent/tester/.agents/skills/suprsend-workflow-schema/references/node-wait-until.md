# Wait Until Node

**Schema `node_type`:** `branch_waituntil`

> **Use `branch_waituntil` (not `delay`) whenever the wait depends on a real-world event.** Natural-language signals: *"after completion"*, *"after the call ends"*, *"once the user submits / finishes / pays / confirms"*, *"when X is done"*, *"after they sign up / verify / approve"*. In every case, the right pattern is a `branch_waituntil` on a `future_event` matching the completion event (and a timeout branch for the case where the event never arrives). Do not approximate the wait with a fixed or relative `delay` — the action's duration is variable and the message will fire mid-action.

## Documentation

# Wait Until

> Learn to use Wait Until node in workflow to halt until a condition or max time is met.

Wait Until is a conditional branch which halts the workflow until either the branch condition is met or the maximum wait duration is reached. It is most used for cases where sequential notifications need to be sent to users based on certain conditions, such as payment or task reminders.

## How wait until works?

Wait Until has 2 branches- **Condition** and **Max time**. The user proceeds through the branch that is satisfied first.

1. [Condition:](/docs/wait-until#conditions) User proceeds through this path when a condition is met, such as an event being triggered, user properties, or the event properties that initiated the workflow. In case of payment reminder, condition could be the event trigger of `user completing payment`.
2. [Max time:](/docs/wait-until#max-time) This is the maximum time the user can wait for the condition to satisfy until the next step should be executed. If a person reaches the maximum wait time without achieving any other conditions, they'll progress through this branch.


> **Note:**
  You can incorporate **multiple Wait Until** nodes in sequence to create a multi-step notification journey, where each notification is sent based on a specific condition being met.


## Conditions

You can add conditions on event properties, user properties, and action / event performed by user. It's important to note that conditions are evaluated when the workflow execution reaches "Wait Until" node, meaning any events performed before this point will not satisfy the condition branch.

Except for max time branch, all other branches are condition branches. To setup a condition, you can select the type of the condition and the expression defining the condition.

### Type: Event is performed

Here, the branch condition satisfies when a given event is received during the wait time. This type of condition is ideal for scenarios like reminders, where you want to avoid sending a reminder if the necessary action is completed within the wait time.

You can define the event name and apply conditions on event properties to filter and identify the exact event associated with the workflow. For instance, in a booking reminder scenario, If a user has multiple bookings, you can match the booking ID of the cancellation event with the booking ID of the original event to ensure the correct reminder is cancelled.


### Adding filter on event properties

Property condition is constructed as key, operator and value. You can add multiple conditions separated by `AND`, `OR`.

1. **Key:** It is the variable key in your wait until event properties.
2. **Operator:** you can use any of the below operators to compare key and value:

| Operator         | Description                                                                                                                                                                  |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `==`             | Key **is equal to** value. This is a case-sensitive check.                                                                                                                   |
| `!=`             | Key **is not equal to** value. This is a case-sensitive check.                                                                                                               |
| `>`              | Key **is greater than** value. Can be applied to integers, float values, or epoch timestamps.                                                                                |
| `>=`             | Key **is greater than or equal to** value. Can be applied to integers, float values, or epoch timestamps.                                                                    |
| `<`              | Key **is less than** value. Can be applied to integers and float values.                                                                                                     |
| `<=`             | Key **is less than or equal to** value. Can be applied to integers and float values.                                                                                         |
| `contains`       | Key should be a substring or a list item in an array.                                                                                                                        |
| `not contains`   | Key should not be a substring or match any list item in an array.                                                                                                            |
| `is empty`       | Evaluates to `true` if the key is missing, an empty string, or has a `null` value.                                                                                           |
| `is not empty`   | Key should be present and should not be an empty string or `null` value.                                                                                                     |
| `intersects`     | Evaluates to true if **any value** in the left array matches **any value** in the right array. Useful for checking overlaps between arrays.                                  |
| `not intersects` | Evaluates to true if **no values** in the left array match any values in the right array. It could be used in case of checking or filtering out any overlaps between arrays. |

3. **Value:** Value can be fixed (static value) or dynamic (evaluated dynamically from workflow data).

#### Fixed values

Fixed values can be added as:

1. **string**- enclose within double inverted commas as `"string"`

2. **number**- `1`, `1.2`

3. **boolean**- `true`, `false`

#### Dynamic values

Dynamic values are evaluated based on the data available at the node input along with actor, recipient or tenant properties. Refer below table for types of dynamic values and their respective syntax.

| Data Type         | Description                                                                                                                                                                                                                                                          | Referring this property in condition     |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| **Input Payload** | Includes data from your trigger payload and any data modified or added by nodes such as data transform, batch/digest, or webhook/fetch nodes before the branch node.                                                                                                 | Directly specify as `key` with no prefix |
| **Actor**         | Actor properties. In the case of an event trigger, `distinct_id` works as both actor and recipient. For an inline workflow trigger, it is the `distinct_id` in the actor object.                                                                                     | Add as `$actor.<property_key>`           |
| **Recipient**     | Recipient properties. It is the `distinct_id` in your event trigger or the key value defined in [override recipient](https://docs.suprsend.com/docs/override-recipient-list) field. For an inline workflow trigger, it is the `distinct_id` in the recipient object. | Add as `$recipient.<property_key>`       |
| **Tenant**        | Tenant properties. These include all properties of the `tenant_id` in your workflow trigger.                                                                                                                                                                         | Add as `$brand.<property_key>`           |

### Adding conditions on multiple events

You can add condition on multiple events separated by `OR` operator. Evaluation will pass if any of the conditions separated by `OR` is true.

## Max time

This branch will be executed if none of the condition branches are satisfied. This is where you'll add your send nodes in case of reminder workflows. You can either add a [Fixed delay](/docs/wait-until#fixed-delay) or [Dynamic delay](/docs/wait-until#dynamic-delay) in max time. Dynamic delays are computed using data in your event properties and can vary for each user. A good example of dynamic delay could be reminders where frequency is set by the user.

### Fixed delay

Fixed delay is defined in your workflow form as `**d **h **m **s` and it adds a fixed delay for all users.


Some examples of fixed delay are:

* Sending multiple payment or activity reminders at predetermined intervals. For instance, sending three payment reminders spaced 2 days apart from the last due date.
* Implementing conditional sends across multiple channels. for example, sending an approval notification via Inbox and scheduling an email to be sent one hour later if the approval is not received.

  [Smart channel routing](/docs/smart-delivery) is a better approach to solve this use case.

### Dynamic delay

In case of dynamic delay, delay duration is computed using the data from your event properties. Dynamic delays are helpful for reminders where the schedule is dictated by the user or when notification needs to be sent before the event or task due date.


Imagine you need to send task completion reminders, where users can specify a reminder frequency, such as every 6 hours until the task is finished. This frequency can differ for each task and user. Dynamic wait times effortlessly adapt to these unique preferences.

You can add duration key as a [JQ-expression](https://jqlang.github.io/jq/manual/). Below are some examples of how to add duration key in JQ format:

1. General format for duration key at parent level is `.duration_key`
2. If the duration key is a nested event property key like shown below, enter it in the format `.reminder.frequency`


  ```json theme={"system"}
  {
    "reminder": {
      "frequency": "6h"
    }
  }
  ```


Your duration key variable can be computed to either:

* An ISO-8601 timestamp (for example 2024-03-02T20:34:07Z) which must be a datetime in the future, or
* A relative duration unit, which can be
  * an integer like `50`, considered as duration in seconds.
  * an interval string defined as `**d **h **m **s`, where d = day, h = hour, m = minutes and s = seconds

> **Warning:**
  When the duration key specified is missing, or resolves to an invalid value, workflow execution will stop and corresponding error will be logged.

## Branch Structure

Wait Until uses the same `branches` array as the branch node but always has exactly 2 branches:
one condition branch (`is_default: false`) and one timeout branch (`is_default: true`).

### Branch item properties

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| name | string | Yes | The name of the Branch |
| description | string | null | No | Branch Description |
| ref | string | null | No | ref of the branch. Must be unique within a workflow across all nodes and branches |
| is_default | boolean | Yes | Whether this is the default branch. There can be only one default branch, and it must be the last branch in the list |
| is_terminal | boolean | No | Whether workflow terminates at the end of this branch |
| conditions | array | Yes |  |
| nodes | array | Yes | nodes inside the branch |

### Condition types

The condition branch supports these condition types:

- `future_event` — waits for a specific event to arrive
- `expression_v1` — evaluates conditions on existing data
- `delay` — timeout (used in the default branch)

### Future event condition properties

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| type | string | Yes |  |
| event_name | string | Yes |  |
| event_conditions | array | No |  |

### Delay condition (timeout) properties

The default branch uses a delay condition with the same schema as the delay node:

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| delay_type | string | Yes |  |
| value | string | No |  |
| relative_to | any | No |  |

## Example

```json
{
  "node_type": "branch_waituntil",
  "properties": {},
  "branches": [
    {
      "name": "Payment received",
      "is_default": false,
      "conditions": [
        {
          "type": "future_event",
          "event_name": "payment_completed",
          "event_conditions": []
        }
      ],
      "nodes": []
    },
    {
      "name": "Timeout after 48h",
      "is_default": true,
      "conditions": [
        { "type": "delay", "delay_properties": { "delay_type": "fixed", "value": "2d" } }
      ],
      "nodes": [
        { "node_type": "send_email", "properties": { "template": "payment-overdue" } }
      ]
    }
  ]
}
```

## Example: send a follow-up only after the action completes

The post-delivery sends fire only after `order_delivered` arrives, never before. The terminal timeout branch ends the workflow cleanly if delivery never confirms.

```json
{
  "node_type": "branch_waituntil",
  "name": "Wait for order_delivered",
  "properties": {},
  "branches": [
    {
      "name": "Delivered",
      "ref": "delivered",
      "is_default": false,
      "conditions": [
        {
          "type": "future_event",
          "event_name": "order_delivered",
          "event_conditions": [
            {
              "type": "expression_v1",
              "expression_v1": {
                "op": "AND",
                "args": [
                  { "variable_ns": "$future_event", "variable": "order_id", "op": "==", "value": "order_id" }
                ]
              }
            }
          ]
        }
      ],
      "nodes": [ /* post-delivery sends go here */ ]
    },
    {
      "name": "Timeout",
      "ref": "delivery_timeout",
      "is_default": true,
      "is_terminal": true,
      "conditions": [ { "type": "delay", "delay_properties": { "delay_type": "fixed", "value": "7d" } } ],
      "nodes": []
    }
  ]
}
```

## Terminating on timeout

The default branch in `branch_waituntil` represents the "event never arrived" path. In most flows, this is also where the workflow should end — there is no point continuing the post-event sequence for a user who never completed the action. Set `is_terminal: true` on the timeout branch to make this explicit.

```json
{
  "name": "Timeout",
  "ref": "no_response_timeout",
  "is_default": true,
  "is_terminal": true,
  "conditions": [ { "type": "delay", "delay_properties": { "delay_type": "fixed", "value": "24h" } } ],
  "nodes": [ /* optional last-ditch notification, then exit */ ]
}
```

Without `is_terminal: true`, the workflow falls through to whatever follows the `branch_waituntil` node — usually the post-completion sequence — which fires for users who timed out, contrary to intent.
