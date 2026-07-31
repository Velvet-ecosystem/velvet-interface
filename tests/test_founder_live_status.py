import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.founder_live_status import load_founder_live_status


def boot_snapshot():
    return {
        "doctor": {"ready": True, "state": "ready", "checks": [], "errors": []},
        "service": {"active_state": "active", "sub_state": "running"},
        "route_count": 2,
    }


def sensor_record(monotonic_time=10.0):
    return {
        "event_id": "sensor-r1",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "source": "can-observer",
        "family": "sensor",
        "schema_version": "1.0",
        "timestamp": 10.0,
        "payload": {
            "module_id": "can-observer",
            "node_id": "founder-up2",
            "owning_handmaiden": "Ruby",
            "timestamp": 10.0,
            "monotonic_time": monotonic_time,
            "sensor_type": "can_frame",
            "interface_type": "socketcan",
            "health_state": "ONLINE",
            "confidence": 1.0,
            "payload": {
                "can_id": 291,
                "read_only": True,
                "actuation_granted": False,
                "actuation_performed": False,
            },
            "receipt_id": "sensor-r1",
            "source_clock": "device",
            "stale_after_ms": 2000,
            "calibration_version": "v1",
        },
    }


def health_record(state_after="ONLINE"):
    event_type = "STALE" if state_after == "DEGRADED" else "ONLINE"
    return {
        "event_id": "health-e1",
        "event_type": "HEALTH_%s" % event_type,
        "source": "can-observer",
        "family": "health",
        "schema_version": "1.0",
        "timestamp": 11.0,
        "payload": {
            "event_id": "health-e1",
            "event_type": event_type,
            "module_id": "can-observer",
            "node_id": "founder-up2",
            "owning_handmaiden": "Ruby",
            "timestamp": 11.0,
            "severity": "WARNING" if state_after == "DEGRADED" else "INFO",
            "state_before": "ONLINE" if state_after == "DEGRADED" else "UNKNOWN",
            "state_after": state_after,
            "confidence": 1.0,
            "diagnostic_payload": {"read_only": True},
            "receipt_id": "health-r1",
        },
    }


def write_snapshots(root, records, **overrides):
    boot_path = root / "boot.json"
    body_path = root / "body.json"
    boot_path.write_text(json.dumps(boot_snapshot()), encoding="utf-8")
    document = {
        "schema": "velvet.runtime.body_state_snapshot.v1",
        "read_only": True,
        "authority": "none",
        "actuation_granted": False,
        "actuation_performed": False,
        "records": records,
    }
    document.update(overrides)
    body_path.write_text(json.dumps(document), encoding="utf-8")
    return boot_path, body_path


class FounderLiveStatusTests(unittest.TestCase):
    def test_combines_boot_and_body_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            boot_path, body_path = write_snapshots(
                root,
                [sensor_record(), health_record()],
            )
            model = load_founder_live_status(
                boot_path,
                body_path,
                now_monotonic=11.0,
            )

            self.assertTrue(model.body_available)
            self.assertEqual(model.sensor_count, 1)
            self.assertEqual(model.health_event_count, 1)
            self.assertEqual(model.receipt_count, 2)
            self.assertIn(("Body", "OBSERVING"), model.rows())
            self.assertIn("Waiting for Mister", model.message)

    def test_missing_body_snapshot_is_honest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            boot_path = root / "boot.json"
            boot_path.write_text(json.dumps(boot_snapshot()), encoding="utf-8")

            model = load_founder_live_status(
                boot_path,
                root / "missing.json",
            )

            self.assertFalse(model.body_available)
            self.assertIn("awaiting", model.body_error.lower())
            self.assertIn(("Body", "UNAVAILABLE"), model.rows())

    def test_authority_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            boot_path, body_path = write_snapshots(
                root,
                [],
                authority="court",
            )

            model = load_founder_live_status(boot_path, body_path)

            self.assertFalse(model.body_available)
            self.assertIn("cannot carry authority", model.body_error)

    def test_stale_sensor_recommends_warning_presence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            boot_path, body_path = write_snapshots(
                root,
                [sensor_record(monotonic_time=1.0)],
            )

            model = load_founder_live_status(
                boot_path,
                body_path,
                now_monotonic=10.0,
            )

            self.assertEqual(model.body_presence, "warning")
            self.assertIn("stale", model.body_summary)


if __name__ == "__main__":
    unittest.main()
