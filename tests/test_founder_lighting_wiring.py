# SPDX-License-Identifier: GPL-3.0-only

import unittest
from pathlib import Path

from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader


class FounderLightingWiringTests(unittest.TestCase):
    def test_lighting_surface_places_context_widget_and_stays_non_authoritative(self):
        root = Path(__file__).resolve().parents[1]
        scene = YAMLSceneLoader().load(
            str(root / "examples/surfaces/lighting.surface.yaml"),
            require_background=True,
        )
        widgets = {item["widget_id"]: item for item in scene["widgets"]}
        self.assertIn("lighting_context_status", widgets)
        self.assertIn("owner", widgets["lighting_context_status"]["visible_in"])
        self.assertIn("service", widgets["lighting_context_status"]["visible_in"])

        metadata = scene["metadata"]
        self.assertEqual(metadata["posture"], "presentation-only")
        self.assertEqual(metadata["physical_control"], "disabled")

        actions = {region["action"] for region in scene["regions"]}
        self.assertEqual(
            actions,
            {"navigate:founder_home", "navigate:emergency"},
        )


if __name__ == "__main__":
    unittest.main()
