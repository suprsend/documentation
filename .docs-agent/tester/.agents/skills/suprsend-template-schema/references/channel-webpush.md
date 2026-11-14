# Web Push Content Schema

For variants with `channel: "webpush"`.

**Schema URL:** `https://schema.suprsend.com/template/v2/channel/webpush_schema.json`

## Fields

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| $schema | string | No |  |
| templating_language | string | No |  |
| header | string | Yes | message title/header |
| body | string | Yes | message text/body |
| icon_url | string | No |  |
| image_url | string | No | image url |
| action_url | string | No | action url/deeplink |
| badge_url | string | No | badge url |
| dir | string | No |  |
| vibrate | array | No |  |
| sound | string | No |  |
| is_sticky | boolean | No |  |
| is_silent | boolean | No |  |
| renotify | boolean | No |  |
| group | string | No |  |
| lang | string | No |  |
| buttons | array | No |  |
| extra_payload | object | No | extra payload. dict of key-value pairs |

`header` and `body` are required.

### `dir` values

- `auto`
- `ltr`
- `rtl`

`vibrate` is an array of positive integers (alternating vibration / pause durations in ms — service worker reads it directly).

## Buttons

Up to 2 entries in `buttons[]`:

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| id | string | No |  |
| text | string | Yes |  |
| url | string | Yes |  |
| icon | string | No |  |

## Examples

### Simple notification

```json
{
  "header": "Build complete",
  "body": "{{ repo }} – {{ branch }} built in {{ duration }}",
  "icon_url": "{{ $brand.logo }}",
  "action_url": "https://acme.com/builds/{{ build.id }}"
}
```

### Notification with actions and badge

```json
{
  "header": "{{ sender.name }} sent a message",
  "body": "{{ message.preview }}",
  "icon_url": "{{ sender.avatar_url }}",
  "badge_url": "https://cdn.acme.com/badge.png",
  "action_url": "https://acme.com/chat/{{ thread.id }}",
  "buttons": [
    { "id": "reply",   "text": "Reply",   "url": "https://acme.com/chat/{{ thread.id }}?reply=1" },
    { "id": "dismiss", "text": "Dismiss", "url": "https://acme.com/chat/{{ thread.id }}?dismiss=1" }
  ],
  "renotify": true,
  "group": "chat-{{ thread.id }}"
}
```

## Documentation

```
# Web Push

> Design Web Push notification templates with title, body, image, action URL, and buttons - with a live Windows/macOS preview.

The Web Push editor is a form with title, body, image, action URL, and buttons - with a live preview on the right (toggle between Windows and macOS). Content is personalised with [Handlebars](/docs/handlebars-helpers) variables (`{{variable_name}}`).


## Web Push fields

**Title** - single-line heading. Keep under 40 characters (Windows truncates aggressively; macOS is more generous). Supports Handlebars variables.

**Large Icon** - shown to the right of the notification text. Defaults to your organisation logo (set in Organisation Settings). Cannot be changed per template.

**Body** - 2-3 lines max. One sentence with a clear CTA is ideal. Supports Handlebars variables.

**Banner Image URL** - *optional.* 2:1 aspect ratio (recommended 720x480), under 200 KB for instant rendering. Formats: PNG, JPG, JPEG.

**Action URL** - URL opened on notification click. Always include one - without it, clicking does nothing. Supports Handlebars variables.

**Chrome Action Buttons** - *optional.* Up to 2 buttons with action-oriented labels (2-3 words: "View Order", "Shop Now"). Supports Handlebars. Only visible on Chromium browsers (Chrome, Edge, Brave) - on Firefox and Safari, only the title, body, and click action are shown.

## Adding dynamic content

You can add variables in the template to personalise it for each recipient. Variables are replaced with actual data at send time.


  **Add variables in the Variables panel**
    Add sample data in the **Variables panel** (Input Payload section) on the left side of the editor. This powers auto-suggestions and the live preview. For the full guide, see [Adding dynamic content](/docs/templates#the-variables-panel).
  

  **Use variables in the template**
    Type `{{` in any field - matching variables appear as auto-suggestions. You can also type variable names manually following [Handlebars syntax](https://handlebarsjs.com/guide/#what-is-handlebars).

    **Examples using this sample data:**

    
      ```json json theme={"system"}
      {
        "event": {
          "order_id": "11200123",
          "first_name": "Emma"
        },
        "product_name": "RayBan Sunglasses",
        "product_image_url": "https://yourapp.com/images/product.jpg"
      }
      ```
    

    * **Nested variable:** `{{event.order_id}}` → renders as `11200123`
    * **Variable with space in name:** `{{event.[first name]}}`

    The preview section shows sample values rendered in real-time. If a variable isn't rendering, check:

    1. The variable is defined in the Variables panel.
    2. The variable name matches the Handlebars syntax exactly.
  


> **Warning:**
  If a variable cannot be rendered at send time (missing or mismatched data), SuprSend discards the Web Push notification for that user. Other channels in the same template group are still sent.


## Preview and test

The right panel shows a live notification preview (toggle Windows / macOS). Variables render using data from the **Variables panel**.

Click **Test** in the top-right corner to send a real web push to a real browser. This uses the **live version** - commit your changes before testing. See [Testing a Template](/docs/templates#test) for the full guide.

## Commit

Click **Commit** in the top bar to publish the current draft as a new live version. Add an optional description for versioning.

## Common scenarios


  ### Back-in-stock alert
    | Field            | Value                                                     |
    | ---------------- | --------------------------------------------------------- |
    | Title            | `Back in stock: {{product_name}}`                         |
    | Body             | `The item you were watching is available again.`          |
    | Banner Image URL | `{{product_image_url}}`                                   |
    | Action URL       | `https://yourapp.com/product/{{product_id}}`              |
    | Button 1         | `Buy Now` → `https://yourapp.com/cart/add/{{product_id}}` |
  

  ### New content published
    | Field            | Value                                   |
    | ---------------- | --------------------------------------- |
    | Title            | `New article: {{article_title}}`        |
    | Body             | `{{article_excerpt}}`                   |
    | Banner Image URL | `{{cover_image_url}}`                   |
    | Action URL       | `https://yourblog.com/{{article_slug}}` |
  

  ### Price drop
    | Field      | Value                                                         |
    | ---------- | ------------------------------------------------------------- |
    | Title      | `Price dropped on {{product_name}}`                           |
    | Body       | `Now {{new_price}} (was {{old_price}})`                       |
    | Action URL | `https://yourapp.com/product/{{product_id}}`                  |
    | Button 1   | `View Deal` → `https://yourapp.com/product/{{product_id}}`    |
    | Button 2   | `Add to Cart` → `https://yourapp.com/cart/add/{{product_id}}` |
  


## Frequently asked questions


  ### Which browsers support which features?
    | Feature        | Chrome        | Firefox | Safari (macOS) | Edge          |
    | -------------- | ------------- | ------- | -------------- | ------------- |
    | Title + Body   | Yes           | Yes     | Yes            | Yes           |
    | Banner Image   | Yes           | Yes     | No             | Yes           |
    | Action Buttons | Yes (up to 2) | No      | No             | Yes (up to 2) |
    | Large Icon     | Yes           | Yes     | No             | Yes           |

    Action buttons are labelled "Chrome Action Buttons" in the editor because they only render on Chromium browsers. Design your notification so the core message is in the title + body, with buttons as an enhancement.
  

  ### How do I change the large icon?
    The large icon defaults to your organisation logo set in **Organisation Settings** on the SuprSend dashboard. It cannot be changed per template - update it in your org settings if you need a different icon.
  

  ### How often should I send web push notifications?
    Web push has higher opt-out rates than other channels. Send only high-value, time-sensitive notifications to maintain subscriber trust. Over-sending is the fastest way to lose subscribers.
  

  ### What happens if a variable is missing at send time?
    SuprSend discards the Web Push notification for that user. Other channels in the same template group are still sent if they render successfully.
```
