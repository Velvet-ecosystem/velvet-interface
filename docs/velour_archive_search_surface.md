# Velour Archive Search surface

The Archive magnifying glass opens `velour_archive_search`, a reference-only federated search desk inside the existing Founder Scroll artwork.

## Search sources

One query is passed through the narrow `VelourSearchBridge` to the reviewed `velour-search` CLI. The backend keeps sources separate:

- `library` — Velour's local evidence/index search under the configured Library root;
- `zim` — optional loopback Kiwix/ZIM full-text search;
- `web` — optional explicitly configured SearXNG live-web search.

The local Library remains the primary source. Kiwix and Web are optional. Provider status is displayed independently, so an unavailable optional source does not erase results from the others.

## Founder configuration

The built-in widget registry recognizes these configuration values:

```text
VELVET_VELOUR_FEDERATED_EXECUTABLE=$HOME/.local/bin/velour-search
VELVET_VELOUR_LIBRARY_ROOT=/srv/velvet/library
VELVET_VELOUR_KIWIX_ENDPOINT=http://127.0.0.1:8080
VELVET_VELOUR_SEARCH_ENDPOINT=https://search.example/search
```

`VELVET_VELOUR_KIWIX_ENDPOINT` is optional and the Velour backend accepts loopback Kiwix only. `VELVET_VELOUR_SEARCH_ENDPOINT` is also optional and reuses the reviewed Web Research search-provider boundary. A loopback Web search endpoint still requires the existing `VELVET_VELOUR_SEARCH_ALLOW_LOOPBACK=true` opt-in.

## Visual model

The magnifying-glass hotspot uses the exact coordinates measured on Founder. The destination reuses the physically reviewed Scroll writing rectangle:

```text
x      0.175347
y      0.195000
width  0.647570
height 0.575062
```

The result list labels each row `LIB`, `ZIM`, or `WEB`. Selecting a row shows the reference summary and source metadata in the scrollable detail pane. No result opens an external link or persists itself in this phase.

## Trust boundary

Federated search remains presentation/reference-only:

- `authority` must be `none`;
- every result must remain `external_reference: true`;
- the Interface performs no direct networking;
- the Interface invokes only the fixed `velour-search` executable with `shell=False`;
- no JavaScript executes;
- no external links open;
- no result is automatically written to the Library;
- no search result becomes memory, Court input, or physical-control authority.

The later source-opening and Save-to-Library flows should preserve these same provider identities and provenance fields rather than flattening all search results into one trust class.
