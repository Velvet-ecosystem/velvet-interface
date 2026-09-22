# SPDX-License-Identifier: GPL-3.0-only

import unittest
from pathlib import Path

from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader


class FounderBackroomWiringTests(unittest.TestCase):
    def test_backroom_uses_existing_read_only_diagnostic_widgets(self):
        root = Path(__file__).resolve().parents[1]
        scene = YAMLSceneLoader().load(
            str(root / "examples/surfaces/backroom.surface.yaml"),
            require_background=True,
        )
        widget_ids = {item["widget_id"] for item in scene["widgets"]}
        self.assertEqual(
            widget_ids,
            {
                "founder_body_status",
                "gnss_status",
                "vehicle_power_status",
                "microphone_input_status",
                "seat_presence_status",
                "nfc_status",
            },
        )
        for item in scene["widgets"]:
            self.assertIn("owner", item["visible_in"])
            self.assertIn("service", item["visible_in"])

        metadata = scene["metadata"]
        self.assertEqual(metadata["posture"], "presentation-only")
        self.assertFalse(metadata["physical_control"])

        actions = {region["action"] for region in scene["regions"]}
        self.assertEqual(
            actions,
            {"navigate:founder_home", "navigate:emergency"},
        )


if __name__ == "__main__":
    unittest.main()
