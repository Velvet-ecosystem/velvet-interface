# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.vehicle_power_live_status import (
    load_vehicle_power_live_status,
)


class VehiclePowerLiveStatusTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            status = load_vehicle_power_live_status(Path(directory) / "missing.json")
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")
        self.assertEqual(status.ignition_state, "UNKNOWN")
        self.assertIsNone(status.voltage_v)

    def test_live_normal_voltage_and_off_ignition_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(12.6, False, "NORMAL", 10.0)])
            status = load_vehicle_power_live_status(path, now_monotonic=10.5)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "ONLINE")
        self.assertEqual(status.ignition_state, "OFF")
        self.assertEqual(status.voltage_band, "NORMAL")
        self.assertAlmostEqual(status.voltage_v, 12.6)
        self.assertEqual(status.freshness, "fresh")

    def test_low_voltage_is_visible_as_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(11.2, True, "LOW", 10.0)])
            status = load_vehicle_power_live_status(path, now_monotonic=10.5)
        self.assertEqual(status.state, "DEGRADED")
        self.assertEqual(status.ignition_state, "ON")
        self.assertIn("low", status.message.lower())

    def test_charging_band_does_not_claim_engine_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record(14.2, False, "CHARGING", 10.0)
            self.assertFalse(record["payload"]["payload"]["engine_running_inferred"])
            _write_snapshot(path, [record])
            status = load_vehicle_power_live_status(path, now_monotonic=10.5)
        self.assertEqual(status.voltage_band, "CHARGING")
        self.assertEqual(status.ignition_state, "OFF")
        self.assertIn("not inferred", status.message.lower())

    def test_last_real_observation_is_labeled_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(12.6, True, "NORMAL", 10.0)])
            status = load_vehicle_power_live_status(path, now_monotonic=14.0)
        self.assertEqual(status.state, "STALE")
        self.assertEqual(status.freshness, "stale")
        self.assertAlmostEqual(status.voltage_v, 12.6)
        self.assertIn("stale", status.message.lower())

    def test_failed_source_has_no_fabricated_voltage_or_ignition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_health_record()])
            status = load_vehicle_power_live_status(path, now_monotonic=10.0)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "FAILED")
        self.assertEqual(status.ignition_state, "UNKNOWN")
        self.assertIsNone(status.voltage_v)
        self.assertIn("missing", status.message.lower())

    def test_invalid_ignition_value_rejects_entire_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record(12.6, True, "NORMAL", 10.0)
            record["payload"]["payload"]["ignition_on"] = "yes"
            _write_snapshot(path, [record])
            status = load_vehicle_power_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")


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


def _sensor_record(voltage, ignition_on, band, monotonic_time):
    healthy = band in {"NORMAL", "CHARGING"}
    return {
        "event_id": "power-sensor-receipt",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": "vehicle-power-main",
            "node_id": "founder-up2",
            "owning_handmaiden": "Ruby",
            "timestamp": 100.0,
            "monotonic_time": monotonic_time,
            "sensor_type": "vehicle_power_state",
            "interface_type": "read-only-value-files",
            "health_state": "ONLINE" if healthy else "DEGRADED",
            "confidence": 0.98,
            "payload": {
                "voltage_v": voltage,
                "ignition_on": ignition_on,
                "ignition_state": "ON" if ignition_on else "OFF",
                "voltage_band": band,
                "nominal_voltage_v": 12.0,
                "engine_running_inferred": False,
                "read_only": True,
            },
            "receipt_id": "power-sensor-receipt",
            "source_clock": "device",
            "stale_after_ms": 1000,
            "calibration_version": "vehicle-power-v1",
            "degraded_reason": None if healthy else "VOLTAGE_%s" % band,
            "raw_reference": "local:test",
        },
    }


def _health_record():
    return {
        "event_id": "power-health-receipt",
        "event_type": "HEALTH_FAILED",
        "family": "health",
        "payload": {
            "event_id": "power-health-receipt",
            "event_type": "FAILED",
            "module_id": "vehicle-power-main",
            "node_id": "founder-up2",
            "owning_handmaiden": "Ruby",
            "timestamp": 100.0,
            "severity": "ERROR",
            "state_before": "ONLINE",
            "state_after": "FAILED",
            "confidence": 1.0,
            "diagnostic_payload": {
                "detail": "Vehicle voltage input missing",
                "reason_code": "POWER_SOURCE_FAILURE",
                "read_only": True,
            },
            "receipt_id": "power-health-receipt",
            "recovery_action": "continue read-only vehicle power observation",
            "fallback_owner": "Velvet",
        },
    }


if __name__ == "__main__":
    unittest.main()
