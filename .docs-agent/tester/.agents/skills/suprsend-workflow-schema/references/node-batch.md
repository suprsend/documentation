# Batch Node

**Schema `node_type`:** `batch`

## Documentation

# Batch

> Learn about batch node in workflow and how to use it to group similar notifications into a single notification.

Batch node aggregates multiple triggers into a single batch output to send one consolidated notification rather than sending notification for every user activity. Batching events are useful when a user needs to be notified about a lot of events happening at once but doesn't need a notification for every single event within the batch. for example, if you have a product where users can interact with each other's content and post 5 comments in 10 minutes. In this case, rather than sending 5 notifications, you can batch the events for 10 minutes and send one notification about the 5 comments that the user received.

## How Batching works


  **Opens batch window**
    When a workflow reaches the batch node, it opens a batch for given batch window.
  

  **Aggregates incoming triggers**
    When the batch window is open, all the workflows initiated for the recipient with the same workflow slug and batch key are aggregated in the batch. Batches are created unique for each recipient and batch key combination for that workflow.
  

  **Move to next workflow step once batch window is closed**
    After the batch window is closed, it will send one notification for each batch created in the batch window. Also, with retain batch events, you can limit the number of event data that should be retained in the batch for sending the notification. The output variable structure of a batch is different from the data in your event properties. Refer [Using batch variables in templates](/docs/batch#using-batch-variables-in-templates) to know more.
  


## Batch Window

Batch window is the time for which batch should be open for. After receiving the first event, batch window opens and all the events coming in this interval will be accumulated. The next node is executed after the batch window is closed. There is a setting `Flush first item immediately` which bypasses batch window and sends the first trigger immediately and accumulates the rest.

There are 3 types of window type: **Fixed** (fixed for all users), **Dynamic** (Passed in trigger payload), Relative (relative to a future timestamp, for example 10 minutes before task due time).


  ### Fixed
    Fixed batch window is defined in your workflow form as `**d **h **m **s` and it keeps the batch open for a fixed duration for all users. An example of using fixed batch window can be social media updates where you want to send alert to users about new comments or post likes after an hour from the first comment.

    

    
  

  ### Dynamic
    In case of dynamic batch window, batch duration is computed using the data from your event properties. Dynamic batch window is helpful for cases where batch schedule is defined by the user.

    

    

    You can add duration key as a [JQ-expression](https://jqlang.github.io/jq/manual/). Below are some examples of how to add duration key in JQ format:

    1. General format for duration key at parent level is`.duration_key`
    2. If the duration key is a nested event property key like shown below, enter it in the format`.preferencs.alert_frequency`.

    
      ```json json theme={"system"}
      properties = {
        "preferencs": {
          "alert_frequency": "1h",
          "channels": ["email","inbox"]
        }
      ```
    

    > **Warning:**
      When the duration key specified is missing, or resolves to an invalid value, workflow execution will stop and corresponding error will be logged in the logs❗️
    

    Your duration key variable can be computed to either:

    * An ISO-8601 timestamp (for example 2024-03-02T20:34:07Z) which must be a datetime in the future, or
    * A relative duration unit, which can be
      * an integer like`50`, which will be considered as duration in seconds
      * an interval string defined as`**d **h **m **s`, where d = day, h = hour, m = minutes and s = seconds

    > **Note:**
      **Batch window is not modified by subsequent workflows once the window is open**

      It's important to note that an open batch window cannot be extended by a subsequent workflow trigger if a different dynamic batch window is specified. Once a batch has been opened by a workflow trigger, its window interval is set and cannot be altered.
    
  

  ### Relative
    Relative batch window is calculated based on a future timestamp. for example, sending a batched list of all pending tasks 1 hour before workday end time, where workday_end_time is a key in the trigger payload. It consists of three key components:

    1. **Interval**: The delay from the future timestamp, formatted as xxdxxhxxmxxs (for example 30m for 30 minutes). This can be: Fixed (for example always 1 hour minutes before). Dynamic, where the value is retrieved from the payload (for example in Google Calendar, users can set reminders for 10 or 20 minutes before an event).
    2. **Before/After**: Determines whether the interval is subtracted (before) or added (after) to the timestamp.
    3. **Timestamp**: An ISO-8601 format datetime (for example 2024-03-02T20:34:07Z), which must be in the future. Dynamic Interval & Timestamp must be passed as a JQ-expression. Examples: Timestamp at the parent level: `.timestamp`. If the dynamic interval is set as recipient property: `."$recipient".interval`
  


## Batch Key

This is the property in your `track event` call used for defining unique batches of the events. By default, event will be batched per user. You can use batch key to create multiple batches per user. Batches are created for each unique `distinct_id` and `batch_key` combination. For instance, you can add `post_id` as your batch key if you want to send separate notifications for comments on different LinkedIn posts.


## Retain Batch events

It will define the number of event data that will be included in your batch variable. You have the option to display either the first n events or the last n events in your batch output. By default, the first 10 events are included in your batch output variable once the batch window closes. You can customize the number of events to any value between 2 and 100.


## Flush first item immediately

When this setting is enabled, the first trigger sends a notification immediately, while subsequent triggers are grouped into a batch.

Here, the batch is opened on receiving the first item irrespective of the flush setting. The only difference is, unlike a normal batch, the first item will not be included in batch events and will continue execution past the batch step.

The output structure of the first notification matches the batch structure, with `$batched_events_count = 1`. You can use this count in your workflow or templates to customize content based on whether the notification is sent immediately or as part of a batch.

**Example Use Case:**
Send anomaly alert with first notification sent at the occurrence of first error and next alert sent after 30 minutes if there are further errors. These could be the template content for single vs batched trigger:

* First notification (sent immediately):`A new error encountered in your account - {{$batched_events.[0].error_message}}`
* Batched notification (sent after grouping all errors from second error onwards):`{{$batched_events_count}} errors occurred in your account in the last 30 mins - {{#each $batched_events}}{{error_message}}{{/each}}`

## Using Batch variables in templates

Batch output variable has 2 type of variables:

1. `$batched_events`array : All the event properties corresponding to a batched event is appended to this array and can be used in the template in the array format. The number of event properties returned here is limited by retaining batch events.
2. `$batched_event_count`: This count represents the number of events in a batch and is utilized to render the batch count in a template. For instance, you might send a message like,`Joe left 5 comments in the last 1 hour`where 5 corresponds to \$batched_event_count.

> **Note:**
  📘 Please note that **Retain batch events** setting doesn't impact the count, it just limits the number of event properties returned in `$batched_events` array.


Let's understand the batch variable structure with an example of task comments with below notification content.

```
3 comments are added on your task in last 1 hour.

- Steve: Hey, added the test cases added for PRD-12

- Olivia: Hey, done with the testing. Check the bugs

- Joe: 3 bugs are resolved, 4 are still pending
```

Here is a list of events triggered in the batched window:


  ```javascript javascript theme={"system"}
  //Event 1

  const event_name = "new_comment"

  const properties = {
    "name": "Steve",
    "card_id": "SS-12",
    "comment": "Hey, added the test cases added for PRD-12"
  }

  const event = new Event(distinct_id, event_name, properties)

  //Event 2

  const event_name = "new_comment"

  const properties = {
    "name": "Olivia",
    "card_id": "SS-12",
    "comment": "Hey, done with the testing. Check the bugs"
  }

  const event = new Event(distinct_id, event_name, properties)

  //Event 3

  const event_name = "new_comment"

  const properties = {
    "name": "Joe",
    "card_id": "SS-12",
    "comment": "3 bugs are resolved, 4 are still pending"
  }

  const event = new Event(distinct_id, event_name, properties)
  ```


Output variable of the batch will have `$batched_events_count` and `$batched_events` array of all properties passed in the event payload as shown below:


  ```json json theme={"system"}
  {
    "$batched_events": [
      {
        "name": "Steve",
        "card_id": "SS-12",
        "comment": "Hey, added the test cases added for PRD-12"
      },
      {
        "name": "Olivia",
        "card_id": "SS-12",
        "comment": "Hey, done with the testing. Check the bugs"
      },
      {
        "name": "Joe",
        "card_id": "SS-12",
        "comment": "3 bugs are resolved, 4 are still pending"
      }
    ],
    "$batched_events_count": 3
  }
  ```


This is how you'll add the variable in your template to render the desired notification content.


  ```Text Template theme={"system"}
  {{$batched_events_count}} comments are added on your task in last 1 hour.

  {{#each $batched_events}}
  - {{name}}: {{comment}}

  {{/each}}
  ```

  ```Text Rendered notification theme={"system"}
  3 comments are added on your task in last 1 hour.

  - Steve: Hey, added the test cases added for PRD-12

  - Olivia: Hey, done with the testing. Check the bugs

  - Joe: 3 bugs are resolved, 4 are still pending
  ```


You can also test this behaviour via `Enable batching` option in [Mock data](/docs/templates#the-variables-panel) button on template details page. Once enabled, you'll start getting `$batched_events*` variable in auto suggestion on typing `{{` in template editor. The variables in mock data will be treated as event properties and `Event Count` will imitate the number of times this event will be triggered in the batch.


## Transforming Batch variable output

There can be cases where you need to split the batch output variables into multiple arrays based on keys in your input data. for example, to send a message like `You have got 5 comments and 3 likes on your post in the past 1 hour` where post and likes are interaction_type in your input payload. You can use [data transform node](/docs/data-transform) and generate relevant variables using **JSONNET editor** to handle this use case.


Let's take below example. There are 3 post interactions, 2 comments and 1 like and this is your workflow trigger.


  ```node node theme={"system"}
  //Event 1

  const event_name = "new_post_interaction"

  const properties = {
    "name": "Steve",
    "post_id": "PS-12",
    "interaction_type":"comment",
    "comment": "Well written! looking for more such posts"
  }

  const event = new Event(distinct_id, event_name, properties)

  //Event 2

  const event_name = "new_post_interaction"

  const properties = {
    "name": "Olivia",
    "card_id": "PS-12",
    "interaction_type":"like"
  }

  const event = new Event(distinct_id, event_name, properties)

  //Event 3

  const event_name = "new_post_interaction"

  const properties = {
    "name": "Joe",
    "post_id": "PS-12",
    "interaction_type":"comment",
    "comment": "Every leader should read this"
  }

  const event = new Event(distinct_id, event_name, properties)
  ```


Without transformation, batch output will look like this:


  ```json json theme={"system"}
  {
    "$batched_events":[
      {
    "name": "Steve",
    "post_id": "PS-12",
    "interaction_type":"comment",
    "comment": "Well written! looking for more such posts"
      },
     {
    "name": "Olivia",
    "card_id": "PS-12",
    "interaction_type":"like"
  } ,
   {
    "name": "Joe",
    "post_id": "PS-12",
    "interaction_type":"comment",
    "comment": "Every leader should read this"
  }
    ],
   "$batched_events_count":3
  }
  ```


We'll add 3 variables in data transform node

* `comment_count`: to get the count of all interactions where`interaction_type = comment`
* `like_count`: to get the count of all interactions where`interaction_type = like`
* `all_comments`: to fetch all array objects where`interaction type = comment`


  ```json JSONNET syntax to generate above variables theme={"system"}
  //comment_count
  std.length([x for x in data["$batched_events"] if x.interaction_type == "comment"])

  //like_count
  std.length([x for x in data["$batched_events"] if x.interaction_type == "like"])

  //all_comments
  [x.comment for x in data["$batched_events"] if x.interaction_type == "comment"]
  ```


After data transform node, output variables will contain 3 additional keys generated above. You can use these variables in your template to send the desired message as `You have got {{comment_count}} comments and {{like_count}} likes on your post in the past 1 hour.`.


  ```json json theme={"system"}

  {
    "comment_count":"2",
    "like_count":"1",
    "all_comments":["Well written! looking for more such posts","Every leader should read this"],
    "$batched_events":[
      {
    "name": "Steve",
    "post_id": "PS-12",
    "interaction_type":"comment",
    "comment": "Well written! looking for more such posts"
      },
     {
    "name": "Olivia",
    "card_id": "PS-12",
    "interaction_type":"like"
  } ,
   {
    "name": "Joe",
    "post_id": "PS-12",
    "interaction_type":"comment",
    "comment": "Every leader should read this"
  }
    ],
   "$batched_events_count":3
  }
  ```


***

## Frequently Asked Questions:


  ### What does this error in logs mean batch: this event was added to the running batch of a pre-existing workflow?
    This error indicates that the event triggering the workflow was added to the ongoing batch of an existing workflow. In the context of batched workflows, this occurrence is expected and transient, so it can be safely disregarded.
  

  ### What happens when I have multiple batch nodes in a workflow?
    Each batch node aggregates the event triggers that initiate the workflow and doesn't apply to the output of the batch node connected to its input. The primary impact of connected batch nodes is their cumulative effect on the delay of the notification. The delivery node utilizes the output of the last connected batch node to its input.
  

  ### Do you support per-user batch windows?
    You can use dynamic batch windows and pass per-user batch durations as part of the event property.
  


***

## Schema Properties

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| mode | string | Yes |  |
| window_type | string | Yes |  |
| fixed_window | string | No | Duration format ([xx]d[xx]h[xx]m[xx]s) examples [30s, 1m, 1m30s, 1d3h45m] |
| dynamic_window_expr | string | No | if window_type=dynamic, jq-expression for deriving delay/window |
| relative_to | object | No |  |
| retain_count | integer | No | max number of items to retain after batch closes |
| retain_order | string | No | retain items in this order. first -> first n items. last -> last n items |
| batch_key | string | No | jq-expression for deriving batch-key from payload |

### Mode values

- `accumulate_all`
- `flush_leading_item`

### Window type values

- `fixed`
- `dynamic`
- `relative_to`

### Retain order values

- `first`
- `last`

## Example

```json
{
  "node_type": "batch",
  "properties": {
    "mode": "accumulate_all",
    "window_type": "fixed",
    "fixed_window": "1h",
    "batch_key": ".post_id",
    "retain_count": 10,
    "retain_order": "last"
  }
}
```
