# Runtime Recall Adapter

Velvet Interface accepts the public-safe Runtime recall result shape and projects it into `RecallCard`.

The adapter requires matching record and score event identifiers and exposes only bounded presentation fields plus an optional receipt identifier.

It rejects private memory payloads, conversations, embeddings, commands, routes, executors, and capability tokens.

The resulting card remains display-only. It does not claim truth, grant authority, or permit actuation.
