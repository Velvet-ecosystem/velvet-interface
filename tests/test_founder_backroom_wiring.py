# SPDX-License-Identifier: GPL-3.0-only

import unittest
from pathlib import Path

import yaml

from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader


class FounderBackroomWiringTests(unittest.TestCase):
    def test_front_room_preserves_backroom_seam(self):
        root = Path(__file__).resolve().parents[1]
        scene = YAMLSceneLoader().load(
            str(root / "examples/surfaces/founder_home.surface.yaml"),
            require_background=True,
        )
        entry = next(region for region in scene["regions"] if region["name"] == "backroom")
        self.assertEqual(entry["action"], "navigate:backroom")
        self.assertEqual(entry["metadata"]["visibility"], "discreet")
        self.assertEqual(
            entry["metadata"]["placement_status"],
            "founder-mapped-2026-09-23",
        )
        self.assertEqual(
            scene["metadata"]["backroom_entry"],
            "founder-mapped-right-edge-seam",
        )

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
        self.assertEqual(metadata["physical_control"], "disabled")

        actions = {region["action"] for region in scene["regions"]}
        self.assertEqual(
            actions,
            {
                "navigate:founder_home",
                "navigate:emergency",
                "emit:backroom.hidden_owner_maintenance.selected",
            },
        )
        self.assertNotIn("navigate:owner_maintenance", actions)

        hidden = next(
            region for region in scene["regions"] if region["name"] == "hidden_owner_maintenance"
        )
        self.assertEqual(hidden["metadata"]["visibility"], "concealed")
        self.assertEqual(hidden["metadata"]["gate"], "owner-plus-maintenance")
        self.assertEqual(
            hidden["metadata"]["placement_status"],
            "founder-mapped-2026-09-23",
        )

    def test_physical_mapping_keeps_bottom_widgets_above_maintenance_target(self):
        root = Path(__file__).resolve().parents[1]
        document = yaml.safe_load(
            (root / "examples/surfaces/backroom.surface.yaml").read_text(
                encoding="utf-8"
            )
        )
        widgets = {item["widget_id"]: item for item in document["widgets"]}
        hidden = next(
            point
            for point in document["press_points"]
            if point["id"] == "hidden_owner_maintenance"
        )
        maintenance_top = min(point[1] for point in hidden["polygon"])

        for widget_id in (
            "microphone_input_status",
            "seat_presence_status",
            "nfc_status",
        ):
            y = widgets[widget_id]["rect"][1]
            height = widgets[widget_id]["rect"][3]
            self.assertLess(y + height, maintenance_top)


if __name__ == "__main__":
    unittest.main()
