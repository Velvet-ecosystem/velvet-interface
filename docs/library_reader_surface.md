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

## Catalog-first capability

The reader now prefers Velour's canonical on-disk catalog contract when this file exists beneath the configured library root:

```text
catalog/items.jsonl
```

Interface intentionally does not import the Cyberdeck package. It consumes the catalog as a read-only data contract so the UI and library engine remain independently deployable.

Catalog-backed browsing exposes title, collection, source, format, extraction status, adapter identity, and extraction notes. Search can match title, relative path, collection, source, subjects, and tags.

If no catalog exists, the reader falls back to the original bounded filesystem preview. This is useful for bench work and first bring-up, but the catalog is the preferred production path as the vault grows.

## Current format behavior

The reader recognises:

- plain text
- Markdown / reStructuredText
- JSON / YAML / CSV / logs
- local HTML / XHTML
- PDF
- EPUB
- ZIM

Text-oriented files can be previewed directly. Local HTML is rendered through Qt's rich-text document surface with external link opening disabled and without a JavaScript execution engine.

When the catalog reports a PDF or EPUB as successfully extracted, the derived text index can be read immediately in the white viewport. The UI labels this explicitly as `PDF TEXT` or `EPUB TEXT`; it does not pretend that extracted text is a page-faithful renderer.

The original PDF/EPUB remains untouched and canonical. Dedicated page/chapter rendering may be added later without changing the catalog boundary.

ZIM remains a Kiwix-owned archive. The reader reports that state explicitly until the dedicated local Kiwix bridge is connected.

## Security boundary

Library material is reference input, not trusted code and not authority.

The preview layer:

- is read-only;
- does not modify source files;
- never grants capability or Court authority;
- does not execute scripts or attachments;
- does not open external links from rendered HTML;
- resolves payload and extracted-text paths beneath one configured library root;
- rejects catalog entries or derived paths that escape that root;
- caps individual text/HTML/extracted-text previews at 4 MiB by default;
- bounds a filesystem preview scan to 2,000 recognised items by default;
- bounds catalog reading to 100,000 entries and 1 MiB per JSONL line by default.

The 2,000-item UI display bound is not a future shelf-size limit. Canonical search/index services may page or query much larger shelves without asking Interface to recursively enumerate the entire vault.

## Shared vault convention

Runtime currently documents `/srv/velvet` as the shared vault convention. The standalone preview launcher therefore defaults to:

```text
/srv/velvet
```

The path can be overridden with `VELVET_LIBRARY_ROOT` or `--library-root`. A nonstandard catalog path can also be supplied with `--catalog` for bench testing.

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

This launcher exists so the catalog/reader surface can be exercised on the UP Squared before the Archive room entry point is mapped.

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

## Remaining adapters

The main remaining backend work is intentionally separate from the visual surface:

1. Kiwix/ZIM local reader/server handoff;
2. optional PDF page rendering in addition to extracted searchable text;
3. optional EPUB chapter/navigation presentation in addition to extracted searchable text;
4. site-tree or WARC integrity adapters for complete downloaded websites;
5. optional "ask Velour about this item" retrieval handoff that remains reference-only and authority-free.

The Interface should consume those contracts rather than becoming the library engine itself.
