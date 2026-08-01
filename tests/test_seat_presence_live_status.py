# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.seat_presence_live_status import load_seat_presence_live_status

class SeatPresenceLiveStatusTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            status = load_seat_presence_live_status(Path(directory) / "missing.json")
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")

    def test_multiple_seats_preserve_positive_and_no_detection_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [
                _sensor_record("driver", True, False, True, 75, 10.0),
                _sensor_record("front-passenger", False, False, False, None, 10.0),
            ])
            status = load_seat_presence_live_status(path, now_monotonic=10.5)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "ONLINE")
        self.assertEqual([seat.seat_id for seat in status.seats], ["driver", "front-passenger"])
        self.assertEqual(status.seats[0].state, "RADAR_PRESENT")
        self.assertEqual(status.seats[0].movement_state, "STATIONARY")
        self.assertEqual(status.seats[1].state, "NO_RADAR_PRESENCE")
        self.assertIn("not inferred", status.seats[1].message.lower())

    def test_stale_is_visible_without_erasing_last_real_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record("driver", True, True, False, 60, 10.0)])
            status = load_seat_presence_live_status(path, now_monotonic=15.0)
        self.assertEqual(status.state, "DEGRADED")
        self.assertEqual(status.seats[0].state, "STALE")
        self.assertEqual(status.seats[0].detection_distance_cm, 60)

    def test_failed_health_without_sensor_is_displayed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_health_record("driver")])
            status = load_seat_presence_live_status(path, now_monotonic=10.0)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "FAILED")
        self.assertEqual(status.seats[0].state, "FAILED")

    def test_unsafe_inference_claim_rejects_entire_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record("driver", False, False, False, None, 10.0)
            record["payload"]["payload"]["no_detection_means_empty"] = True
            _write_snapshot(path, [record])
            status = load_seat_presence_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)

    def test_duplicate_seat_and_contradictory_movement_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            one = _sensor_record("driver", True, False, True, 75, 10.0)
            two = _sensor_record("driver", True, True, False, 60, 10.1)
            two["payload"]["module_id"] = "seat-presence-driver-second"
            _write_snapshot(path, [one, two])
            self.assertFalse(load_seat_presence_live_status(path, now_monotonic=10.5).available)
            bad = _sensor_record("driver", True, False, True, 75, 10.0)
            bad["payload"]["payload"]["movement_state"] = "MOVING"
            _write_snapshot(path, [bad])
            status = load_seat_presence_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)

def _write_snapshot(path, records):
    path.write_text(json.dumps({
        "schema": "velvet.runtime.body_state_snapshot.v1",
        "read_only": True,
        "authority": "none",
        "actuation_granted": False,
        "actuation_performed": False,
        "records": records,
    }), encoding="utf-8")

def _sensor_record(seat_id, present, moving, stationary, distance, monotonic_time):
    module_id = "seat-presence-%s" % seat_id
    movement = "MOVING_AND_STATIONARY" if moving and stationary else (
        "MOVING" if moving else "STATIONARY" if stationary else "NO_RADAR_PRESENCE")
    return {
        "event_id": module_id + "-receipt", "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": module_id, "node_id": "seat-node-%s" % seat_id,
            "owning_handmaiden": "Temperance", "timestamp": 100.0,
            "monotonic_time": monotonic_time, "sensor_type": "seat_presence_radar",
            "interface_type": "read-only-serial-json", "health_state": "ONLINE",
            "confidence": 0.9 if present else 0.65,
            "payload": {
                "seat_id": seat_id, "source_id": "seat.radar.%s" % seat_id,
                "sensor_model": "HLK-LD2410C", "firmware_version": "seat-node-0.1.0",
                "node_boot_id": "boot-a", "sequence": 4, "node_uptime_ms": 1000,
                "radar_presence_detected": present, "moving_target_detected": moving,
                "stationary_target_detected": stationary, "movement_state": movement,
                "detection_distance_cm": distance,
                "moving_distance_cm": distance if moving else None,
                "stationary_distance_cm": distance if stationary else None,
                "moving_energy": 30 if moving else 0,
                "stationary_energy": 30 if stationary else 0,
                "no_detection_means_empty": False, "seat_occupancy_inferred": False,
                "occupant_identity_inferred": False, "heartbeat_measured": False,
                "medical_state_inferred": False, "emergency_condition_inferred": False,
                "grants_authority": False, "read_only": True,
            },
            "receipt_id": module_id + "-receipt", "source_clock": "runtime-receive",
            "stale_after_ms": 1000, "calibration_version": "test-v1",
            "degraded_reason": None, "raw_reference": "serial:test",
        },
    }

def _health_record(seat_id):
    module_id = "seat-presence-%s" % seat_id
    return {
        "event_id": module_id + "-health", "event_type": "HEALTH_FAILED",
        "family": "health",
        "payload": {
            "event_id": module_id + "-health", "event_type": "FAILED",
            "module_id": module_id, "node_id": "seat-node-%s" % seat_id,
            "owning_handmaiden": "Temperance", "timestamp": 100.0,
            "severity": "ERROR", "state_before": "DEGRADED", "state_after": "FAILED",
            "confidence": 1.0,
            "diagnostic_payload": {
                "detail": "Seat node missing", "reason_code": "SEAT_NODE_SOURCE_FAILURE",
                "seat_id": seat_id, "read_only": True,
                "seat_occupancy_inferred": False, "medical_state_inferred": False,
                "authority_granted": False,
            },
            "receipt_id": module_id + "-health",
            "recovery_action": "continue observation-only seat-node monitoring",
            "fallback_owner": "Velvet",
        },
    }

if __name__ == "__main__":
    unittest.main()
