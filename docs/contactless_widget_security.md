# Contactless Widget Security Boundary

`nfc_status` is a presentation-only widget. It reads the bounded Runtime body-state snapshot and displays reader health plus the latest verification-factor state.

It never receives raw tag data, the private HMAC secret, the registry file, a serial handle, a Runtime route, a Court capability, or an executor. A matched static tag remains corroborating evidence only.
