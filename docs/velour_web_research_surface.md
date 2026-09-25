# Velour Web Research surface

Velour Web Research is a controlled, reference-only research desk inside the existing Founder Scroll artwork.

## Visual model

The image surface owns `examples/assets/workspace_scroll.png`, Return-to-Archive navigation, Emergency navigation, and the overall Founder scene lifecycle.

The interactive research widget is placed only inside the physically reviewed Scroll writing area:

```text
x      0.175347
y      0.195000
width  0.647570
height 0.575062
```

This preserves the preferred Founder window size and the established Scroll proportions. The Scroll image does not move. The inner `QTextBrowser` reading pane scrolls vertically when reference content is longer than the visible page.

The composition is:

```text
VELOUR RESEARCH                       REFERENCE ONLY
[ Search the web through Velour... ] [ Search ]

┌──────────── Results ────────────┐ ┌──────── Reading pane ────────┐
│                                │ │                               │
│ bounded search results         │ │ vertically scrollable        │
│                                │ │ sanitized reference content  │
│                                │ │                               │
└────────────────────────────────┘ └───────────────────────────────┘

Source: none                     [Ask Velour] [Save to Library]
```

## Current phase

The reviewed `velours_library` backend owns search, URL policy, selected-page retrieval, redirect and response limits, private-network protections, sanitization, and provenance capture.

`velvet-interface` now contains only a narrow CLI bridge. It invokes the reviewed `velour-web` adapter without a shell, validates the returned JSON schema and trust markers, and converts it into the existing `WebResearchResult` / `WebResearchDocument` presentation contracts.

No provider is enabled implicitly. If no explicit search endpoint is configured, the Scroll remains in its honest offline-shell state.

Founder configuration uses:

```text
VELVET_VELOUR_WEB_EXECUTABLE=/path/to/velour-web
VELVET_VELOUR_SEARCH_ENDPOINT=https://search.example/search
```

A loopback SearXNG endpoint is supported only when explicitly opted in:

```text
VELVET_VELOUR_SEARCH_ALLOW_LOOPBACK=true
```

The default executable location expected by the registry is:

```text
~/velvet/.venvs/velour/bin/velour-web
```

The Archive's measured right-hand reading stand navigates to `velour_web_research`. Search returns bounded metadata. A page is fetched only after the user selects a result and presses Open.

`Ask Velour` and `Save to Library` intentionally remain disabled in this phase. Those are later deliberate handoffs, not side effects of opening a web reference.

## Provider boundary

Interface defines only the presentation contracts:

- `WebResearchResult` for bounded search-result metadata;
- `WebResearchDocument` for sanitized external reference content plus retrieval provenance;
- a search provider callable;
- a document provider callable.

The Interface does not perform web retrieval itself. `VelourWebBridge` invokes the isolated adapter and rejects malformed schemas, authority claims, missing external-reference markers, duplicate result ids, invalid provenance fields, oversized bridge output, nonzero adapter exits, and unavailable executables.

The document contract preserves retrieval timestamp, SHA-256, content type, and fetched byte count so a later `Save to Library` action can carry provenance forward rather than reconstructing it from rendered text.

## Trust and authority

Web material is external reference input, not Velvet authority.

The current surface and contracts preserve these rules:

- no physical-control authority;
- no Court authority;
- no JavaScript execution;
- no external-link opening from the reading pane;
- no automatic downloads;
- no automatic Library persistence;
- no automatic memory promotion;
- `WebResearchDocument.authority` must remain `none`;
- every research document remains marked as an external reference.

The `QTextBrowser` reader has external and in-document link opening disabled. Sanitized HTML or plain text may be displayed, but active browser behavior is not part of this lightweight reader.

## Next phase

After Founder deployment of the adapter executable and an explicit search endpoint, the next implementation slice is the deliberate `Save to Library` handoff using the preserved URL, timestamp, digest, content type, and byte length. `Ask Velour about this page` remains a separate reference-only analysis handoff.

A heavyweight JavaScript-capable interactive browser remains a separate optional future fallback for sites that genuinely require JavaScript. It is not part of the normal Velour research path.
