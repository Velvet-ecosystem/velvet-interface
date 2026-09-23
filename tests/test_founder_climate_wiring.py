# SPDX-License-Identifier: GPL-3.0-only

import unittest
from pathlib import Path

from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader


class FounderClimateWiringTests(unittest.TestCase):
    def test_climate_surface_places_read_only_environment_widget(self):
        root = Path(__file__).resolve().parents[1]
        scene = YAMLSceneLoader().load(
            str(root / "examples/surfaces/climate.surface.yaml"),
            require_background=True,
        )
        widgets = scene.get("widgets", [])
        self.assertEqual(len(widgets), 1)
        self.assertEqual(widgets[0]["widget_id"], "climate_environment_status")
        self.assertEqual(tuple(widgets[0]["visible_in"]), ("owner", "service"))

        metadata = scene.get("metadata", {})
        self.assertEqual(metadata.get("posture"), "presentation-only")
        self.assertEqual(metadata.get("physical_control"), "disabled")

    def test_existing_climate_touchpoints_remain_navigation_or_evidence_only(self):
        root = Path(__file__).resolve().parents[1]
        scene = YAMLSceneLoader().load(
            str(root / "examples/surfaces/climate.surface.yaml"),
            require_background=True,
        )
        actions = [region.get("action", "") for region in scene.get("regions", [])]
        self.assertTrue(actions)
        self.assertTrue(all(action.startswith(("navigate:", "emit:")) for action in actions))


if __name__ == "__main__":
    unittest.main()
