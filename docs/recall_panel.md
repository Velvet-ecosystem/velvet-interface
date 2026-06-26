# Quiet Recall Panel

`RecallPanel` is a bounded, display-only container for public-safe recall cards.

Supported states are `empty`, `loading`, `ready`, and `failed`.

Only the ready state may carry cards. Failed state requires a stable error code. The panel never claims truth, grants authority, or permits actuation.
