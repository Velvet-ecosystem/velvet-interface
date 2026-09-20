from pathlib import Path
import unittest

import yaml


class ForgeSurfaceTests(unittest.TestCase):
    def test_forge_surface_maps_five_workstations(self):
        path = Path("examples/surfaces/forge.surface.yaml")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(document["name"], "forge")
        self.assertEqual(document["background"]["image"], "../assets/forge.png")
        self.assertEqual(
            [point["id"] for point in document["press_points"]],
            [
                "return_home",
                "eleanor_engineering",
                "character_foundry",
                "module_lab",
                "test_bench",
                "surface_studio",
                "emergency",
            ],
        )

        expected = {
            "eleanor_engineering": {
                "polygon": [
                    [0.362847, 0.566358],
                    [0.654514, 0.543210],
                    [0.758681, 0.638889],
                    [0.470486, 0.679012],
                ],
                "action": "emit:forge.eleanor.selected",
            },
            "character_foundry": {
                "polygon": [
                    [0.237847, 0.324074],
                    [0.322049, 0.339506],
                    [0.334201, 0.509259],
                    [0.251736, 0.516975],
                ],
                "action": "emit:forge.character_foundry.selected",
            },
            "module_lab": {
                "polygon": [
                    [0.000868, 0.405864],
                    [0.098958, 0.418210],
                    [0.147569, 0.521605],
                    [0.040799, 0.540123],
                ],
                "action": "emit:forge.module_lab.selected",
            },
            "test_bench": {
                "polygon": [
                    [0.908854, 0.578704],
                    [0.967882, 0.609568],
                    [0.963542, 0.740741],
                    [0.909722, 0.703704],
                ],
                "action": "emit:forge.test_bench.selected",
            },
            "surface_studio": {
                "polygon": [
                    [0.006076, 0.699074],
                    [0.050347, 0.688272],
                    [0.260417, 0.827160],
                    [0.004340, 0.919753],
                ],
                "action": "emit:forge.surface_studio.selected",
            },
        }

        points = {point["id"]: point for point in document["press_points"]}
        for point_id, expectation in expected.items():
            with self.subTest(point_id=point_id):
                self.assertEqual(points[point_id]["polygon"], expectation["polygon"])
                self.assertEqual(points[point_id]["action"], expectation["action"])
                self.assertTrue(points[point_id]["enabled"])

        self.assertEqual(points["return_home"]["action"], "navigate:founder_home")
        self.assertEqual(points["emergency"]["action"], "navigate:emergency")
        self.assertEqual(document["metadata"]["physical_control"], "disabled")
        self.assertIn("Five Forge workstations mapped", document["metadata"]["implementation_status"])

    def test_reusable_workspace_scroll_asset_exists(self):
        self.assertTrue(Path("examples/assets/workspace_scroll.png").is_file())
        self.assertTrue(Path("examples/assets/forge.png").is_file())


if __name__ == "__main__":
    unittest.main()
