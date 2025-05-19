# SuprSend Documentation

Available at https://docs.suprsend.com


### Mapping all the API-Endpoints to tags:

| Endpoint                                                                      | Tag Name        |
| ----------------------------------------------------------------------------- | --------------- |
| `/event/` (POST)                                                              | Events          |
| `/v1/tenant/{tenant_id}` (POST)                                               | Tenants         |
| `/v1/tenant/{tenant_id}` (GET)                                                | Tenants         |
| `/v1/tenant/{tenant_id}` (DELETE)                                             | Tenants         |
| `/v1/tenant/` (GET)                                                           | Tenants         |
| `/v1/subscriber_list/{list_id}/subscriber/remove` (POST)                      | Lists           |
| `/v1/subscriber_list/` (GET)                                                  | Lists           |
| `/v1/subscriber_list/` (POST)                                                 | Lists           |
| `/{workspace_key}/trigger/` (POST)                                            | Workflows       |
| `/v1/user/{distinct_id}/preference/category/` (GET)                           | Preferences     |
| `/v1/subscriber_list/{list_id}/subscriber/add` (POST)                         | Lists           |
| `/v1/subscriber_list/{list_id}/` (GET)                                        | Lists           |
| `/{workspace_key}/broadcast` (POST)                                           | Broadcasts      |
| `/v1/user/{distinct_id}/preference/channel_preference/` (GET)                 | Preferences     |
| `/v1/user/{distinct_id}/preference/channel_preference/` (PATCH)               | Preferences     |
| `/v1/user/{distinct_id}/preference/category/{category_slug}/` (PATCH)         | Preferences     |
| `/v1/tenant/{tenant_id}/category/{category_slug}/` (PATCH)                    | Tenants         |
| `/v1/subscriber_list/{list_id}/delete` (PATCH)                                | Lists           |
| `/v1/user/{distinct_id}/preference/category/{category_slug}` (GET)            | Preferences     |
| `/v1/tenant/{tenant_id}/category/` (GET)                                      | Tenants         |
| `/v1/subscriber_list/{list_id}/version/{version_id}/subscriber/add` (POST)    | Drafts          |
| `/v1/subscriber_list/{list_id}/version/{version_id}/delete` (PATCH)           | Drafts          |
| `/v1/template/{template_slug}` (GET)                                          | Templates       |
| `/v1/subscriber_list/{list_id}/version/{version_id}/finish_sync` (PATCH)      | Drafts          |
| `/v1/subscriber_list/{list_id}/version/{version_id}/subscriber/remove` (POST) | Drafts          |
| `/v1/subscriber_list/{list_id}/start_sync` (POST)                             | Drafts          |
| `/v1/template/{template_slug}/channel/{channel_slug}` (GET)                   | Templates       |
| `/v1/template` (GET)                                                          | Templates       |
| `/trigger/` (POST)                                                            | Workflows       |
| `/v1/bulk/subscriber/preference/` (PATCH)                                     | Bulk Operations |
| `/v1/bulk/subscriber/preference/reset/` (PATCH)                               | Bulk Operations |
| `/v1/user/{distinct_id}/preference/` (GET)                                    | Preferences     |
| `/v1/subscriber_list/{list_id}/subscriber/` (GET)                             | Lists           |
| `/v1/object/{object_type}/{id}/` (POST)                                       | Objects         |
| `/v1/object/{object_type}/{id}/` (GET)                                        | Objects         |
| `/v1/object/{object_type}/{id}/` (DELETE)                                     | Objects         |
| `/v1/object/{object_type}/{id}/` (PATCH)                                      | Objects         |
| `/v1/object/{object_type}/{id}/subscription/` (POST)                          | Subscriptions   |
| `/v1/object/{object_type}/{id}/subscription/` (GET)                           | Subscriptions   |
| `/v1/object/{object_type}/{id}/subscription/` (DELETE)                        | Subscriptions   |
| `/v1/object/{object_type}/` (GET)                                             | Objects         |
| `/v1/object/{object_type}/{id}/preference/category/{category_slug}/` (PATCH)  | Preferences     |
| `/v1/object/{object_type}/{id}/preference/channel_preference/` (PATCH)        | Preferences     |
| `/v1/object/{object_type}/{id}/preference/channel_preference/` (GET)          | Preferences     |
| `/v1/object/{object_type}/{id}/preference/` (GET)                             | Preferences     |
| `/v1/object/{object_type}/{id}/preference/category/` (GET)                    | Preferences     |
| `/v1/object/{object_type}/{id}/preference/category/{category_slug}` (GET)     | Preferences     |
| `/v1/user/{distinct_id}/` (POST)                                              | Users           |
| `/v1/user/{distinct_id}/` (GET)                                               | Users           |
| `/v1/user/{distinct_id}/` (DELETE)                                            | Users           |
| `/v1/user/{distinct_id}/` (PATCH)                                             | Users           |
| `/v1/user/` (GET)                                                             | Users           |
| `/v1/user/{distinct_id}/merge/` (POST)                                        | Users           |
| `/v1/user/{distinct_id}/subscribed_to/object/` (GET)                          | Subscriptions   |
| `/v1/user/{distinct_id}/subscribed_to/list/` (GET)                            | Subscriptions   |
| `/v1/object/{object_type}/{id}/subscribed_to/object/` (GET)                   | Subscriptions   |
