# SPDX-License-Identifier: GPL-3.0-only

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from velvet_interface.library_reader_registration import (
    build_library_reader_scene,
    default_catalog_path,
    default_library_root,
    register_library_reader,
)


class _FakeRouter:
    def __init__(self):
        self.registered = []

    def register_scene(self, scene):
        self.registered.append(scene)

    def back(self):
        return True


class LibraryReaderRegistrationTests(unittest.TestCase):
    def test_shared_vault_is_default_library_root(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(default_library_root(), Path("/srv/velvet"))
            self.assertIsNone(default_catalog_path())

    def test_environment_overrides_are_explicit(self):
        with patch.dict(
            os.environ,
            {
                "VELVET_LIBRARY_ROOT": "/tmp/velvet-vault",
                "VELVET_LIBRARY_CATALOG": "/tmp/velvet-vault/catalog/custom.jsonl",
            },
            clear=True,
        ):
            self.assertEqual(default_library_root(), Path("/tmp/velvet-vault"))
            self.assertEqual(
                default_catalog_path(),
                Path("/tmp/velvet-vault/catalog/custom.jsonl"),
            )

    def test_builder_uses_catalog_aware_provider_and_scroll_scene(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            scene = build_library_reader_scene(
                access_provider=lambda: True,
                library_root=Path(temp_dir),
            )

            self.assertEqual(scene.scene_id, "library_reader")
            self.assertEqual(scene.provider.root, Path(temp_dir))
            self.assertEqual(
                scene.background_path.as_posix(),
                "examples/assets/workspace_scroll.png",
            )

    def test_registration_binds_router_and_preserves_access_boundary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            router = _FakeRouter()
            scene = register_library_reader(
                router,
                access_provider=lambda: False,
                library_root=Path(temp_dir),
            )

            self.assertEqual(router.registered, [scene])
            self.assertIs(scene._router, router)
            self.assertFalse(scene._has_access())


if __name__ == "__main__":
    unittest.main()
