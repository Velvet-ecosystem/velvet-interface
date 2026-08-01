# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.microphone_input_live_status import (
    load_microphone_input_live_status,
)


class MicrophoneInputLiveStatusTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            status = load_microphone_input_live_status(
                Path(directory) / "missing.json"
            )
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")
        self.assertEqual(status.channel_count, 0)

    def test_live_five_channel_roof_array_is_projected(self) -> None:
        channels = [
            _channel("front-left", "ACTIVE", -3.0, -22.0),
            _channel("front-right", "ACTIVE", -4.0, -24.0),
            _channel("rear-left", "QUIET", -55.0, -70.0),
            _channel("rear-right", "QUIET", -56.0, -71.0),
            _channel("roof-center", "ACTIVE", -5.0, -25.0),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(channels, 10.0)])
            status = load_microphone_input_live_status(path, now_monotonic=10.5)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "ONLINE")
        self.assertEqual(status.channel_count, 5)
        self.assertEqual(status.active_channels, 3)
        self.assertEqual(status.quiet_channels, 2)
        self.assertEqual(status.channels[-1].label, "roof-center")
        self.assertIn("quiet is healthy", status.message.lower())

    def test_exact_digital_silence_is_visible_as_degraded(self) -> None:
        channels = [
            _channel("front-left", "ACTIVE", -3.0, -22.0),
            _channel("front-right", "DIGITAL_SILENCE", -120.0, -120.0),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(channels, 10.0)])
            status = load_microphone_input_live_status(path, now_monotonic=10.5)
        self.assertEqual(status.state, "DEGRADED")
        self.assertEqual(status.digital_silence_channels, 1)
        self.assertIn("digital silence", status.message.lower())

    def test_clipping_is_visible(self) -> None:
        channels = [_channel("roof-center", "CLIPPING", 0.0, -1.0)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(channels, 10.0)])
            status = load_microphone_input_live_status(path, now_monotonic=10.5)
        self.assertEqual(status.clipping_channels, 1)
        self.assertIn("clipping", status.message.lower())

    def test_last_probe_is_labeled_stale(self) -> None:
        channels = [_channel("roof-center", "QUIET", -60.0, -70.0)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_sensor_record(channels, 10.0)])
            status = load_microphone_input_live_status(path, now_monotonic=30.0)
        self.assertEqual(status.state, "STALE")
        self.assertEqual(status.freshness, "stale")
        self.assertIn("stale", status.message.lower())

    def test_failed_source_fabricates_no_channels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            _write_snapshot(path, [_health_record()])
            status = load_microphone_input_live_status(path, now_monotonic=10.0)
        self.assertTrue(status.available)
        self.assertEqual(status.state, "FAILED")
        self.assertEqual(status.channel_count, 0)
        self.assertEqual(status.channels, ())
        self.assertIn("missing", status.message.lower())

    def test_privacy_claim_must_remain_false(self) -> None:
        channels = [_channel("roof-center", "ACTIVE", -4.0, -24.0)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record(channels, 10.0)
            record["payload"]["payload"]["audio_retained"] = True
            _write_snapshot(path, [record])
            status = load_microphone_input_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)
        self.assertEqual(status.state, "UNAVAILABLE")

    def test_unbalanced_counts_fail_closed(self) -> None:
        channels = [_channel("roof-center", "ACTIVE", -4.0, -24.0)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.json"
            record = _sensor_record(channels, 10.0)
            record["payload"]["payload"]["quiet_channels"] = 1
            _write_snapshot(path, [record])
            status = load_microphone_input_live_status(path, now_monotonic=10.5)
        self.assertFalse(status.available)


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


def _channel(label, state, peak, rms):
    return {
        "index": 0,
        "label": label,
        "state": state,
        "peak_dbfs": peak,
        "rms_dbfs": rms,
        "clipping_ratio": 0.01 if state == "CLIPPING" else 0.0,
        "nonzero_ratio": 0.0 if state == "DIGITAL_SILENCE" else 1.0,
    }


def _sensor_record(channels, monotonic_time):
    counts = {
        "ACTIVE": 0,
        "QUIET": 0,
        "DIGITAL_SILENCE": 0,
        "CLIPPING": 0,
    }
    for channel in channels:
        counts[channel["state"]] += 1
    degraded = counts["DIGITAL_SILENCE"] or counts["CLIPPING"]
    return {
        "event_id": "microphone-sensor-receipt",
        "event_type": "SENSOR_PACKET_OBSERVED",
        "family": "sensor",
        "payload": {
            "module_id": "microphone-input-main",
            "node_id": "founder-up2",
            "owning_handmaiden": "Velvet",
            "timestamp": 100.0,
            "monotonic_time": monotonic_time,
            "sensor_type": "microphone_input_health",
            "interface_type": "alsa-arecord-health-probe",
            "health_state": "DEGRADED" if degraded else "ONLINE",
            "confidence": 1.0,
            "payload": {
                "source_id": "microphone.array.roof",
                "device_alias": "hw:2,0",
                "channel_count": len(channels),
                "sample_rate_hz": 16000,
                "sample_format": "S16_LE",
                "probe_seconds": 1,
                "frames_per_channel": 16000,
                "captured_byte_count": len(channels) * 32000,
                "channels": channels,
                "active_channels": counts["ACTIVE"],
                "quiet_channels": counts["QUIET"],
                "digital_silence_channels": counts["DIGITAL_SILENCE"],
                "clipping_channels": counts["CLIPPING"],
                "audio_retained": False,
                "audio_persisted": False,
                "speech_recognition_performed": False,
                "wake_word_detection_performed": False,
                "command_interpreted": False,
                "voice_command_authority": False,
                "read_only": True,
            },
            "receipt_id": "microphone-sensor-receipt",
            "source_clock": "device",
            "stale_after_ms": 15000,
            "calibration_version": "microphone-input-health-v1",
            "degraded_reason": "INPUT_DEGRADED" if degraded else None,
            "raw_reference": "hw:2,0",
        },
    }


def _health_record():
    return {
        "event_id": "microphone-health-receipt",
        "event_type": "HEALTH_FAILED",
        "family": "health",
        "payload": {
            "event_id": "microphone-health-receipt",
            "event_type": "FAILED",
            "module_id": "microphone-input-main",
            "node_id": "founder-up2",
            "owning_handmaiden": "Velvet",
            "timestamp": 100.0,
            "severity": "ERROR",
            "state_before": "DEGRADED",
            "state_after": "FAILED",
            "confidence": 1.0,
            "diagnostic_payload": {
                "detail": "ALSA microphone device missing",
                "reason_code": "CAPTURE_FAILURE",
                "audio_retained": False,
                "read_only": True,
            },
            "receipt_id": "microphone-health-receipt",
            "recovery_action": "continue bounded microphone input-health probing",
            "fallback_owner": "Velvet",
        },
    }


if __name__ == "__main__":
    unittest.main()
