# Object Operation Nodes

## Subscribe to Object

**Schema `node_type`:** `objectoperation_addsubscription`

### Documentation

# Subscribe to Object

> Dynamically add users in object subscription within a workflow.

You can use this node to dynamically add recipient or actor in [object subscription](/docs/object-subscriptions) based on an event or action.

If you have event-based data coming from third-party systems, you don’t need to write custom object subscription APIs in your codebase. Simply send events to SuprSend, and let the workflow handle object subscriptions. For example, when someone subscribes to a topic (like a tournament), you can automatically add them as a subscriber to the corresponding object. This ensures they receive all relevant notifications about topic-related activities without manual intervention.


### Compute and create objects at runtime

You can either add users to a pre-defined object or compute object on the fly using workflow input data. While defining object, both ID and type are mandatory. Type defines the group that object belong to (example, teams, departments). Dynamic object are defined in handlebars format as `{{...}}`.

Computed Object will only be created if `Create object if it doesn't exist` setting is ON.

One common use case of creating object dynamically is when you need to create different objects based on user topic subscription. For example, there are multiple player tournaments happening and you want to create a separate object for each tournament. Object ID in such case can be `{{tournament_id}}` and type `tournaments`.

> **Warning:**
  Both object ID and type only supports following characters- \`a-z,0-9,-,_\`. Ensure that the variable resolves to a valid format; otherwise, object creation will fail.


### Subscription properties

Subscription properties are the set of variables defining relationship between a subscriber and an object. During a workflow execution, these properties can be accessed under the `recipient.subscription` namespace as `recipient.subscription.property_key`. Subscription properties are added in [JSONNET](https://jsonnet.org/ref/language.html) format. You can [read more about object subscription here](/docs/object-subscriptions).

***

## Unsubscribe from Object

**Schema `node_type`:** `objectoperation_removesubscription`

### Documentation

# Unsubscribe from Object

> Dynamically remove users from object subscription within a workflow.

You can use this node to dynamically remove recipient or actor from [object subscription](/docs/object-subscriptions) based on an event or action.

If you have event-based data coming from third-party systems, you don’t need to write custom object subscription APIs in your codebase. Simply send events to SuprSend, and let the workflow handle object subscriptions. For example, when someone unsubscribes from a topic (like a tournament), you can automatically remove their subscription from the corresponding object. This ensures they receive all relevant notifications about topic-related activities without manual intervention.


### Compute objects at runtime

You can either remove users from a pre-defined object or compute object on the fly using workflow input data. While defining object, both ID and type are mandatory. Type defines the group that object belong to (example, teams, departments). Dynamic object are defined in handlebars format as `{{...}}`.

One common use case of creating object dynamically is when you need to compute objects based on user topic subscription. For example, there are multiple player tournaments happening and there are separate objects for each tournament. Object ID in such case can be `{{tournament_id}}` and type `tournaments`.

> **Warning:**
  Object subscription will only be removed if the computed object exists, else this action will fail.


### Subscription properties

Subscription properties are the set of variables defining relationship between a subscriber and an object. During a workflow execution, these properties can be accessed under the `recipient.subscription` namespace as `recipient.subscription.property_key`. Subscription properties are added in [JSONNET](https://jsonnet.org/ref/language.html) format. You can [read more about object subscription here](/docs/object-subscriptions).

***

## Schema Properties (shared)

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| is_object_id_dynamic | boolean | No | If dynamic, object_type/id static literal or a handlebars expression |
| object_type | string | Yes | static literal OR a handlebars expression (if dynamic) |
| object_id | string | Yes | static literal OR a handlebars expression (if dynamic) |
| create_object_if_missing | boolean | No | applicable when op=add_subscription. should object be created in doesn't exist? |
| user_selection | array | Yes |  |
| subscription_properties | string | null | No | subscription properties. JSONNET expression that evaluates to a map/dictionary |

### User selection values

- `actor`
- `recipient`

## Examples

### Subscribe to object

```json
{
  "node_type": "objectoperation_addsubscription",
  "properties": {
    "op": "add_subscription",
    "object_type": "team",
    "object_id": "engineering",
    "user_selection": ["recipient"],
    "create_object_if_missing": true,
    "subscription_properties": "{ role: data.team_role }"
  }
}
```

### Subscribe to dynamic object

```json
{
  "node_type": "objectoperation_addsubscription",
  "properties": {
    "op": "add_subscription",
    "is_object_id_dynamic": true,
    "object_type": "",
    "object_id": "",
    "user_selection": ["recipient"],
    "create_object_if_missing": true
  }
}
```

### Unsubscribe from object

```json
{
  "node_type": "objectoperation_removesubscription",
  "properties": {
    "op": "remove_subscription",
    "object_type": "tournament",
    "object_id": "summer-2024",
    "user_selection": ["recipient"]
  }
}
```
