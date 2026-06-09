---
name: Preserve enums in OpenAPI spec
description: When adding descriptions to OpenAPI spec fields, do not remove existing enum values — they help users understand valid values
type: feedback
---

Do not remove `enum` values from OpenAPI spec fields when adding or editing descriptions.

**Why:** Enums help users understand what values can be passed for a given field. Removing them degrades the API documentation quality even if descriptions are added.

**How to apply:** When editing OpenAPI spec files (e.g., adding descriptions to fields), always preserve existing `enum` arrays. Descriptions and enums serve complementary purposes — descriptions explain *what* the field does, enums show *which values* are accepted.
