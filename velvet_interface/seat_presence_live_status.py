# SPDX-License-Identifier: GPL-3.0-only
"""Read-only aggregate seat-radar projection from Runtime body evidence."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from velvet_interface.core.body_state import BodyStateStore

BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"
_ALLOWED_MOVEMENT = {
    "MOVING", "STATIONARY", "MOVING_AND_STATIONARY", "NO_RADAR_PRESENCE"
}
_SEAT_ORDER = {"driver": 0, "front-passenger": 1, "rear-left": 2, "rear-right": 3}

@dataclass(frozen=True)
class SeatPresenceLiveSeat:
    seat_id: str
    state: str
    freshness: str
    movement_state: str = "UNKNOWN"
    detection_distance_cm: Optional[int] = None
    node_id: str = "-"
    sensor_model: str = "-"
    confidence: float = 0.0
    receipt_id: Optional[str] = None
    message: str = ""

@dataclass(frozen=True)
class SeatPresenceLiveStatus:
    available: bool
    state: str
    seats: Tuple[SeatPresenceLiveSeat, ...] = ()
    message: str = ""


def load_seat_presence_live_status(body_path: Path,
                                   now_monotonic: Optional[float] = None) -> SeatPresenceLiveStatus:
    try:
        document = json.loads(Path(body_path).read_text(encoding="utf-8"))
        _validate_snapshot(document)
        store = BodyStateStore()
        store.apply_many(document["records"])
        current = time.monotonic() if now_monotonic is None else float(now_monotonic)
        if not math.isfinite(current) or current < 0:
            raise ValueError("current monotonic time must be finite and non-negative")
        body = store.snapshot(current)
        health_by_module = {item.module_id: item for item in body.health_events}
        sensor_modules = {
            item.module_id for item in body.sensors
            if item.sensor_type == "seat_presence_radar"
        }
        seats = []
        seen = set()
        for sensor in body.sensors:
            if sensor.sensor_type != "seat_presence_radar":
                continue
            payload = sensor.payload
            seat_id = _required_text(payload, "seat_id")
            if seat_id in seen:
                raise ValueError("duplicate seat presence evidence for %s" % seat_id)
            seen.add(seat_id)
            _validate_observation_only_claims(payload)
            present = _required_bool(payload, "radar_presence_detected")
            moving = _required_bool(payload, "moving_target_detected")
            stationary = _required_bool(payload, "stationary_target_detected")
            if present != (moving or stationary):
                raise ValueError("seat radar presence fields are contradictory")
            movement = _required_text(payload, "movement_state").upper()
            if movement not in _ALLOWED_MOVEMENT:
                raise ValueError("unsupported seat movement state")
            if movement != _movement_state(moving, stationary):
                raise ValueError("seat movement summary contradicts target fields")
            distance = _optional_integer(payload, "detection_distance_cm", 0, 600)
            if present != (distance is not None):
                raise ValueError("seat distance contradicts radar presence")
            freshness = sensor.freshness(current)
            state = sensor.health_state.upper()
            health = health_by_module.get(sensor.module_id)
            if health is not None and health.state_after == "FAILED":
                state = "FAILED"
            elif freshness == "stale":
                state = "STALE"
            elif state == "ONLINE":
                state = "RADAR_PRESENT" if present else "NO_RADAR_PRESENCE"
            elif state != "DEGRADED":
                raise ValueError("unsupported seat health state")
            seats.append(SeatPresenceLiveSeat(
                seat_id=seat_id,
                state=state,
                freshness=freshness,
                movement_state=movement,
                detection_distance_cm=distance,
                node_id=sensor.node_id,
                sensor_model=_required_text(payload, "sensor_model"),
                confidence=_finite_probability(sensor.confidence),
                receipt_id=sensor.receipt_id,
                message=_seat_message(state, movement, distance),
            ))

        for health in body.health_events:
            if health.module_id in sensor_modules:
                continue
            diagnostic = health.diagnostic_payload
            seat_id = diagnostic.get("seat_id")
            if health.state_after != "FAILED" or not isinstance(seat_id, str) or not seat_id.strip():
                continue
            if seat_id in seen:
                continue
            seen.add(seat_id)
            seats.append(SeatPresenceLiveSeat(
                seat_id=seat_id.strip(), state="FAILED", freshness="unknown",
                node_id=health.node_id, receipt_id=health.receipt_id,
                message=str(diagnostic.get("detail", "Seat node failed")),
            ))

        seats.sort(key=lambda item: (_SEAT_ORDER.get(item.seat_id, 99), item.seat_id))
        if not seats:
            return SeatPresenceLiveStatus(
                available=False, state="UNAVAILABLE",
                message="Seat-presence evidence awaiting Runtime",
            )
        aggregate = "ONLINE"
        if any(item.state == "FAILED" for item in seats):
            aggregate = "DEGRADED" if any(item.state != "FAILED" for item in seats) else "FAILED"
        elif any(item.state in {"DEGRADED", "STALE"} for item in seats):
            aggregate = "DEGRADED"
        return SeatPresenceLiveStatus(
            available=True, state=aggregate, seats=tuple(seats),
            message="%d seat radar node%s observed; occupancy is not inferred" % (
                len(seats), "" if len(seats) == 1 else "s"
            ),
        )
    except FileNotFoundError:
        message = "Seat-presence evidence awaiting Runtime snapshot"
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        message = "Seat presence unavailable: %s" % exc
    return SeatPresenceLiveStatus(available=False, state="UNAVAILABLE", message=message)


def _validate_observation_only_claims(payload: Mapping[str, Any]) -> None:
    for key in (
        "no_detection_means_empty", "seat_occupancy_inferred",
        "occupant_identity_inferred", "heartbeat_measured",
        "medical_state_inferred", "emergency_condition_inferred",
        "grants_authority",
    ):
        if payload.get(key) is not False:
            raise ValueError("seat presence %s must remain false" % key)
    if payload.get("read_only") is not True:
        raise ValueError("seat presence evidence must remain read-only")


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


def _movement_state(moving: bool, stationary: bool) -> str:
    if moving and stationary:
        return "MOVING_AND_STATIONARY"
    if moving:
        return "MOVING"
    if stationary:
        return "STATIONARY"
    return "NO_RADAR_PRESENCE"


def _seat_message(state: str, movement: str, distance: Optional[int]) -> str:
    if state == "FAILED":
        return "Seat radar node failed"
    if state == "STALE":
        return "Last genuine seat-radar observation is stale"
    if state == "DEGRADED":
        return "Seat radar evidence is degraded"
    if state == "NO_RADAR_PRESENCE":
        return "No radar presence detected; seat occupancy not inferred"
    suffix = "" if distance is None else " at approximately %d cm" % distance
    return "%s radar presence%s; occupancy not inferred" % (
        movement.title().replace("_", " "), suffix
    )


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("seat presence %s must be non-empty text" % key)
    return value.strip()


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError("seat presence %s must be boolean" % key)
    return value


def _optional_integer(payload: Mapping[str, Any], key: str,
                      minimum: int, maximum: int) -> Optional[int]:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError("seat presence %s is outside supported bounds" % key)
    return value


def _finite_probability(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("seat presence confidence must be numeric")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError("seat presence confidence must be between zero and one")
    return result
