import unittest

from velvet_interface.core.body_state import BodyStateStore
from velvet_interface.scenes.diagnostics_scene import DiagnosticsScene


def sensor_record():
    payload = {
        "module_id": "gnss-main",
        "node_id": "founder-up2",
        "owning_handmaiden": "Navigator",
        "timestamp": 100.0,
        "monotonic_time": 10.0,
        "sensor_type": "gnss",
        "interface_type": "uart",
        "health_state": "ONLINE",
        "confidence": 0.97,
        "payload": {"latitude": 43.0, "longitude": -79.0},
        "receipt_id": "receipt-sensor-1",
        "source_clock": "gnss",
        "stale_after_ms": 1000,
        "calibration_version": "m9n-v1",
        "degraded_reason": None,
        "raw_reference": "nmea:1",
    }
    return {
        "event_id": payload["receipt_id"],
        "event_type": "SENSOR_PACKET_OBSERVED",
        "source": payload["module_id"],
        "family": "sensor",
        "schema_version": "1.0",
        "timestamp": payload["timestamp"],
        "payload": payload,
    }


def health_record():
    payload = {
        "event_id": "health-1",
        "event_type": "DEGRADED",
        "module_id": "gnss-main",
        "node_id": "founder-up2",
        "owning_handmaiden": "Navigator",
        "timestamp": 101.0,
        "severity": "WARNING",
        "state_before": "ONLINE",
        "state_after": "DEGRADED",
        "confidence": 1.0,
        "diagnostic_payload": {"reason": "satellites-low"},
        "receipt_id": "receipt-health-1",
        "recovery_action": "continue observation",
        "fallback_owner": "Velvet",
    }
    return {
        "event_id": payload["event_id"],
        "event_type": "HEALTH_DEGRADED",
        "source": payload["module_id"],
        "family": "health",
        "schema_version": "1.0",
        "timestamp": payload["timestamp"],
        "payload": payload,
    }


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
