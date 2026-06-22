# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet_interface.core.observation_widget import ObservationWidget


class FakeObservationWidget(ObservationWidget):
    def render(self, surface, x, y):
        return self.snapshot()


class TestObservationWidget(unittest.TestCase):
    def test_accepts_sanitized_observations(self):
        widget = FakeObservationWidget("vehicle-signals", max_values=4)
        widget.update_observations([
            {
                "signal_name": "wheel_speed",
                "value": 42.3,
                "confidence": 0.91,
                "observed_at": 10.0,
                "source_profile": "profile-abc",
                "unit": "km/h",
                "status": "observation-only",
                "read_only": True,
                "actuation_granted": False,
                "actuation_performed": False,
            }
        ])

        snapshot = widget.snapshot(now=11.0, stale_after_s=2.0)

        self.assertEqual(snapshot["value_count"], 1)
        self.assertEqual(snapshot["values"][0]["name"], "wheel_speed")
        self.assertEqual(snapshot["values"][0]["freshness"], "fresh")
        self.assertEqual(snapshot["values"][0]["quality"], "validated")
        self.assertFalse(snapshot["actuation_granted"])
        self.assertFalse(snapshot["actuation_performed"])

    def test_marks_old_values_stale_and_low_confidence_provisional(self):
        widget = FakeObservationWidget("vehicle-signals")
        widget.update_observations([
            {
                "name": "gear",
                "value": 3,
                "confidence": 0.55,
                "timestamp": 1.0,
                "source_profile": "profile-abc",
                "status": "observation-only",
                "read_only": True,
                "actuation_granted": False,
                "actuation_performed": False,
            }
        ])

        snapshot = widget.snapshot(now=10.0, stale_after_s=2.0)

        self.assertEqual(snapshot["values"][0]["freshness"], "stale")
        self.assertEqual(snapshot["values"][0]["quality"], "provisional")

    def test_rejects_authority_fields(self):
        widget = FakeObservationWidget("vehicle-signals")

        with self.assertRaisesRegex(ValueError, "forbidden authority fields"):
            widget.update_observations([
                {
                    "name": "gear",
                    "value": 3,
                    "confidence": 1.0,
                    "observed_at": 1.0,
                    "source_profile": "profile-abc",
                    "status": "observation-only",
                    "read_only": True,
                    "actuation_granted": False,
                    "actuation_performed": False,
                    "executor_name": "can-writer",
                }
            ])

    def test_rejects_false_safety_claims(self):
        widget = FakeObservationWidget("vehicle-signals")

        with self.assertRaisesRegex(ValueError, "read_only"):
            widget.update_observations([
                {
                    "name": "gear",
                    "value": 3,
                    "confidence": 1.0,
                    "observed_at": 1.0,
                    "source_profile": "profile-abc",
                    "status": "observation-only",
                    "read_only": False,
                    "actuation_granted": False,
                    "actuation_performed": False,
                }
            ])

    def test_bounds_visible_values(self):
        widget = FakeObservationWidget("vehicle-signals", max_values=2)
        values = []
        for index in range(3):
            values.append({
                "name": "signal-%s" % index,
                "value": index,
                "confidence": 1.0,
                "observed_at": float(index),
                "source_profile": "profile-abc",
                "status": "observation-only",
                "read_only": True,
                "actuation_granted": False,
                "actuation_performed": False,
            })

        widget.update_observations(values)

        self.assertEqual(len(widget.observations), 2)


if __name__ == "__main__":
    unittest.main()
