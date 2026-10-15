# List Operation Nodes

## Add User to List

**Schema `node_type`:** `subscriberlistoperation_adduser`

### Documentation

# Add User to list

> Dynamically add users to list within a workflow.

You can use this node to dynamically add recipient or actor in the list. This is one of the ways to create user segment based on an event or action. For example, when someone registers for an event, you can send them a confirmation email and at the same time, add them to a list to send them reminder messages or announcements related to the event.


### Creating list dynamically within workflow

You can either add users to an existing list or create the list on the fly using workflow input data. Dynamic list are defined in handlebars format as `{{...}}`.

List will only be created if the `Create list if it doesn't exist` setting is ON.

One common use case of creating list dynamically is when you need to create different lists based on user topic subscription. for example, there are multiple events happening and you want to create a separate list for each event. List ID in such case can be `{{event_id}}_subscribers` and List name `{{event_name}} - subscribers`.

> **Warning:**
  Please note that list ID only supports following characters- \`a-z,0-9,-,_\`. Ensure that list_id variable resolves to a valid format; otherwise, list creation will fail. 🚧


### Lists vs. Objects for topic subscriptions

* [Lists](/docs/lists) are ideal for one-time broadcasts to large user groups with high throughput (up to 1000 notifications/second). Example: Sending announcements or updates to all users subscribed to a particular event.

* [Objects](/docs/objects) are better for reusable topic subscriptions when additional workflows need to be triggered for the same subscribers. Example: Notifying team members or running nested workflows for hierarchical subscribers.

***

## Remove User from List

**Schema `node_type`:** `subscriberlistoperation_removeuser`

### Documentation

# Remove User from list

> Dynamically remove users from list within a workflow.

You can use this node to dynamically remove recipient or actor from the list. You can use it for use cases like when someone unsubscribes from an event or completes an action, you can remove them from the notification list to stop sending them further alerts.


### Compute List ID at runtime

You can either add users to a pre-defined list or dynamically render list ID during workflow execution. Dynamic list are defined in handlebars format as `{{...}}`.

One common use-case of computing list ID dynamically is when you have different lists based on user topic subscription. For example, there are multiple events happening and you have separate list for each event. List ID in such case can be `{{event_id}}_subscribers` and List name `{{event_name}} - subscribers`.

> **Warning:**
  There should be an existing list with the ID computed during trigger else this action will fail.


### Lists vs. Objects for topic subscriptions

* [Lists](/docs/lists) are ideal for one-time broadcasts to large user groups with high throughput (up to 1000 notifications/second). Example: Sending announcements or updates to all users subscribed to a particular event.

* [Objects](/docs/objects) are better for reusable topic subscriptions when additional workflows need to be triggered for the same subscribers. Example: Notifying team members or running nested workflows for hierarchical subscribers.

***

## Schema Properties (shared)

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| is_list_id_dynamic | boolean | No | Is list_id a static literal or a handlebars expression |
| list_id | string | Yes | static literal OR a handlebars expression (if dynamic) |
| create_list_if_missing | boolean | No | applicable when op=add_user. Should list be created if it doesn't exist? |
| list_name | string | No | applicable when op=add_user & create_list_if_missing=true. A handlebars expression to derive list-name |
| user_selection | array | Yes |  |

### User selection values

- `actor`
- `recipient`

## Examples

### Add user to list

```json
{
  "node_type": "subscriberlistoperation_adduser",
  "properties": {
    "op": "add_user",
    "list_id": "event-attendees",
    "user_selection": ["recipient"],
    "create_list_if_missing": true,
    "list_name": "Event Attendees"
  }
}
```

### Add user to dynamic list

```json
{
  "node_type": "subscriberlistoperation_adduser",
  "properties": {
    "op": "add_user",
    "is_list_id_dynamic": true,
    "list_id": "_subscribers",
    "user_selection": ["recipient"],
    "create_list_if_missing": true
  }
}
```

### Remove user from list

```json
{
  "node_type": "subscriberlistoperation_removeuser",
  "properties": {
    "op": "remove_user",
    "list_id": "trial-users",
    "user_selection": ["recipient"]
  }
}
```
