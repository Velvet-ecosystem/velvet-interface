# Velour Web Research surface

Velour Web Research is a controlled, reference-only research desk inside the existing Founder Scroll artwork.

## Visual model

The image surface owns `examples/assets/workspace_scroll.png`, Return-to-Archive navigation, Emergency navigation, and the overall Founder scene lifecycle.

The interactive research widget is placed only inside the physically measured Scroll writing area:

```text
x      0.175347
y      0.180000
width  0.647570
height 0.590062
```

This preserves the preferred Founder window size and the established Scroll proportions. The Scroll image does not move. The inner `QTextBrowser` reading pane scrolls vertically when reference content is longer than the visible page.

The initial composition is:

```text
VELOUR RESEARCH                       REFERENCE ONLY
[ Search the web through Velour... ] [ Search ]

┌──────────── Results ────────────┐ ┌──────── Reading pane ────────┐
│                                │ │                               │
│ future search results          │ │ vertically scrollable        │
│                                │ │ sanitized reference content  │
│                                │ │                               │
└────────────────────────────────┘ └───────────────────────────────┘

Source: none                     [Ask Velour] [Save to Library]
```

## Current phase

The surface shell is active, but no live network provider is connected yet.

The Archive's measured right-hand reading stand now navigates to `velour_web_research`. Search may be typed into the field, but pressing Search reports that the live adapter is not connected. This is deliberate rather than simulated success.

`Ask Velour` and `Save to Library` remain disabled until a real external reference document has been opened through reviewed provider contracts.

## Provider boundary

Interface defines only the presentation contracts:

- `WebResearchResult` for bounded search-result metadata;
- `WebResearchDocument` for sanitized external reference content;
- a search provider callable;
- a document provider callable.

The Interface package performs no networking in this phase. A later adapter/service will own network access, URL policy, redirects, size limits, sanitization, and source retrieval.

This keeps the visible research desk independent from whichever search/fetch backend is selected later.

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

The `QTextBrowser` reader has external and in-document link opening disabled. A future provider may supply sanitized HTML or plain text, but active browser behavior is not part of this lightweight reader.

## Next phase

The next implementation slice is the controlled search/fetch adapter. It should:

1. accept one explicit research query;
2. return bounded result metadata;
3. fetch only an explicitly selected result;
4. enforce HTTP/HTTPS and private-network protections;
5. bound redirects, response size, and content type;
6. sanitize HTML before returning it to Interface;
7. keep fetched content reference-only;
8. expose provenance needed by the later `Save to Library` handoff.

A heavyweight interactive browser remains a separate optional future fallback for sites that genuinely require JavaScript. It is not part of the normal Velour research path.
