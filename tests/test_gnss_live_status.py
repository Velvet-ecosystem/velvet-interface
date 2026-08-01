# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.gnss_live_status import load_gnss_live_status


class GnssLiveStatusTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            status = load_gnss_live_status(Path(directory) / "missing.json")
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")
        self.assertEqual(status.fix_label, "NO DATA")

    def test_live_fix_is_projected_without_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(True, 10.0)])
            status = load_gnss_live_status(path, now_monotonic=10.5)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "ONLINE")
        self.assertEqual(status.fix_label, "FIX")
        self.assertAlmostEqual(status.latitude, 43.6532, places=6)
        self.assertAlmostEqual(status.longitude, -79.3832, places=6)
        self.assertEqual(status.satellites, 12)
        self.assertEqual(status.freshness, "fresh")

    def test_no_fix_never_projects_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record(False, 10.0)
            record["payload"]["payload"].pop("latitude")
            record["payload"]["payload"].pop("longitude")
            _write_snapshot(path, [record])
            status = load_gnss_live_status(path, now_monotonic=10.5)
        self.assertEqual(status.state, "DEGRADED")
        self.assertEqual(status.fix_label, "NO FIX")
        self.assertIsNone(status.latitude)
        self.assertIsNone(status.longitude)
        self.assertIn("waiting", status.message.lower())

    def test_last_real_fix_is_labeled_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(True, 10.0)])
            status = load_gnss_live_status(path, now_monotonic=14.0)
        self.assertEqual(status.state, "STALE")
        self.assertEqual(status.fix_label, "FIX")
        self.assertEqual(status.freshness, "stale")
        self.assertIsNotNone(status.latitude)
        self.assertIn("stale", status.message.lower())

    def test_failed_health_is_visible_without_sensor_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_health_record()])
            status = load_gnss_live_status(path, now_monotonic=10.0)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "FAILED")
        self.assertEqual(status.fix_label, "NO DATA")
        self.assertIn("disconnected", status.message)


def _write_snapshot(path: Path, records) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "velvet.runtime.body_state_snapshot.v1",
                "read_only": True,
                "authority": "none",
                "actuation_granted": False,
                "actuation_performed": False,
                "records": records,
            }
        ),
        encoding="utf-8",
    )


def _sensor_record(has_fix: bool, monotonic_time: float):
    payload = {
        "has_fix": has_fix,
        "latitude": 43.6532,
        "longitude": -79.3832,
        "satellites": 12,
        "horizontal_dilution": 0.8,
        "speed_kmh": 22.5,
        "course_deg": 180.0,
    }
    return {
        "event_id": "gnss-sensor-receipt",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": "gnss-main",
            "node_id": "founder-up2",
            "owning_handmaiden": "Navigator",
            "timestamp": 100.0,
            "monotonic_time": monotonic_time,
            "sensor_type": "gnss_fix",
            "interface_type": "serial-nmea",
            "health_state": "ONLINE" if has_fix else "DEGRADED",
            "confidence": 0.9 if has_fix else 0.2,
            "payload": payload,
            "receipt_id": "gnss-sensor-receipt",
            "source_clock": "gnss",
            "stale_after_ms": 1000,
            "calibration_version": "neo-m9n-nmea-v1",
            "degraded_reason": None if has_fix else "NO_FIX",
            "raw_reference": "nmea:GGA",
        },
    }


def _health_record():
    return {
        "event_id": "gnss-health-receipt",
        "event_type": "HEALTH_FAILED",
        "family": "health",
        "payload": {
            "event_id": "gnss-health-receipt",
            "event_type": "FAILED",
            "module_id": "gnss-main",
            "node_id": "founder-up2",
            "owning_handmaiden": "Navigator",
            "timestamp": 100.0,
            "severity": "ERROR",
            "state_before": "ONLINE",
            "state_after": "FAILED",
            "confidence": 1.0,
            "diagnostic_payload": {"detail": "GNSS port disconnected"},
            "receipt_id": "gnss-health-receipt",
            "recovery_action": "continue read-only GNSS observation",
            "fallback_owner": "Velvet",
        },
    }


if __name__ == "__main__":
    unittest.main()
