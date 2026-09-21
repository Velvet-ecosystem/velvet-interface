from pathlib import Path
import unittest

import yaml


class FounderConversationEntryTests(unittest.TestCase):
    def test_velvet_presence_opens_trusted_written_conversation(self):
        document = yaml.safe_load(
            Path("examples/surfaces/founder_home.surface.yaml").read_text(encoding="utf-8")
        )
        points = {point["id"]: point for point in document["press_points"]}
        entry = points["velvet_conversation"]

        self.assertEqual(entry["action"], "navigate:written_conversation")
        self.assertEqual(entry["accessibility_label"], "Talk to Velvet")
        self.assertEqual(
            entry["polygon"],
            [[0.43, 0.07], [0.57, 0.07], [0.57, 0.21], [0.43, 0.21]],
        )
        self.assertTrue(entry["enabled"])
        self.assertEqual(entry["z_index"], 40)
        self.assertEqual(document["metadata"]["physical_control"], "disabled")
        self.assertEqual(document["metadata"]["conversation_entry"], "velvet_presence")

        presence = next(
            widget for widget in document["widgets"]
            if widget["widget_id"] == "velvet_presence"
        )
        self.assertEqual(presence["rect"], [0.43, 0.07, 0.14, 0.14])


if __name__ == "__main__":
    unittest.main()
