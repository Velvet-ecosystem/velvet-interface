import unittest
from velvet_interface.core.observation_widget import ObservationWidget

class FakeObservationWidget(ObservationWidget):
    def render(self, surface, x, y):
        return self.snapshot()

class TestObservationWidget(unittest.TestCase):
    def test_accepts_and_marks_state(self):
        widget = FakeObservationWidget("vehicle-signals", max_values=2)
        widget.update_observations([{
            "signal_name": "wheel_speed", "value": 42.3, "confidence": 0.91,
            "observed_at": 10.0, "source_profile": "profile-abc", "unit": "km/h",
            "status": "observation-only", "read_only": True,
            "actuation_granted": False, "actuation_performed": False,
        }])
        snapshot = widget.snapshot(now=11.0, stale_after_s=2.0)
        self.assertEqual(snapshot["values"][0]["freshness"], "fresh")
        self.assertEqual(snapshot["values"][0]["quality"], "validated")
        self.assertFalse(snapshot["actuation_granted"])

    def test_rejects_forbidden_fields(self):
        widget = FakeObservationWidget("vehicle-signals")
        payload = {
            "name": "gear", "value": 3, "confidence": 1.0,
            "observed_at": 1.0, "source_profile": "profile-abc",
            "status": "observation-only", "read_only": True,
            "actuation_granted": False, "actuation_performed": False,
            "route_id": "forbidden",
        }
        with self.assertRaises(ValueError):
            widget.update_observations([payload])

    def test_bounds_values(self):
        widget = FakeObservationWidget("vehicle-signals", max_values=1)
        base = {"confidence": 1.0, "observed_at": 1.0, "source_profile": "p",
                "status": "observation-only", "read_only": True,
                "actuation_granted": False, "actuation_performed": False}
        widget.update_observations([dict(base, name="a", value=1), dict(base, name="b", value=2)])
        self.assertEqual(len(widget.observations), 1)

if __name__ == "__main__":
    unittest.main()
