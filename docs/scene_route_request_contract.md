# Scene Route Request Contract

Velvet scenes express intent. They do not choose execution authority.

A scene request contains only an intent identifier, a route identifier, and bounded parameters.

Example:

```json
{
  "intent_id": "intent-1",
  "route_id": "runtime-status",
  "parameters": {
    "detail": "summary"
  }
}
```

Identity and execution bindings are supplied inside Velvet Runtime from verified boot context and trusted route registration.

The request path is:

```text
scene interaction
  -> bounded route request
  -> Runtime local gateway
  -> strict intent
  -> authorization
  -> safety check
  -> approved executor
  -> receipts
```

A route request is not permission. Unknown routes, extra fields, reserved parameter names, and non-normalized identifiers are rejected.

Local navigation remains an interface concern. Protected system actions must travel through Runtime.
