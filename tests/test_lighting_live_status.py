# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.lighting_live_status import load_lighting_live_status


class LightingLiveStatusTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable_and_unbound(self):
        with tempfile.TemporaryDirectory() as directory:
            status = load_lighting_live_status(Path(directory) / "missing.json")
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")
        self.assertEqual(status.lighting_observer_state, "UNBOUND")
        self.assertEqual(status.physical_control_state, "DISABLED")

    def test_live_ambient_light_is_projected_without_fixture_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(monotonic_time=10.0)])
            status = load_lighting_live_status(path, now_monotonic=10.5)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "ONLINE")
        self.assertEqual(status.ambient_light_lux, 420.0)
        self.assertEqual(status.observer, "Jade")
        self.assertEqual(status.lighting_observer_state, "UNBOUND")
        self.assertEqual(status.physical_control_state, "DISABLED")
        self.assertIn("starlight", status.message.lower())

    def test_stale_ambient_context_is_not_presented_as_live(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(monotonic_time=10.0)])
            status = load_lighting_live_status(path, now_monotonic=20.0)
        self.assertEqual(status.state, "STALE")
        self.assertEqual(status.freshness, "stale")
        self.assertIn("stale", status.message.lower())

    def test_authority_bearing_environment_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record(monotonic_time=10.0)
            record["payload"]["payload"]["control_requested"] = True
            _write_snapshot(path, [record])
            status = load_lighting_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")
        self.assertEqual(status.physical_control_state, "DISABLED")


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


def _sensor_record(monotonic_time: float):
    return {
        "event_id": "lighting-context-receipt",
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
            "confidence": 0.9,
            "payload": {
                "cabin_temperature_c": 22.0,
                "outside_temperature_c": 12.0,
                "ambient_light_lux": 420.0,
                "relative_humidity_percent": 45.0,
                "sample_count": 3,
                "control_requested": False,
                "grants_authority": False,
                "read_only": True,
            },
            "receipt_id": "lighting-context-receipt",
            "source_clock": "device",
            "stale_after_ms": 5000,
            "calibration_version": "environment-reader-v1",
            "raw_reference": "service:environment-reader-service",
        },
    }


if __name__ == "__main__":
    unittest.main()
