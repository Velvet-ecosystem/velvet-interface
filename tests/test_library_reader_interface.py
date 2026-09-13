# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.catalog_library_preview import CatalogLibraryPreviewProvider
from velvet_interface.library_preview import LocalLibraryPreviewProvider
from velvet_interface.scenes.library_reader_scene import LibraryReaderScene


class LibraryPreviewProviderTests(unittest.TestCase):
    def test_catalogues_known_formats_and_reads_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "manual.md").write_text("# Manual\nHello Velvet", encoding="utf-8")
            (root / "site.html").write_text("<h1>Offline site</h1>", encoding="utf-8")
            (root / "book.pdf").write_bytes(b"%PDF-test")
            (root / "ignore.bin").write_bytes(b"nope")

            provider = LocalLibraryPreviewProvider(root)
            items = provider.list_items()

            self.assertEqual([item.suffix for item in items], [".pdf", ".md", ".html"])
            manual = next(item for item in items if item.suffix == ".md")
            site = next(item for item in items if item.suffix == ".html")
            pdf = next(item for item in items if item.suffix == ".pdf")
            self.assertEqual(provider.read_text(manual), "# Manual\nHello Velvet")
            self.assertEqual(provider.read_text(site), "<h1>Offline site</h1>")
            self.assertEqual(pdf.preview_kind, "pdf")
            with self.assertRaises(ValueError):
                provider.read_text(pdf)

    def test_search_is_bounded_to_title_or_relative_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "cars").mkdir()
            (root / "cars" / "tiburon_service.txt").write_text("service", encoding="utf-8")
            (root / "garden.txt").write_text("garden", encoding="utf-8")
            provider = LocalLibraryPreviewProvider(root)

            items = provider.list_items(query="tiburon")

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].relative_path, "cars/tiburon_service.txt")

    def test_missing_library_root_is_empty_not_exception(self):
        provider = LocalLibraryPreviewProvider(Path("/definitely/not/a/velvet/library"))
        self.assertEqual(provider.list_items(), [])


class CatalogLibraryPreviewProviderTests(unittest.TestCase):
    def _write_catalog(self, root: Path, entries) -> None:
        catalog_dir = root / "catalog"
        catalog_dir.mkdir(parents=True, exist_ok=True)
        with (catalog_dir / "items.jsonl").open("w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry) + "\n")

    def test_catalog_metadata_search_and_pdf_extracted_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload_dir = root / "collections" / "manuals"
            payload_dir.mkdir(parents=True)
            pdf = payload_dir / "service.pdf"
            pdf.write_bytes(b"%PDF-test")
            text_dir = root / "indexes" / "text"
            text_dir.mkdir(parents=True)
            extracted = text_dir / "lib_pdf.txt"
            extracted.write_text("Tiburon timing belt service procedure", encoding="utf-8")
            self._write_catalog(
                root,
                [
                    {
                        "item_id": "lib_pdf",
                        "title": "Tiburon Service Manual",
                        "collection": "vehicle-manuals",
                        "source": "manufacturer archive",
                        "file_path": str(pdf),
                        "media_type": "application/pdf",
                        "checksum_sha256": "unused-by-interface",
                        "imported_at": "2026-09-12T00:00:00+00:00",
                        "subjects": ["service"],
                        "tags": ["tiburon"],
                        "language": "en",
                        "trust_note": None,
                        "extracted_text_path": str(extracted),
                        "adapter_id": "pdf-pdftotext",
                        "adapter_version": "1",
                        "extraction_status": "extracted",
                        "extraction_note": None,
                    }
                ],
            )

            provider = CatalogLibraryPreviewProvider(root)
            items = provider.list_items(query="manufacturer")

            self.assertTrue(provider.catalog_available)
            self.assertEqual(len(items), 1)
            item = items[0]
            self.assertEqual(item.title, "Tiburon Service Manual")
            self.assertTrue(provider.has_extracted_text(item))
            self.assertEqual(provider.read_text(item), "Tiburon timing belt service procedure")
            metadata = provider.metadata_for(item)
            self.assertIsNotNone(metadata)
            self.assertEqual(metadata.collection, "vehicle-manuals")
            self.assertEqual(metadata.adapter_id, "pdf-pdftotext")

    def test_catalog_entry_outside_root_is_not_exposed(self):
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(temp_dir)
            outside = Path(outside_dir) / "secret.txt"
            outside.write_text("not library content", encoding="utf-8")
            self._write_catalog(
                root,
                [
                    {
                        "item_id": "lib_bad",
                        "title": "Outside",
                        "collection": "bad",
                        "source": "bad",
                        "file_path": str(outside),
                        "media_type": "text/plain",
                        "checksum_sha256": "unused",
                        "imported_at": "2026-09-12T00:00:00+00:00",
                    }
                ],
            )

            provider = CatalogLibraryPreviewProvider(root)
            self.assertEqual(provider.list_items(), [])

    def test_missing_catalog_falls_back_to_bounded_filesystem_preview(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "notes.txt").write_text("hello", encoding="utf-8")
            provider = CatalogLibraryPreviewProvider(root)

            items = provider.list_items()

            self.assertFalse(provider.catalog_available)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].relative_path, "notes.txt")


class LibraryReaderSceneTests(unittest.TestCase):
    def test_scene_defaults_to_reusable_workspace_scroll(self):
        provider = LocalLibraryPreviewProvider(Path("unused"))
        scene = LibraryReaderScene(provider=provider, access_provider=lambda: True)
        self.assertEqual(scene.scene_id, "library_reader")
        self.assertEqual(scene.background_path.as_posix(), "examples/assets/workspace_scroll.png")
        self.assertFalse(scene.is_active)

    def test_scene_access_fails_closed(self):
        provider = LocalLibraryPreviewProvider(Path("unused"))
        denied = LibraryReaderScene(provider=provider, access_provider=lambda: False)
        broken = LibraryReaderScene(
            provider=provider,
            access_provider=lambda: (_ for _ in ()).throw(RuntimeError("no access evidence")),
        )
        self.assertFalse(denied._has_access())
        self.assertFalse(broken._has_access())


if __name__ == "__main__":
    unittest.main()
