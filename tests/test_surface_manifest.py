import tempfile
import unittest
from pathlib import Path

from velvet_interface.scene_system.surface_manifest import (
    SurfaceManifestError,
    SurfaceManifestLoader,
)
from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader


class SurfaceManifestTests(unittest.TestCase):
    def surface_mapping(self):
        return {
            "schema": "velvet.interface.surface.v1",
            "name": "home",
            "base_resolution": [1000, 500],
            "background": {
                "image": "home.png",
                "fit": "cover",
                "alt_text": "Home",
            },
            "press_points": [
                {
                    "id": "drive",
                    "coordinate_space": "normalized",
                    "polygon": [[0.1, 0.2], [0.3, 0.2], [0.3, 0.4], [0.1, 0.4]],
                    "action": "navigate:drive",
                    "accessibility_label": "Open Drive",
                }
            ],
            "widgets": [
                {
                    "widget_id": "body_status",
                    "coordinate_space": "normalized",
                    "rect": [0.7, 0.1, 0.2, 0.2],
                    "visible_in": ["owner"],
                }
            ],
        }

    def test_normalized_geometry_projects_to_base_pixels(self):
        manifest = SurfaceManifestLoader().from_mapping(self.surface_mapping())
        scene = manifest.to_scene_data()

        self.assertEqual(scene["background_fit"], "cover")
        self.assertEqual(
            scene["regions"][0]["polygon"],
            [[100.0, 100.0], [300.0, 100.0], [300.0, 200.0], [100.0, 200.0]],
        )
        self.assertEqual(scene["widgets"][0]["rect"], [700.0, 50.0, 200.0, 100.0])

    def test_resolves_background_relative_to_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "home.png"
            image.write_bytes(b"not-a-real-image-but-an-existing-asset")
            manifest_path = root / "home.surface.yaml"
            manifest_path.write_text(
                "\n".join(
                    [
                        "schema: velvet.interface.surface.v1",
                        "name: home",
                        "base_resolution: [1000, 500]",
                        "background:",
                        "  image: home.png",
                        "  fit: contain",
                        "press_points: []",
                        "widgets: []",
                    ]
                ),
                encoding="utf-8",
            )

            manifest = SurfaceManifestLoader().load(str(manifest_path))
            self.assertEqual(Path(manifest.background.image_path), image.resolve())
            self.assertEqual(manifest.background.fit, "contain")

    def test_rejects_authoritative_action(self):
        mapping = self.surface_mapping()
        mapping["press_points"][0]["action"] = "command:unlock"
        with self.assertRaises(SurfaceManifestError):
            SurfaceManifestLoader().from_mapping(mapping)

    def test_rejects_nested_authority_field(self):
        mapping = self.surface_mapping()
        mapping["widgets"][0]["metadata"] = {"capability_token": "bad"}
        with self.assertRaises(SurfaceManifestError):
            SurfaceManifestLoader().from_mapping(mapping)

    def test_rejects_duplicate_widget_ids(self):
        mapping = self.surface_mapping()
        mapping["widgets"].append(dict(mapping["widgets"][0]))
        with self.assertRaises(SurfaceManifestError):
            SurfaceManifestLoader().from_mapping(mapping)

    def test_legacy_regions_remain_pixel_coordinates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.yaml"
            path.write_text(
                "\n".join(
                    [
                        "name: legacy",
                        "base_resolution: [800, 480]",
                        "background: missing.png",
                        "regions:",
                        "  - name: drive",
                        "    polygon: [[10, 20], [110, 20], [110, 120], [10, 120]]",
                        "    action: navigate:drive",
                    ]
                ),
                encoding="utf-8",
            )
            scene = YAMLSceneLoader().load(str(path), require_background=False)
            self.assertEqual(scene["regions"][0]["polygon"][0], [10.0, 20.0])


if __name__ == "__main__":
    unittest.main()
