# SPDX-License-Identifier: GPL-3.0-only

import tempfile
import unittest
from pathlib import Path

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
