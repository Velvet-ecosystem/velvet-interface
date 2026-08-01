# SPDX-License-Identifier: GPL-3.0-only
"""Read-only microphone input-health projection from Runtime evidence."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from velvet_interface.core.body_state import BodyStateStore


BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"
_ALLOWED_CHANNEL_STATES = {"ACTIVE", "QUIET", "DIGITAL_SILENCE", "CLIPPING"}


@dataclass(frozen=True)
class MicrophoneChannelLiveStatus:
    label: str
    state: str
    peak_dbfs: float
    rms_dbfs: float


@dataclass(frozen=True)
class MicrophoneInputLiveStatus:
    available: bool
    state: str
    freshness: str
    source_id: str = "-"
    device_alias: str = "-"
    channel_count: int = 0
    sample_rate_hz: int = 0
    active_channels: int = 0
    quiet_channels: int = 0
    digital_silence_channels: int = 0
    clipping_channels: int = 0
    channels: Tuple[MicrophoneChannelLiveStatus, ...] = ()
    receipt_id: Optional[str] = None
    message: str = ""


def load_microphone_input_live_status(
    body_path: Path,
    now_monotonic: Optional[float] = None,
) -> MicrophoneInputLiveStatus:
    try:
        document = json.loads(Path(body_path).read_text(encoding="utf-8"))
        _validate_snapshot(document)
        store = BodyStateStore()
        store.apply_many(document["records"])
        current = time.monotonic() if now_monotonic is None else float(now_monotonic)
        if not math.isfinite(current) or current < 0:
            raise ValueError("current monotonic time must be finite and non-negative")
        body = store.snapshot(current)
        sensor = next(
            (
                item
                for item in body.sensors
                if item.sensor_type == "microphone_input_health"
                or item.module_id == "microphone-input-main"
            ),
            None,
        )
        health = next(
            (
                item
                for item in body.health_events
                if item.module_id == "microphone-input-main"
            ),
            None,
        )

        if sensor is None:
            if health is not None and health.state_after == "FAILED":
                detail = str(
                    health.diagnostic_payload.get(
                        "detail", "Microphone input-health probe failed"
                    )
                )
                return MicrophoneInputLiveStatus(
                    available=True,
                    state="FAILED",
                    freshness="unknown",
                    receipt_id=health.receipt_id,
                    message=detail,
                )
            return MicrophoneInputLiveStatus(
                available=False,
                state="UNAVAILABLE",
                freshness="unknown",
                message="Microphone input-health evidence awaiting Runtime",
            )

        payload = sensor.payload
        freshness = sensor.freshness(current)
        state = sensor.health_state.upper()
        if health is not None and health.state_after == "FAILED":
            state = "FAILED"
        elif freshness == "stale":
            state = "STALE"

        source_id = _required_text(payload, "source_id")
        device_alias = _required_text(payload, "device_alias")
        channel_count = _required_integer(payload, "channel_count", 1, 32)
        sample_rate_hz = _required_integer(payload, "sample_rate_hz", 8000, 384000)
        raw_channels = payload.get("channels")
        if not isinstance(raw_channels, list) or len(raw_channels) != channel_count:
            raise ValueError("microphone channels must match channel_count")
        channels = []
        for raw_channel in raw_channels:
            if not isinstance(raw_channel, Mapping):
                raise ValueError("microphone channel entry must be an object")
            channel_state = _required_text(raw_channel, "state").upper()
            if channel_state not in _ALLOWED_CHANNEL_STATES:
                raise ValueError("unsupported microphone channel state")
            channels.append(
                MicrophoneChannelLiveStatus(
                    label=_required_text(raw_channel, "label"),
                    state=channel_state,
                    peak_dbfs=_required_finite_number(raw_channel, "peak_dbfs"),
                    rms_dbfs=_required_finite_number(raw_channel, "rms_dbfs"),
                )
            )

        active = _required_integer(payload, "active_channels", 0, channel_count)
        quiet = _required_integer(payload, "quiet_channels", 0, channel_count)
        silence = _required_integer(
            payload, "digital_silence_channels", 0, channel_count
        )
        clipping = _required_integer(payload, "clipping_channels", 0, channel_count)
        if active + quiet + silence + clipping != channel_count:
            raise ValueError("microphone channel-state counts do not balance")
        for key in (
            "audio_retained",
            "audio_persisted",
            "speech_recognition_performed",
            "wake_word_detection_performed",
            "command_interpreted",
            "voice_command_authority",
        ):
            if payload.get(key) is not False:
                raise ValueError("microphone %s must remain false" % key)

        return MicrophoneInputLiveStatus(
            available=True,
            state=state,
            freshness=freshness,
            source_id=source_id,
            device_alias=device_alias,
            channel_count=channel_count,
            sample_rate_hz=sample_rate_hz,
            active_channels=active,
            quiet_channels=quiet,
            digital_silence_channels=silence,
            clipping_channels=clipping,
            channels=tuple(channels),
            receipt_id=sensor.receipt_id,
            message=_message(state, freshness, active, quiet, silence, clipping),
        )
    except FileNotFoundError:
        message = "Microphone input-health evidence awaiting Runtime snapshot"
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        message = "Microphone input unavailable: %s" % exc
    return MicrophoneInputLiveStatus(
        available=False,
        state="UNAVAILABLE",
        freshness="unknown",
        message=message,
    )


def _validate_snapshot(document: Any) -> None:
    if not isinstance(document, Mapping):
        raise ValueError("body snapshot root must be an object")
    if document.get("schema") != BODY_STATE_SNAPSHOT_SCHEMA:
        raise ValueError("unsupported body snapshot schema")
    if document.get("read_only") is not True:
        raise ValueError("body snapshot must be read-only")
    if document.get("authority", "none") != "none":
        raise ValueError("body snapshot cannot carry authority")
    if document.get("actuation_granted") is not False:
        raise ValueError("body snapshot cannot grant actuation")
    if document.get("actuation_performed") is not False:
        raise ValueError("body snapshot cannot claim actuation")
    if not isinstance(document.get("records"), list):
        raise ValueError("body snapshot records must be a list")


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("microphone %s must be non-empty text" % key)
    return value.strip()


def _required_integer(
    payload: Mapping[str, Any],
    key: str,
    minimum: int,
    maximum: int,
) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("microphone %s must be an integer" % key)
    if not minimum <= value <= maximum:
        raise ValueError("microphone %s is outside supported bounds" % key)
    return value


def _required_finite_number(payload: Mapping[str, Any], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("microphone %s must be numeric" % key)
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("microphone %s must be finite" % key)
    return number


def _message(
    state: str,
    freshness: str,
    active: int,
    quiet: int,
    silence: int,
    clipping: int,
) -> str:
    if state == "FAILED":
        return "Microphone capture path failed"
    if freshness == "stale":
        return "Last microphone health probe is stale"
    if clipping:
        return "%d channel%s clipping" % (clipping, " is" if clipping == 1 else "s are")
    if silence:
        return "%d channel%s at exact digital silence" % (
            silence,
            " is" if silence == 1 else "s are",
        )
    return "%d active, %d quiet; quiet is healthy" % (active, quiet)
