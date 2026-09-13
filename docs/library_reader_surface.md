# Velour Library Reader Surface

Velour's Library Reader is a read-only Founder Interface workspace for browsing local offline reference material without turning library content into authority.

## Visual model

The reader reuses `examples/assets/workspace_scroll.png` as the Velvet workspace frame.

Inside that frame, the actual document content is shown in a neutral white viewport. This distinction is intentional:

- Velvet owns the surrounding workspace and navigation.
- The source document owns the inner reading area.
- Downloaded HTML therefore does not inherit a parchment treatment that can distort its original layout.
- Text-oriented material remains readable against a conventional document surface.

The same scroll asset remains reusable by Character Foundry and other document/workspace tools.

## Current first-pass capability

The temporary local preview provider recursively scans a configured library root and recognises:

- plain text
- Markdown / reStructuredText
- JSON / YAML / CSV / logs
- local HTML / XHTML
- PDF
- EPUB
- ZIM

Text-oriented files can be previewed directly. Local HTML is rendered through Qt's rich-text document surface with external link opening disabled and without a JavaScript execution engine.

PDF, EPUB, and ZIM are currently catalogued and displayed with an explicit adapter-not-connected message. Their originals remain untouched. Dedicated render/search adapters belong behind the reader contract rather than being faked inside Interface.

This matches the current offline-library architecture, where these richer formats are retained and checksum-verifiable but still require later format adapters.

## Security boundary

Library material is reference input, not trusted code and not authority.

The preview layer:

- is read-only;
- does not modify source files;
- never grants capability or Court authority;
- does not execute scripts or attachments;
- does not open external links from rendered HTML;
- resolves requested files beneath one configured library root;
- rejects traversal outside that root;
- caps individual text/HTML previews at 4 MiB by default;
- bounds a preview scan to 2,000 recognised items by default.

The 2,000-item scan is a temporary Interface preview limit, not a future shelf-size limit. A canonical Velour catalog/index service should replace recursive UI scanning as the vault grows.

## Shared vault convention

Runtime currently documents `/srv/velvet` as the shared vault convention. The standalone preview launcher therefore defaults to:

```text
/srv/velvet
```

The path can be overridden with `VELVET_LIBRARY_ROOT` or `--library-root`.

Interface must not silently claim arbitrary mounted filesystems as Velvet storage. Production deployment should use the same reviewed vault identity/path binding used by Runtime.

## Standalone bench preview

From the repository root:

```bash
python3 scripts/library_reader_preview.py --library-root /srv/velvet
```

Optional full-screen test:

```bash
python3 scripts/library_reader_preview.py --library-root /srv/velvet --fullscreen
```

This launcher exists so the surface can be exercised on the UP Squared before it is mapped into the Archive room.

## Archive-room integration

`LibraryReaderScene` is a trusted built-in scene boundary with scene ID:

```text
library_reader
```

The intended navigation path is:

```text
Founder Home
  -> Archive room
  -> mapped bookshelf / reading object
  -> library_reader
  -> workspace_scroll.png reader
```

Do not invent the Archive hotspot coordinates in source merely to make the scene reachable. The physical-looking entry object should be mapped on the actual Founder display using the same placement workflow used for the other image surfaces.

Once the built-in scene is registered by the Founder launcher, the mapped Archive action will be:

```text
navigate:library_reader
```

## Next adapters

The next useful backend work is intentionally separate from the visual surface:

1. canonical catalog/search provider from Velour's library service;
2. PDF page rendering and text extraction;
3. EPUB spine/chapter navigation;
4. ZIM/Kiwix handoff or embedded offline article rendering;
5. provenance/source metadata from the vault catalog;
6. optional "ask Velour about this item" retrieval handoff that remains reference-only and authority-free.

The Interface should consume those contracts rather than becoming the library engine itself.
