# API Breaking Changes Reference Guide

When evaluating OpenAPI contract diffs, categorize changes using the following rules:

### Non-Breaking Changes (Safe)
- Adding a new optional request parameter.
- Adding a new response field (unless strict clients reject unknown fields).
- Adding a new independent endpoint path (`POST /api/v1/new-feature`).
- Adding a new optional header.

### Breaking Changes (Requires Migration / Human Confirmation)
- Renaming or deleting an existing endpoint or HTTP method.
- Adding a required request parameter or body property without a default value.
- Changing the data type of an existing field (e.g. `string` to `integer`).
- Removing an existing response field or altering status codes.
