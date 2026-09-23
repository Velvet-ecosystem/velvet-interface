from pathlib import Path
import unittest

import yaml


class ForgeSurfaceTests(unittest.TestCase):
    def test_forge_surface_maps_six_workstations(self):
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
                "engineering_design",
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
                "action": "navigate:eleanor_engineering",
            },
            "character_foundry": {
                "polygon": [
                    [0.237847, 0.324074],
                    [0.322049, 0.339506],
                    [0.334201, 0.509259],
                    [0.251736, 0.516975],
                ],
                "action": "navigate:character_foundry",
            },
            "engineering_design": {
                "polygon": [
                    [0.001736, 0.401235],
                    [0.093750, 0.416667],
                    [0.150174, 0.529321],
                    [0.039062, 0.533951],
                ],
                "action": "navigate:engineering_design",
            },
            "module_lab": {
                "polygon": [
                    [0.848958, 0.365741],
                    [0.993924, 0.348765],
                    [0.989583, 0.523148],
                    [0.847222, 0.516975],
                ],
                "action": "navigate:module_lab",
            },
            "test_bench": {
                "polygon": [
                    [0.908854, 0.578704],
                    [0.967882, 0.609568],
                    [0.963542, 0.740741],
                    [0.909722, 0.703704],
                ],
                "action": "navigate:test_bench",
            },
            "surface_studio": {
                "polygon": [
                    [0.006076, 0.699074],
                    [0.050347, 0.688272],
                    [0.260417, 0.827160],
                    [0.004340, 0.919753],
                ],
                "action": "navigate:surface_studio",
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
        self.assertIn("dedicated Founder surface", document["metadata"]["implementation_status"])

    def test_live_scroll_workspaces_are_presentation_only(self):
        expected_widgets = {
            "engineering_design": "forge_engineering_design",
            "module_lab": "forge_module_lab",
            "test_bench": "forge_test_bench",
        }
        for scene_name, widget_id in expected_widgets.items():
            with self.subTest(scene=scene_name):
                document = yaml.safe_load(
                    Path("examples/surfaces/%s.surface.yaml" % scene_name).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(document["name"], scene_name)
                self.assertEqual(document["background"]["image"], "../assets/workspace_scroll.png")
                self.assertEqual(document["metadata"]["posture"], "presentation-only")
                self.assertEqual(document["metadata"]["physical_control"], "disabled")
                self.assertEqual(document["metadata"]["authority"], "none")
                self.assertEqual(document["widgets"][0]["widget_id"], widget_id)
                self.assertEqual(document["widgets"][0]["rect"], [0.0, 0.0, 1.0, 1.0])
                points = {point["id"]: point for point in document["press_points"]}
                self.assertEqual(points["return_forge"]["action"], "navigate:forge")
                self.assertEqual(points["emergency"]["action"], "navigate:emergency")

    def test_reusable_workspace_scroll_asset_exists(self):
        self.assertTrue(Path("examples/assets/workspace_scroll.png").is_file())
        self.assertTrue(Path("examples/assets/forge.png").is_file())


if __name__ == "__main__":
    unittest.main()
