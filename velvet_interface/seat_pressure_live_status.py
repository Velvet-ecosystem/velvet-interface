# SPDX-License-Identifier: GPL-3.0-only
"""Read-only pressure-pad projection from Runtime body evidence."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from velvet_interface.core.body_state import BodyStateStore

BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"
_ALLOWED_CONTACT_STATES = {
    "CONTACT_CONFIRMED",
    "NO_CONTACT_CONFIRMED",
    "TRANSITION",
}
_ALLOWED_MODES = {"BINARY_CONTACT", "CALIBRATED_LOAD"}
_ALLOWED_LATERAL_STATES = {
    "LEFT",
    "CENTER",
    "RIGHT",
    "BALANCED",
    "MIXED",
    "NO_CONTACT",
    "UNKNOWN",
}
_ALLOWED_DIRECTIONS = {"LEFT", "RIGHT", "NONE", "UNKNOWN"}
_SEAT_ORDER = {
    "driver": 0,
    "front-passenger": 1,
    "rear-left": 2,
    "rear-right": 3,
}


@dataclass(frozen=True)
class SeatPressureLiveSeat:
    seat_id: str
    state: str
    freshness: str
    pressure_mode: str = "UNKNOWN"
    pad_count: int = 0
    active_pad_count: int = 0
    lateral_state: str = "UNKNOWN"
    lateral_shift_direction: str = "NONE"
    total_load_kg_equivalent: Optional[float] = None
    node_id: str = "-"
    sensor_model: str = "-"
    confidence: float = 0.0
    receipt_id: Optional[str] = None
    message: str = ""


@dataclass(frozen=True)
class SeatPressureLiveStatus:
    available: bool
    state: str
    seats: Tuple[SeatPressureLiveSeat, ...] = ()
    message: str = ""


def load_seat_pressure_live_status(
    body_path: Path, now_monotonic: Optional[float] = None
) -> SeatPressureLiveStatus:
    try:
        document = json.loads(Path(body_path).read_text(encoding="utf-8"))
        _validate_snapshot(document)
        store = BodyStateStore()
        store.apply_many(document["records"])
        current = (
            time.monotonic()
            if now_monotonic is None
            else float(now_monotonic)
        )
        if not math.isfinite(current) or current < 0:
            raise ValueError(
                "current monotonic time must be finite and non-negative"
            )
        body = store.snapshot(current)
        health_by_module = {
            item.module_id: item for item in body.health_events
        }
        sensor_modules = {
            item.module_id
            for item in body.sensors
            if item.sensor_type == "seat_pressure_array"
        }
        seats = []
        seen = set()
        for sensor in body.sensors:
            if sensor.sensor_type != "seat_pressure_array":
                continue
            payload = sensor.payload
            seat_id = _required_text(payload, "seat_id")
            if seat_id in seen:
                raise ValueError(
                    "duplicate seat pressure evidence for %s" % seat_id
                )
            seen.add(seat_id)
            projection = _validate_pressure_payload(payload)

            freshness = sensor.freshness(current)
            state = sensor.health_state.upper()
            health = health_by_module.get(sensor.module_id)
            if health is not None and health.state_after == "FAILED":
                state = "FAILED"
            elif freshness == "stale":
                state = "STALE"
            elif state == "ONLINE":
                state = projection["contact_state"]
            elif state != "DEGRADED":
                raise ValueError("unsupported pressure health state")

            seats.append(
                SeatPressureLiveSeat(
                    seat_id=seat_id,
                    state=state,
                    freshness=freshness,
                    pressure_mode=projection["pressure_mode"],
                    pad_count=projection["pad_count"],
                    active_pad_count=projection["active_pad_count"],
                    lateral_state=projection["lateral_state"],
                    lateral_shift_direction=projection[
                        "lateral_shift_direction"
                    ],
                    total_load_kg_equivalent=projection[
                        "total_load_kg_equivalent"
                    ],
                    node_id=sensor.node_id,
                    sensor_model=_required_text(
                        payload, "sensor_model"
                    ),
                    confidence=_finite_probability(
                        sensor.confidence
                    ),
                    receipt_id=sensor.receipt_id,
                    message=_seat_message(
                        state,
                        projection["pad_count"],
                        projection["active_pad_count"],
                        projection["lateral_state"],
                    ),
                )
            )

        for health in body.health_events:
            if health.module_id in sensor_modules:
                continue
            diagnostic = health.diagnostic_payload
            if diagnostic.get("sensor_kind") != "seat_pressure_array":
                continue
            seat_id = diagnostic.get("seat_id")
            if (
                health.state_after != "FAILED"
                or not isinstance(seat_id, str)
                or not seat_id.strip()
            ):
                continue
            if seat_id in seen:
                continue
            seen.add(seat_id)
            seats.append(
                SeatPressureLiveSeat(
                    seat_id=seat_id.strip(),
                    state="FAILED",
                    freshness="unknown",
                    node_id=health.node_id,
                    receipt_id=health.receipt_id,
                    message=str(
                        diagnostic.get(
                            "detail", "Seat pressure node failed"
                        )
                    ),
                )
            )

        seats.sort(
            key=lambda item: (
                _SEAT_ORDER.get(item.seat_id, 99),
                item.seat_id,
            )
        )
        if not seats:
            return SeatPressureLiveStatus(
                available=False,
                state="UNAVAILABLE",
                message="Seat pressure evidence awaiting Runtime",
            )
        aggregate = "ONLINE"
        if any(item.state == "FAILED" for item in seats):
            aggregate = (
                "DEGRADED"
                if any(item.state != "FAILED" for item in seats)
                else "FAILED"
            )
        elif any(
            item.state in {"DEGRADED", "STALE"}
            for item in seats
        ):
            aggregate = "DEGRADED"
        return SeatPressureLiveStatus(
            available=True,
            state=aggregate,
            seats=tuple(seats),
            message=(
                "%d seat pressure node%s observed; occupancy is not inferred"
                % (len(seats), "" if len(seats) == 1 else "s")
            ),
        )
    except FileNotFoundError:
        message = "Seat pressure evidence awaiting Runtime snapshot"
    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        message = "Seat pressure unavailable: %s" % exc
    return SeatPressureLiveStatus(
        available=False, state="UNAVAILABLE", message=message
    )


def seat_evidence_relationship(
    radar_state: str, pressure_state: str
) -> str:
    """Describe agreement without converting evidence into occupancy."""

    radar = str(radar_state).upper()
    pressure = str(pressure_state).upper()
    if radar == "RADAR_PRESENT" and pressure == "CONTACT_CONFIRMED":
        return "AGREEMENT_PRESENT"
    if (
        radar == "NO_RADAR_PRESENCE"
        and pressure == "NO_CONTACT_CONFIRMED"
    ):
        return "AGREEMENT_QUIET"
    if radar == "RADAR_PRESENT" and pressure == "NO_CONTACT_CONFIRMED":
        return "RADAR_ONLY"
    if (
        radar == "NO_RADAR_PRESENCE"
        and pressure == "CONTACT_CONFIRMED"
    ):
        return "PRESSURE_ONLY"
    if pressure == "TRANSITION":
        return "TRANSITION"
    if radar == "UNAVAILABLE" or pressure == "UNAVAILABLE":
        return "INCOMPLETE"
    if radar in {"FAILED", "STALE", "DEGRADED"} or pressure in {
        "FAILED",
        "STALE",
        "DEGRADED",
    }:
        return "DEGRADED"
    return "MIXED"


def _validate_pressure_payload(
    payload: Mapping[str, Any]
) -> Mapping[str, Any]:
    _validate_observation_only_claims(payload)
    mode = _required_text(payload, "pressure_mode").upper()
    if mode not in _ALLOWED_MODES:
        raise ValueError("unsupported pressure mode")

    pads = payload.get("pads")
    if not isinstance(pads, list) or not 1 <= len(pads) <= 8:
        raise ValueError(
            "seat pressure pads must contain between one and eight entries"
        )
    pad_count = _required_integer(payload, "pad_count", 1, 8)
    if pad_count != len(pads):
        raise ValueError("seat pressure pad_count contradicts pads")

    active_count = 0
    seen = set()
    for index, pad in enumerate(pads):
        if not isinstance(pad, Mapping):
            raise ValueError(
                "seat pressure pad %d must be an object" % index
            )
        pad_id = _required_text(pad, "pad_id")
        if pad_id in seen:
            raise ValueError("duplicate seat pressure pad_id")
        seen.add(pad_id)
        _required_text(pad, "zone")
        active = _required_bool(pad, "active")
        if active:
            active_count += 1
        raw_value = pad.get("raw_value")
        if (
            raw_value is not None
            and (
                isinstance(raw_value, bool)
                or not isinstance(raw_value, int)
                or raw_value < 0
            )
        ):
            raise ValueError("seat pressure raw_value is invalid")
        normalized = pad.get("normalized_load")
        if mode == "BINARY_CONTACT" and normalized is not None:
            raise ValueError(
                "binary pressure evidence cannot carry normalized load"
            )
        if mode == "CALIBRATED_LOAD":
            _finite_bounded_number(
                normalized, "normalized_load", 0.0, 1.0
            )

    declared_active = _required_integer(
        payload, "active_pad_count", 0, pad_count
    )
    if declared_active != active_count:
        raise ValueError(
            "seat pressure active_pad_count contradicts pads"
        )

    raw_contact = _required_bool(
        payload, "pressure_contact_detected_raw"
    )
    if raw_contact != (active_count > 0):
        raise ValueError(
            "seat pressure raw contact contradicts active pads"
        )
    stable_ms = _required_integer(
        payload, "pressure_contact_stable_ms", 0, 2_147_483_647
    )
    contact_assert_ms = _required_integer(
        payload, "contact_assert_ms", 0, 60000
    )
    release_assert_ms = _required_integer(
        payload, "release_assert_ms", 0, 600000
    )
    if release_assert_ms < contact_assert_ms:
        raise ValueError(
            "seat pressure release threshold is shorter than contact"
        )
    expected_state = (
        "CONTACT_CONFIRMED"
        if raw_contact and stable_ms >= contact_assert_ms
        else "NO_CONTACT_CONFIRMED"
        if not raw_contact and stable_ms >= release_assert_ms
        else "TRANSITION"
    )
    contact_state = _required_text(
        payload, "pressure_contact_state"
    ).upper()
    if (
        contact_state not in _ALLOWED_CONTACT_STATES
        or contact_state != expected_state
    ):
        raise ValueError(
            "seat pressure contact state contradicts stable-time evidence"
        )
    if _required_bool(
        payload, "pressure_contact_confirmed"
    ) != (contact_state == "CONTACT_CONFIRMED"):
        raise ValueError("pressure contact confirmation contradicts state")
    if _required_bool(
        payload, "pressure_release_confirmed"
    ) != (contact_state == "NO_CONTACT_CONFIRMED"):
        raise ValueError("pressure release confirmation contradicts state")

    lateral_state = _required_text(
        payload, "lateral_state"
    ).upper()
    if lateral_state not in _ALLOWED_LATERAL_STATES:
        raise ValueError("unsupported pressure lateral state")
    shift_detected = _required_bool(
        payload, "lateral_shift_detected"
    )
    direction = _required_text(
        payload, "lateral_shift_direction"
    ).upper()
    if direction not in _ALLOWED_DIRECTIONS:
        raise ValueError("unsupported pressure shift direction")
    if shift_detected and direction not in {"LEFT", "RIGHT"}:
        raise ValueError(
            "pressure shift requires a left or right direction"
        )
    if not shift_detected and direction not in {"NONE", "UNKNOWN"}:
        raise ValueError(
            "no pressure shift must use NONE or UNKNOWN direction"
        )

    total_load = payload.get("total_load_kg_equivalent")
    load_available = _required_bool(
        payload, "load_estimate_available"
    )
    load_is_estimate = _required_bool(
        payload, "load_is_estimate"
    )
    if mode == "BINARY_CONTACT":
        if total_load is not None or load_available or load_is_estimate:
            raise ValueError(
                "binary pressure evidence cannot claim a load estimate"
            )
    else:
        total_load = _finite_bounded_number(
            total_load,
            "total_load_kg_equivalent",
            0.0,
            300.0,
        )
        if not load_available or not load_is_estimate:
            raise ValueError(
                "calibrated pressure load must remain marked as estimate"
            )

    return {
        "pressure_mode": mode,
        "pad_count": pad_count,
        "active_pad_count": active_count,
        "contact_state": contact_state,
        "lateral_state": lateral_state,
        "lateral_shift_direction": direction,
        "total_load_kg_equivalent": total_load,
    }


def _validate_observation_only_claims(
    payload: Mapping[str, Any]
) -> None:
    for key in (
        "binary_contact_converted_to_load",
        "pressure_contact_means_occupied",
        "no_pressure_contact_means_empty",
        "seat_occupancy_inferred",
        "occupant_identity_inferred",
        "heartbeat_measured",
        "medical_state_inferred",
        "emergency_condition_inferred",
        "grants_authority",
    ):
        if payload.get(key) is not False:
            raise ValueError(
                "seat pressure %s must remain false" % key
            )
    if payload.get("read_only") is not True:
        raise ValueError("seat pressure evidence must remain read-only")


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


def _seat_message(
    state: str,
    pad_count: int,
    active_pad_count: int,
    lateral_state: str,
) -> str:
    if state == "FAILED":
        return "Seat pressure node failed"
    if state == "STALE":
        return "Last genuine pressure-pad observation is stale"
    if state == "DEGRADED":
        return "Seat pressure evidence is degraded"
    if state == "TRANSITION":
        return "Pressure contact is inside its debounce window"
    if state == "NO_CONTACT_CONFIRMED":
        return (
            "No pressure contact confirmed; seat occupancy not inferred"
        )
    return (
        "Pressure contact confirmed on %d of %d pads, %s; "
        "occupancy not inferred"
        % (
            active_pad_count,
            pad_count,
            lateral_state.lower().replace("_", " "),
        )
    )


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "seat pressure %s must be non-empty text" % key
        )
    return value.strip()


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError("seat pressure %s must be boolean" % key)
    return value


def _required_integer(
    payload: Mapping[str, Any],
    key: str,
    minimum: int,
    maximum: int,
) -> int:
    value = payload.get(key)
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            "seat pressure %s is outside supported bounds" % key
        )
    return value


def _finite_bounded_number(
    value: Any, label: str, minimum: float, maximum: float
) -> float:
    if isinstance(value, bool) or not isinstance(
        value, (int, float)
    ):
        raise ValueError("seat pressure %s must be numeric" % label)
    result = float(value)
    if (
        not math.isfinite(result)
        or not minimum <= result <= maximum
    ):
        raise ValueError(
            "seat pressure %s is outside supported bounds" % label
        )
    return result


def _finite_probability(value: Any) -> float:
    return _finite_bounded_number(
        value, "confidence", 0.0, 1.0
    )
