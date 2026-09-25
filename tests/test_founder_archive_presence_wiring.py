from pathlib import Path
import unittest

import yaml


class FounderArchivePresenceWiringTests(unittest.TestCase):
    def test_archive_room_maps_real_furniture_and_opens_trusted_library_reader(self):
        path = Path("examples/surfaces/archive.surface.yaml")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        points = {point["id"]: point for point in document["press_points"]}

        self.assertEqual(points["open_library"]["action"], "navigate:library_reader")
        self.assertTrue(points["open_library"]["enabled"])
        self.assertEqual(
            points["open_library"]["polygon"],
            [
                [0.374219, 0.762500],
                [0.555469, 0.759722],
                [0.567969, 0.894444],
                [0.357812, 0.894444],
            ],
        )

        self.assertEqual(
            points["open_web_research"]["polygon"],
            [
                [0.776563, 0.469444],
                [0.825781, 0.477778],
                [0.785937, 0.551389],
                [0.745313, 0.531944],
            ],
        )
        self.assertEqual(
            points["open_web_research"]["action"],
            "navigate:velour_web_research",
        )
        self.assertTrue(points["open_web_research"]["enabled"])

        expected_reserved = {
            "open_receipts_continuity": [
                [0.861719, 0.698611],
                [0.939063, 0.683333],
                [0.942187, 0.798611],
                [0.917969, 0.805556],
            ],
            "open_catalog_research": [
                [0.709375, 0.406944],
                [0.745313, 0.406944],
                [0.744531, 0.495833],
                [0.710938, 0.487500],
            ],
            "velour_front_desk": [
                [0.463281, 0.433333],
                [0.494531, 0.434722],
                [0.564844, 0.487500],
                [0.396875, 0.484722],
            ],
            "open_archive_search": [
                [0.605469, 0.776389],
                [0.659375, 0.772222],
                [0.682031, 0.887500],
                [0.679687, 0.891667],
            ],
        }
        for point_id, polygon in expected_reserved.items():
            with self.subTest(point_id=point_id):
                self.assertIn(point_id, points)
                self.assertEqual(points[point_id]["polygon"], polygon)
                self.assertFalse(points[point_id]["enabled"])
                self.assertTrue(points[point_id]["action"].startswith("emit:"))

        self.assertEqual(document["metadata"]["physical_control"], "disabled")

    def test_web_research_surface_uses_scroll_and_measured_writing_area(self):
        path = Path("examples/surfaces/velour_web_research.surface.yaml")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        points = {point["id"]: point for point in document["press_points"]}
        widgets = {item["widget_id"]: item for item in document["widgets"]}

        self.assertEqual(document["background"]["image"], "../assets/workspace_scroll.png")
        self.assertEqual(points["return_archive"]["action"], "navigate:archive")
        self.assertEqual(points["emergency"]["action"], "navigate:emergency")
        self.assertEqual(
            widgets["velour_web_research"]["rect"],
            [0.175347, 0.180000, 0.647570, 0.590062],
        )
        self.assertEqual(document["metadata"]["authority"], "none")
        self.assertEqual(document["metadata"]["network_adapter"], "disconnected")
        self.assertFalse(document["metadata"]["scripts_executed"])
        self.assertFalse(document["metadata"]["automatic_library_persistence"])

    def test_home_declares_velvet_presence_without_replacing_conversation_entry(self):
        path = Path("examples/surfaces/founder_home.surface.yaml")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        widgets = {item["widget_id"]: item for item in document["widgets"]}
        points = {point["id"]: point for point in document["press_points"]}

        self.assertIn("velvet_presence", widgets)
        self.assertEqual(
            points["velvet_conversation"]["action"],
            "navigate:written_conversation",
        )
        self.assertEqual(document["metadata"]["physical_control"], "disabled")

    def test_launcher_registers_presence_and_library_as_presentation_boundaries(self):
        launcher = Path("velvet_interface/founder_surface_launcher.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("QtVelvetPresenceWidget", launcher)
        self.assertIn('widget_id == "velvet_presence"', launcher)
        self.assertIn("register_library_reader", launcher)
        self.assertIn('"library_reader"', launcher)


if __name__ == "__main__":
    unittest.main()
