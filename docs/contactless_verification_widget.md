# Contactless Verification Status Widget

The trusted Founder widget ID is:

```text
nfc_status
```

It projects verification-only contactless evidence from the Runtime body-state
snapshot. It may display reader readiness, a matched factor, an unknown factor,
a disabled factor, expired evidence, or reader failure.

The widget never displays the raw tag identifier or private HMAC reference. A
matched presentation remains one corroborating factor and does not establish
owner presence, unlock Maintenance, grant Court authority, or perform actuation.
