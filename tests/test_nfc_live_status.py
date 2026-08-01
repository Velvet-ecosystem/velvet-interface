# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.nfc_live_status import load_nfc_live_status


TOKEN_REF = "hmac-sha256:" + ("a" * 64)


class NfcLiveStatusTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            status = load_nfc_live_status(Path(directory) / "missing.json")
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")
        self.assertEqual(status.match_state, "NO DATA")

    def test_ready_reader_without_presentation_is_idle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_health_record("READY", "ONLINE")])
            status = load_nfc_live_status(path, now_monotonic=10.0)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "IDLE")
        self.assertEqual(status.reader_state, "ONLINE")
        self.assertEqual(status.match_state, "NO PRESENTATION")

    def test_matched_factor_is_not_completed_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record("MATCHED", 10.0)])
            status = load_nfc_live_status(path, now_monotonic=10.5)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "MATCHED")
        self.assertEqual(status.label, "Mister")
        self.assertEqual(status.role_hint, "owner")
        self.assertEqual(status.factor_confidence, 0.55)
        self.assertIn("further verification", status.message.lower())

    def test_last_factor_expires_without_becoming_presence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record("MATCHED", 10.0)])
            status = load_nfc_live_status(path, now_monotonic=16.0)
        self.assertEqual(status.state, "EXPIRED")
        self.assertEqual(status.freshness, "stale")
        self.assertIn("expired", status.message.lower())

    def test_unknown_factor_cannot_claim_principal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record("UNKNOWN", 10.0)
            record["payload"]["payload"]["principal_ref"] = "principal:owner"
            _write_snapshot(path, [record])
            status = load_nfc_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")

    def test_raw_identifier_field_rejects_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record("MATCHED", 10.0)
            record["payload"]["payload"]["tag_hex"] = "000734E0"
            _write_snapshot(path, [record])
            status = load_nfc_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")

    def test_failed_reader_overrides_old_factor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(
                path,
                [
                    _sensor_record("MATCHED", 10.0),
                    _health_record("FAILED", "FAILED"),
                ],
            )
            status = load_nfc_live_status(path, now_monotonic=10.5)
        self.assertEqual(status.state, "FAILED")
        self.assertEqual(status.reader_state, "FAILED")


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


def _sensor_record(match_state: str, monotonic_time: float):
    matched = match_state == "MATCHED"
    factor = {
        "factor_type": "contactless_static_identifier",
        "presentation_id": "presentation-id",
        "match_state": match_state,
        "token_ref": TOKEN_REF,
        "reader_id": "rdm6300-main",
        "factor_confidence": 0.55 if matched else 0.0,
        "static_identifier": True,
        "cryptographic_challenge": False,
        "verification_only": True,
        "presence_claimed": False,
        "grants_authority": False,
        "read_only": True,
    }
    if matched:
        factor.update(
            {
                "principal_ref": "principal:owner",
                "label": "Mister",
                "role_hint": "owner",
                "registry_enabled": True,
            }
        )
    return {
        "event_id": "nfc-sensor-receipt",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": "contactless-token-main",
            "node_id": "founder-up2",
            "owning_handmaiden": "Velvet",
            "timestamp": 100.0,
            "monotonic_time": monotonic_time,
            "sensor_type": "contactless_token_presentation",
            "interface_type": "uart-rdm6300-read-only",
            "health_state": "ONLINE",
            "confidence": 1.0,
            "payload": factor,
            "receipt_id": "nfc-sensor-receipt",
            "source_clock": "device",
            "stale_after_ms": 5000,
            "calibration_version": "rdm6300-em4100-v1",
            "raw_reference": "reader:rdm6300-main",
        },
    }


def _health_record(event_type: str, state_after: str):
    return {
        "event_id": "nfc-health-receipt-%s" % event_type,
        "event_type": "HEALTH_%s" % event_type,
        "family": "health",
        "payload": {
            "event_id": "nfc-health-receipt-%s" % event_type,
            "event_type": event_type,
            "module_id": "contactless-token-main",
            "node_id": "founder-up2",
            "owning_handmaiden": "Velvet",
            "timestamp": 100.0,
            "severity": "ERROR" if state_after == "FAILED" else "INFO",
            "state_before": "UNKNOWN",
            "state_after": state_after,
            "confidence": 1.0,
            "diagnostic_payload": {
                "detail": "Contactless reader state",
                "reason_code": "READER_STATE",
                "read_only": True,
            },
            "receipt_id": "nfc-health-receipt-%s" % event_type,
            "recovery_action": "continue read-only contactless observation",
            "fallback_owner": "Velvet",
        },
    }


if __name__ == "__main__":
    unittest.main()
