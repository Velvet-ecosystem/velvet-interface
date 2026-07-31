import unittest

from velvet_interface.core.body_state import BodyStateStore
from velvet_interface.scenes.diagnostics_scene import DiagnosticsScene
from tests.test_body_state import health_record, sensor_record


class DiagnosticsSceneTests(unittest.TestCase):
    def test_without_provider_reports_waiting_state(self):
        scene = DiagnosticsScene()
        scene.on_enter()
        snapshot = scene.status_snapshot()

        self.assertEqual(snapshot["status"]["Body"], "Awaiting Runtime body state")
        self.assertTrue(snapshot["read_only"])
        self.assertFalse(snapshot["actuation_granted"])

    def test_provider_populates_real_counts(self):
        store = BodyStateStore()
        store.apply_many([sensor_record(), health_record()])
        scene = DiagnosticsScene(body_state_provider=lambda: store.snapshot())

        scene.on_enter()
        status = scene.status_snapshot()["status"]

        self.assertEqual(status["Presence"], "WARNING")
        self.assertEqual(status["Sensors"], "1")
        self.assertEqual(status["Health records"], "1")
        self.assertEqual(status["Receipts"], "2")
        self.assertEqual(status["Physical control"], "DISABLED")

    def test_provider_failure_is_presented_honestly(self):
        def broken_provider():
            raise RuntimeError("runtime socket unavailable")

        scene = DiagnosticsScene(body_state_provider=broken_provider)
        scene.on_enter()
        status = scene.status_snapshot()["status"]

        self.assertEqual(status["Body"], "STATE UNAVAILABLE")
        self.assertIn("runtime socket unavailable", status["Detail"])

    def test_rejects_authoritative_snapshot_claim(self):
        scene = DiagnosticsScene(
            body_state_provider=lambda: {
                "summary": "bad",
                "presence_state": "working",
                "sensors": [],
                "health_events": [],
                "receipt_ids": [],
                "read_only": True,
                "actuation_granted": True,
                "actuation_performed": False,
            }
        )
        scene.on_enter()
        self.assertEqual(scene.status_snapshot()["status"]["Body"], "STATE UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
