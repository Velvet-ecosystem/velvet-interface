from pathlib import Path
import unittest

import yaml


class FounderArchivePresenceWiringTests(unittest.TestCase):
    def test_archive_room_opens_trusted_library_reader(self):
        path = Path("examples/surfaces/archive.surface.yaml")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        points = {point["id"]: point for point in document["press_points"]}

        self.assertEqual(points["open_library"]["action"], "navigate:library_reader")
        self.assertTrue(points["open_library"]["enabled"])
        self.assertEqual(document["metadata"]["physical_control"], "disabled")

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
