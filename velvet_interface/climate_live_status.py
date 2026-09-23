# SPDX-License-Identifier: GPL-3.0-only
"""Read-only cabin climate projection from Runtime body-state evidence."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from velvet_interface.core.body_state import BodyStateStore


BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"
ENVIRONMENT_MODULE_ID = "environmental-sensors"
ENVIRONMENT_SENSOR_TYPE = "environmental_conditions"


@dataclass(frozen=True)
class ClimateLiveStatus:
    available: bool
    state: str
    freshness: str
    cabin_temperature_c: Optional[float] = None
    outside_temperature_c: Optional[float] = None
    relative_humidity_percent: Optional[float] = None
    ambient_light_lux: Optional[float] = None
    sample_count: Optional[int] = None
    owning_handmaiden: Optional[str] = None
    calibration_version: Optional[str] = None
    receipt_id: Optional[str] = None
    message: str = ""


def load_climate_live_status(
    body_path: Path,
    now_monotonic: Optional[float] = None,
) -> ClimateLiveStatus:
    """Project genuine environmental observations without requesting control."""

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
                if item.sensor_type == ENVIRONMENT_SENSOR_TYPE
                or item.module_id == ENVIRONMENT_MODULE_ID
            ),
            None,
        )
        health = next(
            (
                item
                for item in body.health_events
                if item.module_id == ENVIRONMENT_MODULE_ID
            ),
            None,
        )

        if sensor is None:
            if health is not None and health.state_after in {"FAILED", "DEGRADED"}:
                detail = str(
                    health.diagnostic_payload.get(
                        "detail", "Environmental sensing is not healthy"
                    )
                )
                return ClimateLiveStatus(
                    available=True,
                    state=health.state_after,
                    freshness="unknown",
                    owning_handmaiden=health.owning_handmaiden,
                    receipt_id=health.receipt_id,
                    message=detail,
                )
            return ClimateLiveStatus(
                available=False,
                state="UNAVAILABLE",
                freshness="unknown",
                message="Climate evidence awaiting Runtime environmental observations",
            )

        payload = sensor.payload
        _validate_environment_payload(payload)
        freshness = sensor.freshness(current)
        state = sensor.health_state
        if health is not None and health.state_after == "FAILED":
            state = "FAILED"
        elif health is not None and health.state_after == "DEGRADED":
            state = "DEGRADED"
        elif freshness == "stale":
            state = "STALE"

        return ClimateLiveStatus(
            available=True,
            state=state,
            freshness=freshness,
            cabin_temperature_c=_bounded_number(
                payload.get("cabin_temperature_c"),
                -80.0,
                120.0,
                "cabin_temperature_c",
            ),
            outside_temperature_c=_optional_bounded_number(
                payload.get("outside_temperature_c"),
                -100.0,
                100.0,
                "outside_temperature_c",
            ),
            relative_humidity_percent=_optional_bounded_number(
                payload.get("relative_humidity_percent"),
                0.0,
                100.0,
                "relative_humidity_percent",
            ),
            ambient_light_lux=_bounded_number(
                payload.get("ambient_light_lux"),
                0.0,
                500000.0,
                "ambient_light_lux",
            ),
            sample_count=_optional_non_negative_int(payload.get("sample_count")),
            owning_handmaiden=sensor.owning_handmaiden,
            calibration_version=sensor.calibration_version,
            receipt_id=sensor.receipt_id,
            message=_message(state, freshness),
        )
    except FileNotFoundError:
        message = "Climate evidence awaiting Runtime snapshot"
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        message = "Climate evidence unavailable: %s" % exc
    return ClimateLiveStatus(
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


def _validate_environment_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("read_only") is not True:
        raise ValueError("environmental evidence must be read-only")
    if payload.get("grants_authority") is not False:
        raise ValueError("environmental evidence cannot grant authority")
    if payload.get("control_requested") is not False:
        raise ValueError("environmental evidence cannot request control")


def _bounded_number(value: Any, minimum: float, maximum: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % label)
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError("%s is outside supported bounds" % label)
    return number


def _optional_bounded_number(
    value: Any,
    minimum: float,
    maximum: float,
    label: str,
) -> Optional[float]:
    if value is None:
        return None
    return _bounded_number(value, minimum, maximum, label)


def _optional_non_negative_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("sample_count must be a non-negative integer")
    return value


def _message(state: str, freshness: str) -> str:
    if state == "FAILED":
        return "Environmental sensing failed"
    if state == "DEGRADED":
        return "Environmental sensing is degraded"
    if freshness == "stale" or state == "STALE":
        return "Last genuine climate observation is stale"
    return "Live cabin environmental evidence; climate control remains separate"
