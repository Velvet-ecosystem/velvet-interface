# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.climate_live_status import load_climate_live_status


class ClimateLiveStatusTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            status = load_climate_live_status(Path(directory) / "missing.json")
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")

    def test_live_environmental_observation_projects_real_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(10.0)])
            status = load_climate_live_status(path, now_monotonic=11.0)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "ONLINE")
        self.assertEqual(status.cabin_temperature_c, 22.5)
        self.assertEqual(status.outside_temperature_c, 14.0)
        self.assertEqual(status.relative_humidity_percent, 45.0)
        self.assertEqual(status.ambient_light_lux, 400.0)
        self.assertEqual(status.sample_count, 12)
        self.assertEqual(status.owning_handmaiden, "Jade")
        self.assertIn("control remains separate", status.message)

    def test_stale_observation_is_not_presented_as_live(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(10.0)])
            status = load_climate_live_status(path, now_monotonic=20.0)
        self.assertEqual(status.state, "STALE")
        self.assertEqual(status.freshness, "stale")

    def test_failed_health_overrides_old_environmental_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(10.0), _health_record()])
            status = load_climate_live_status(path, now_monotonic=10.5)
        self.assertEqual(status.state, "FAILED")

    def test_authority_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record(10.0)
            record["payload"]["payload"]["grants_authority"] = True
            _write_snapshot(path, [record])
            status = load_climate_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")


def _write_snapshot(path: Path, records) -> None:
    path.write_text(json.dumps({
        "schema": "velvet.runtime.body_state_snapshot.v1",
        "read_only": True,
        "authority": "none",
        "actuation_granted": False,
        "actuation_performed": False,
        "records": records,
    }), encoding="utf-8")


def _sensor_record(monotonic_time: float):
    return {
        "event_id": "climate-sensor-receipt",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": "environmental-sensors",
            "node_id": "founder-up2",
            "owning_handmaiden": "Jade",
            "timestamp": 100.0,
            "monotonic_time": monotonic_time,
            "sensor_type": "environmental_conditions",
            "interface_type": "environment-reader-service",
            "health_state": "ONLINE",
            "confidence": 0.95,
            "payload": {
                "cabin_temperature_c": 22.5,
                "outside_temperature_c": 14.0,
                "ambient_light_lux": 400.0,
                "relative_humidity_percent": 45.0,
                "sample_count": 12,
                "control_requested": False,
                "grants_authority": False,
                "read_only": True,
            },
            "receipt_id": "climate-sensor-receipt",
            "source_clock": "device",
            "stale_after_ms": 5000,
            "calibration_version": "environment-reader-v1",
            "raw_reference": "service:environment-reader-service",
        },
    }


def _health_record():
    return {
        "event_id": "climate-health-receipt",
        "event_type": "HEALTH_FAILED",
        "family": "health",
        "payload": {
            "event_id": "climate-health-receipt",
            "event_type": "FAILED",
            "module_id": "environmental-sensors",
            "node_id": "founder-up2",
            "owning_handmaiden": "Jade",
            "timestamp": 100.0,
            "severity": "ERROR",
            "state_before": "ONLINE",
            "state_after": "FAILED",
            "confidence": 1.0,
            "diagnostic_payload": {"detail": "Environmental sensing failed", "read_only": True},
            "receipt_id": "climate-health-receipt",
            "recovery_action": "continue read-only environmental observation",
            "fallback_owner": "Jade",
        },
    }


if __name__ == "__main__":
    unittest.main()
