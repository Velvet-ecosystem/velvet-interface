# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.seat_pressure_live_status import (
    load_seat_pressure_live_status,
    seat_evidence_relationship,
)


class SeatPressureLiveStatusTests(unittest.TestCase):
    def test_binary_pressure_contact_and_lateral_state_are_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_pressure_record()])
            status = load_seat_pressure_live_status(
                path, now_monotonic=10.5
            )
        self.assertTrue(status.available)
        self.assertEqual(status.state, "ONLINE")
        seat = status.seats[0]
        self.assertEqual(seat.state, "CONTACT_CONFIRMED")
        self.assertEqual(seat.active_pad_count, 2)
        self.assertEqual(seat.lateral_state, "BALANCED")
        self.assertIsNone(seat.total_load_kg_equivalent)
        self.assertIn("not inferred", seat.message.lower())

    def test_release_transition_and_two_second_confirmation_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            transition = _pressure_record(
                contact=False, stable_ms=1999
            )
            _write_snapshot(path, [transition])
            status = load_seat_pressure_live_status(
                path, now_monotonic=10.5
            )
            self.assertEqual(status.seats[0].state, "TRANSITION")

            confirmed = _pressure_record(
                contact=False, stable_ms=2000
            )
            _write_snapshot(path, [confirmed])
            status = load_seat_pressure_live_status(
                path, now_monotonic=10.5
            )
        self.assertEqual(
            status.seats[0].state, "NO_CONTACT_CONFIRMED"
        )
        self.assertIn("not inferred", status.seats[0].message.lower())

    def test_stale_and_failed_pressure_do_not_disappear(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_pressure_record(monotonic_time=10.0)])
            stale = load_seat_pressure_live_status(
                path, now_monotonic=15.0
            )
            self.assertEqual(stale.state, "DEGRADED")
            self.assertEqual(stale.seats[0].state, "STALE")

            _write_snapshot(path, [_pressure_health_record()])
            failed = load_seat_pressure_live_status(
                path, now_monotonic=10.0
            )
        self.assertEqual(failed.state, "FAILED")
        self.assertEqual(failed.seats[0].state, "FAILED")

    def test_binary_load_claim_and_occupancy_claim_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _pressure_record()
            record["payload"]["payload"][
                "total_load_kg_equivalent"
            ] = 70.0
            record["payload"]["payload"][
                "load_estimate_available"
            ] = True
            record["payload"]["payload"]["load_is_estimate"] = True
            _write_snapshot(path, [record])
            self.assertFalse(
                load_seat_pressure_live_status(
                    path, now_monotonic=10.5
                ).available
            )

            record = _pressure_record()
            record["payload"]["payload"][
                "pressure_contact_means_occupied"
            ] = True
            _write_snapshot(path, [record])
            status = load_seat_pressure_live_status(
                path, now_monotonic=10.5
            )
        self.assertFalse(status.available)

    def test_relationship_names_disagreement_without_occupancy(self):
        self.assertEqual(
            seat_evidence_relationship(
                "RADAR_PRESENT", "CONTACT_CONFIRMED"
            ),
            "AGREEMENT_PRESENT",
        )
        self.assertEqual(
            seat_evidence_relationship(
                "NO_RADAR_PRESENCE", "NO_CONTACT_CONFIRMED"
            ),
            "AGREEMENT_QUIET",
        )
        self.assertEqual(
            seat_evidence_relationship(
                "NO_RADAR_PRESENCE", "CONTACT_CONFIRMED"
            ),
            "PRESSURE_ONLY",
        )
        self.assertEqual(
            seat_evidence_relationship(
                "RADAR_PRESENT", "NO_CONTACT_CONFIRMED"
            ),
            "RADAR_ONLY",
        )


def _write_snapshot(path, records):
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


def _pressure_record(
    contact=True, stable_ms=200, monotonic_time=10.0
):
    state = (
        "CONTACT_CONFIRMED"
        if contact and stable_ms >= 150
        else "NO_CONTACT_CONFIRMED"
        if not contact and stable_ms >= 2000
        else "TRANSITION"
    )
    module_id = "seat-pressure-driver"
    pads = [
        {
            "pad_id": "left-pad",
            "zone": "left",
            "active": contact,
            "raw_value": 1 if contact else 0,
            "normalized_load": None,
        },
        {
            "pad_id": "right-pad",
            "zone": "right",
            "active": contact,
            "raw_value": 1 if contact else 0,
            "normalized_load": None,
        },
    ]
    return {
        "event_id": module_id + "-receipt",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": module_id,
            "node_id": "seat-node-driver",
            "owning_handmaiden": "Temperance",
            "timestamp": 100.0,
            "monotonic_time": monotonic_time,
            "sensor_type": "seat_pressure_array",
            "interface_type": "read-only-serial-json",
            "health_state": "ONLINE",
            "confidence": 0.88 if contact else 0.60,
            "payload": {
                "seat_id": "driver",
                "source_id": "seat.pressure.driver",
                "sensor_model": "seat-pressure-pad-array",
                "firmware_version": "seat-node-0.2.0",
                "node_boot_id": "boot-a",
                "sequence": 4,
                "node_uptime_ms": 1000,
                "pressure_mode": "BINARY_CONTACT",
                "pads": pads,
                "pad_count": 2,
                "active_pad_count": 2 if contact else 0,
                "pressure_contact_detected_raw": contact,
                "pressure_contact_stable_ms": stable_ms,
                "pressure_contact_state": state,
                "pressure_contact_confirmed": (
                    state == "CONTACT_CONFIRMED"
                ),
                "pressure_release_confirmed": (
                    state == "NO_CONTACT_CONFIRMED"
                ),
                "contact_assert_ms": 150,
                "release_assert_ms": 2000,
                "lateral_state": (
                    "BALANCED" if contact else "NO_CONTACT"
                ),
                "lateral_shift_detected": False,
                "lateral_shift_direction": "NONE",
                "total_load_kg_equivalent": None,
                "load_estimate_available": False,
                "load_is_estimate": False,
                "binary_contact_converted_to_load": False,
                "pressure_contact_means_occupied": False,
                "no_pressure_contact_means_empty": False,
                "seat_occupancy_inferred": False,
                "occupant_identity_inferred": False,
                "heartbeat_measured": False,
                "medical_state_inferred": False,
                "emergency_condition_inferred": False,
                "grants_authority": False,
                "read_only": True,
            },
            "receipt_id": module_id + "-receipt",
            "source_clock": "runtime-receive",
            "stale_after_ms": 1000,
            "calibration_version": "test-pressure-v1",
            "degraded_reason": None,
            "raw_reference": "serial:test",
        },
    }


def _pressure_health_record():
    module_id = "seat-pressure-driver"
    return {
        "event_id": module_id + "-health",
        "event_type": "HEALTH_FAILED",
        "family": "health",
        "payload": {
            "event_id": module_id + "-health",
            "event_type": "FAILED",
            "module_id": module_id,
            "node_id": "seat-node-driver",
            "owning_handmaiden": "Temperance",
            "timestamp": 100.0,
            "severity": "ERROR",
            "state_before": "DEGRADED",
            "state_after": "FAILED",
            "confidence": 1.0,
            "diagnostic_payload": {
                "detail": "Seat pressure source missing",
                "reason_code": "SEAT_PRESSURE_SOURCE_FAILURE",
                "seat_id": "driver",
                "sensor_kind": "seat_pressure_array",
                "read_only": True,
                "seat_occupancy_inferred": False,
                "medical_state_inferred": False,
                "authority_granted": False,
            },
            "receipt_id": module_id + "-health",
            "recovery_action": (
                "continue observation-only seat pressure monitoring"
            ),
            "fallback_owner": "Velvet",
        },
    }


if __name__ == "__main__":
    unittest.main()
