import unittest

from velvet_interface.core.body_state import BodyStateStore


def sensor_record(**overrides):
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
    payload.update(overrides)
    return {
        "event_id": payload["receipt_id"],
        "event_type": "SENSOR_PACKET_OBSERVED",
        "source": payload["module_id"],
        "family": "sensor",
        "schema_version": "1.0",
        "timestamp": payload["timestamp"],
        "payload": payload,
    }


def health_record(**overrides):
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
    payload.update(overrides)
    return {
        "event_id": payload["event_id"],
        "event_type": "HEALTH_%s" % payload["event_type"],
        "source": payload["module_id"],
        "family": "health",
        "schema_version": "1.0",
        "timestamp": payload["timestamp"],
        "payload": payload,
    }


class BodyStateStoreTests(unittest.TestCase):
    def test_projects_sensor_health_receipts_and_staleness(self):
        store = BodyStateStore()
        store.apply_many([sensor_record(), health_record()])

        snapshot = store.snapshot(now_monotonic=11.5)
        rendered = snapshot.to_dict(now_monotonic=11.5)

        self.assertEqual(snapshot.presence_state, "warning")
        self.assertEqual(rendered["sensors"][0]["freshness"], "stale")
        self.assertEqual(
            rendered["receipt_ids"],
            ["receipt-sensor-1", "receipt-health-1"],
        )
        self.assertTrue(rendered["read_only"])
        self.assertFalse(rendered["actuation_granted"])

    def test_latest_record_replaces_same_module(self):
        store = BodyStateStore()
        store.apply(sensor_record(confidence=0.4, receipt_id="old"))
        store.apply(sensor_record(confidence=0.9, receipt_id="new"))

        snapshot = store.snapshot()
        self.assertEqual(len(snapshot.sensors), 1)
        self.assertEqual(snapshot.sensors[0].confidence, 0.9)
        self.assertEqual(snapshot.sensors[0].receipt_id, "new")

    def test_failed_health_creates_critical_presence(self):
        store = BodyStateStore()
        store.apply(
            health_record(
                event_type="FAILED",
                severity="CRITICAL",
                state_after="FAILED",
            )
        )
        self.assertEqual(store.snapshot().presence_state, "critical")

    def test_rejects_nested_authority_fields(self):
        store = BodyStateStore()
        record = sensor_record()
        record["payload"]["payload"]["executor_name"] = "forbidden"
        with self.assertRaises(ValueError):
            store.apply(record)

    def test_rejects_unknown_family(self):
        store = BodyStateStore()
        with self.assertRaises(ValueError):
            store.apply({"family": "command", "event_type": "DO", "payload": {}})


if __name__ == "__main__":
    unittest.main()
