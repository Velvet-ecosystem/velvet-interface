# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.seat_person_sense_live_status import (
    load_seat_person_sense_live_status,
)


class SeatPersonSensePartialTopologyTests(unittest.TestCase):
    def test_main_pad_only_with_heartbeat_remains_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "velvet.runtime.body_state_snapshot.v1",
                        "read_only": True,
                        "authority": "none",
                        "actuation_granted": False,
                        "actuation_performed": False,
                        "records": [_partial_body_map(), _heartbeat()],
                    }
                ),
                encoding="utf-8",
            )
            status = load_seat_person_sense_live_status(
                path, now_monotonic=10.5
            )
        self.assertTrue(status.available)
        self.assertEqual(status.state, "PARTIAL")
        self.assertEqual(status.seats[0].state, "PARTIAL")
        self.assertEqual(status.seats[0].body_map_state, "PARTIAL")
        self.assertEqual(status.seats[0].heartbeat_state, "ONLINE")
        self.assertFalse(status.seats[0].movement_topology_complete)
        self.assertEqual(status.seats[0].main_total, 1)
        self.assertEqual(status.seats[0].bolster_total, 0)
        self.assertEqual(status.seats[0].edge_total, 0)

    def test_completeness_claim_must_match_actual_roles(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            body_map = _partial_body_map()
            body_map["payload"]["payload"][
                "movement_topology_complete"
            ] = True
            path.write_text(
                json.dumps(
                    {
                        "schema": "velvet.runtime.body_state_snapshot.v1",
                        "read_only": True,
                        "authority": "none",
                        "actuation_granted": False,
                        "actuation_performed": False,
                        "records": [body_map],
                    }
                ),
                encoding="utf-8",
            )
            status = load_seat_person_sense_live_status(
                path, now_monotonic=10.5
            )
        self.assertFalse(status.available)


def _partial_body_map():
    module_id = "seat-person-body-map-driver"
    return {
        "event_id": module_id + "-receipt",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": module_id,
            "node_id": "seat-node-driver",
            "owning_handmaiden": "Temperance",
            "timestamp": 100.0,
            "monotonic_time": 10.0,
            "sensor_type": "seat_person_sense_body_map",
            "interface_type": "derived-from-seat-pressure",
            "health_state": "ONLINE",
            "confidence": 0.65,
            "payload": {
                "seat_id": "driver",
                "source_id": "seat.person_sense.body_map.driver",
                "person_sense_family": "seat_person_sense",
                "fusion_role": "body_contact_and_movement_map",
                "topology_id": "legacy-driver-main-only-v1",
                "vehicle_profile": "legacy-driver-seat",
                "topology_calibration_version": "bench-v1",
                "pressure_calibration_version": "pressure-v1",
                "movement_topology_complete": False,
                "mapped_pads": [
                    {
                        "pad_id": "main-pad",
                        "role": "MAIN_LOAD",
                        "surface": "seat-base-main",
                        "side": "CENTER",
                        "movement_weight": 1.0,
                        "active": True,
                        "raw_value": 1,
                        "normalized_load": None,
                    }
                ],
                "pad_count": 1,
                "role_counts": {
                    "MAIN_LOAD": 1,
                    "SIDE_BOLSTER": 0,
                    "EDGE_MOTION": 0,
                },
                "active_role_counts": {"MAIN_LOAD": 1},
                "side_counts": {"CENTER": 1},
                "active_side_counts": {"CENTER": 1},
                "main_load_contact_detected": True,
                "side_bolster_contact_detected": False,
                "edge_motion_contact_detected": False,
                "baseline_established": True,
                "movement_detected": False,
                "movement_intensity": 0.0,
                "changed_pad_ids": [],
                "changed_roles": [],
                "changed_surfaces": [],
                "pressure_lateral_state": "CENTER",
                "pressure_lateral_shift_detected": False,
                "pressure_lateral_shift_direction": "NONE",
                "companion_evidence_expected": [
                    "seat_presence_radar",
                    "seat_heartbeat_signal",
                    "camera_posture_evidence",
                ],
                "heartbeat_observed_by_this_adapter": False,
                "missing_heartbeat_means_absent": False,
                "person_presence_inferred": False,
                "seat_occupancy_inferred": False,
                "occupant_posture_inferred": False,
                "occupant_identity_inferred": False,
                "heartbeat_measured_by_pressure": False,
                "medical_state_inferred": False,
                "emergency_condition_inferred": False,
                "grants_authority": False,
                "read_only": True,
            },
            "receipt_id": module_id + "-receipt",
            "source_clock": "runtime-derived",
            "stale_after_ms": 3500,
            "calibration_version": "bench-v1",
            "degraded_reason": "PARTIAL_PERSON_SENSE_TOPOLOGY",
            "raw_reference": "serial:test#pressure-body-map",
        },
    }


def _heartbeat():
    module_id = "seat-heartbeat-driver"
    return {
        "event_id": module_id + "-receipt",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": module_id,
            "node_id": "seat-node-driver",
            "owning_handmaiden": "Temperance",
            "timestamp": 100.0,
            "monotonic_time": 10.0,
            "sensor_type": "seat_heartbeat_signal",
            "interface_type": "read-only-serial-json",
            "health_state": "ONLINE",
            "confidence": 0.8,
            "payload": {
                "seat_id": "driver",
                "source_id": "seat.heartbeat.driver",
                "person_sense_family": "seat_person_sense",
                "fusion_role": "heartbeat_signal",
                "sensor_model": "seat-heartbeat-sensor",
                "firmware_version": "seat-node-0.3.0",
                "node_boot_id": "boot-a",
                "sequence": 1,
                "node_uptime_ms": 1000,
                "signal_detected": True,
                "heartbeat_bpm": 72.0,
                "heartbeat_confidence": 0.8,
                "signal_quality": 0.75,
                "measurement_window_ms": 3000,
                "missing_heartbeat_means_absent": False,
                "heartbeat_signal_is_medical_diagnosis": False,
                "person_presence_inferred": False,
                "seat_occupancy_inferred": False,
                "occupant_identity_inferred": False,
                "medical_state_inferred": False,
                "emergency_condition_inferred": False,
                "grants_authority": False,
                "read_only": True,
            },
            "receipt_id": module_id + "-receipt",
            "source_clock": "runtime-receive",
            "stale_after_ms": 5000,
            "calibration_version": "heartbeat-v1",
            "degraded_reason": None,
            "raw_reference": "serial:test",
        },
    }


if __name__ == "__main__":
    unittest.main()
