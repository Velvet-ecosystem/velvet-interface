import tempfile
import unittest
from pathlib import Path

from velvet_interface.scene_system.surface_set import (
    SurfaceSetError,
    SurfaceSetLoader,
)


class SurfaceSetTests(unittest.TestCase):
    def test_resolves_surface_directory_relative_to_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            surfaces = root / "scenes"
            surfaces.mkdir()
            binding = root / "home.surface-set.yaml"
            binding.write_text(
                "\n".join(
                    [
                        "schema: velvet.interface.surface-set.v1",
                        "name: home",
                        "surface_directory: scenes",
                        "initial_scene: home_front_room",
                    ]
                ),
                encoding="utf-8",
            )

            result = SurfaceSetLoader().load(str(binding), require_directory=True)
            self.assertEqual(result.name, "home")
            self.assertEqual(result.surface_path, surfaces.resolve())
            self.assertEqual(result.initial_scene, "home_front_room")

    def test_rejects_secret_or_authority_fields(self):
        with self.assertRaises(SurfaceSetError):
            SurfaceSetLoader().from_mapping(
                {
                    "schema": "velvet.interface.surface-set.v1",
                    "name": "home",
                    "surface_directory": "scenes",
                    "initial_scene": "home_front_room",
                    "token": "not-allowed-here",
                }
            )

    def test_rejects_unknown_schema(self):
        with self.assertRaises(SurfaceSetError):
            SurfaceSetLoader().from_mapping(
                {
                    "schema": "velvet.interface.surface-set.v999",
                    "name": "home",
                    "surface_directory": "scenes",
                    "initial_scene": "home_front_room",
                }
            )

    def test_missing_directory_fails_when_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binding = root / "home.surface-set.yaml"
            binding.write_text(
                "\n".join(
                    [
                        "schema: velvet.interface.surface-set.v1",
                        "name: home",
                        "surface_directory: missing",
                        "initial_scene: home_front_room",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaises(FileNotFoundError):
                SurfaceSetLoader().load(str(binding), require_directory=True)


if __name__ == "__main__":
    unittest.main()
