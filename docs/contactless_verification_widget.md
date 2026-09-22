# Contactless Verification Status Widget

The trusted Founder widget ID is:

```text
nfc_status
```

It projects verification-only contactless evidence from the Runtime body-state
snapshot. It may display reader readiness, a matched factor, an unknown factor,
a disabled factor, expired evidence, or reader failure.

The first physical reader is named `Main in Car`, with reader ID `car-main`,
module ID `contactless-token-car-main`, and location `vehicle.cabin`. The widget
can display that reader identity and location when Runtime publishes them.

The widget is optional presentation only. The contactless reader is a headless
Runtime service and must continue observing, matching, and receipting factors
when this widget is not visible, when another Founder room is open, or when the
Interface is not running. Screen placement therefore does not define where or
whether contactless identity evidence works.

The widget never displays the raw tag identifier or private HMAC reference. A
matched presentation remains one corroborating factor and does not establish
owner presence, unlock Maintenance, grant Court authority, or perform actuation.
