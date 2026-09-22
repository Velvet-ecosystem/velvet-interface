from pathlib import Path
import unittest

import yaml


class FounderRoomLiveWidgetTests(unittest.TestCase):
    def _load(self, name: str):
        path = Path("examples/surfaces") / (name + ".surface.yaml")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_vehicle_surface_places_read_only_power_and_gnss_evidence(self):
        document = self._load("vehicle")
        widgets = {item["widget_id"]: item for item in document["widgets"]}

        self.assertEqual(set(widgets), {"vehicle_power_status", "gnss_status"})
        for widget in widgets.values():
            self.assertEqual(widget["coordinate_space"], "normalized")
            self.assertEqual(widget["visible_in"], ["owner", "service"])
        self.assertEqual(document["metadata"]["physical_control"], "disabled")

    def test_audio_surface_places_microphone_evidence_without_playback_authority(self):
        document = self._load("audio")
        self.assertEqual(
            [item["widget_id"] for item in document["widgets"]],
            ["microphone_input_status"],
        )
        self.assertEqual(document["metadata"]["physical_control"], "disabled")
        self.assertIn("read-only microphone evidence", document["metadata"]["implementation_status"])

    def test_comfort_surface_places_seat_evidence_without_comfort_actuation(self):
        document = self._load("comfort")
        self.assertEqual(
            [item["widget_id"] for item in document["widgets"]],
            ["seat_presence_status"],
        )
        self.assertEqual(document["metadata"]["physical_control"], "disabled")
        self.assertIn("actuation remains disabled", document["metadata"]["implementation_status"])


if __name__ == "__main__":
    unittest.main()
