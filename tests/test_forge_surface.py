from pathlib import Path
import unittest

import yaml


class ForgeSurfaceTests(unittest.TestCase):
    def test_forge_surface_uses_new_artwork_and_mapped_eleanor_desk(self):
        path = Path("examples/surfaces/forge.surface.yaml")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(document["name"], "forge")
        self.assertEqual(document["background"]["image"], "../assets/forge.png")
        self.assertEqual(
            [point["id"] for point in document["press_points"]],
            ["return_home", "eleanor_engineering", "emergency"],
        )
        eleanor = next(
            point for point in document["press_points"]
            if point["id"] == "eleanor_engineering"
        )
        self.assertEqual(
            eleanor["polygon"],
            [
                [0.362847, 0.566358],
                [0.654514, 0.543210],
                [0.758681, 0.638889],
                [0.470486, 0.679012],
            ],
        )
        self.assertEqual(eleanor["action"], "emit:forge.eleanor.selected")
        self.assertEqual(eleanor["label"], "Eleanor Engineering")
        self.assertTrue(eleanor["enabled"])
        self.assertEqual(document["metadata"]["physical_control"], "disabled")
        self.assertIn("remaining Forge tool points", document["metadata"]["implementation_status"])

    def test_reusable_workspace_scroll_asset_exists(self):
        self.assertTrue(Path("examples/assets/workspace_scroll.png").is_file())
        self.assertTrue(Path("examples/assets/forge.png").is_file())


if __name__ == "__main__":
    unittest.main()
