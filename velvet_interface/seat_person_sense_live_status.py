# SPDX-License-Identifier: GPL-3.0-only
"""Read-only projection for Velvet's zoned seat person-sense evidence."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from velvet_interface.core.body_state import BodyStateStore

BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"
_ROLES = {"MAIN_LOAD", "SIDE_BOLSTER", "EDGE_MOTION"}
_SEAT_ORDER = {
    "driver": 0,
    "front-passenger": 1,
    "rear-left": 2,
    "rear-right": 3,
}


@dataclass(frozen=True)
class SeatPersonSenseLiveSeat:
    seat_id: str
    state: str
    body_map_state: str = "UNAVAILABLE"
    heartbeat_state: str = "UNAVAILABLE"
    main_active: int = 0
    main_total: int = 0
    bolster_active: int = 0
    bolster_total: int = 0
    edge_active: int = 0
    edge_total: int = 0
    movement_detected: bool = False
    movement_intensity: float = 0.0
    movement_topology_complete: bool = False
    heartbeat_bpm: Optional[float] = None
    heartbeat_confidence: float = 0.0
    heartbeat_signal_quality: float = 0.0
    message: str = ""


@dataclass(frozen=True)
class SeatPersonSenseLiveStatus:
    available: bool
    state: str
    seats: Tuple[SeatPersonSenseLiveSeat, ...] = ()
    message: str = ""


def load_seat_person_sense_live_status(
    body_path: Path, now_monotonic: Optional[float] = None
) -> SeatPersonSenseLiveStatus:
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

        body_maps = {}  # type: Dict[str, Mapping[str, Any]]
        heartbeats = {}  # type: Dict[str, Mapping[str, Any]]
        for sensor in body.sensors:
            if sensor.sensor_type == "seat_person_sense_body_map":
                seat_id = _required_text(sensor.payload, "seat_id")
                if seat_id in body_maps:
                    raise ValueError("duplicate body-map evidence for %s" % seat_id)
                projection = _validate_body_map(sensor.payload)
                body_maps[seat_id] = {
                    "projection": projection,
                    "state": _sensor_state(sensor, health_by_module, current),
                }
            elif sensor.sensor_type == "seat_heartbeat_signal":
                seat_id = _required_text(sensor.payload, "seat_id")
                if seat_id in heartbeats:
                    raise ValueError("duplicate heartbeat evidence for %s" % seat_id)
                projection = _validate_heartbeat(sensor.payload)
                heartbeats[seat_id] = {
                    "projection": projection,
                    "state": _sensor_state(sensor, health_by_module, current),
                }

        seat_ids = sorted(
            set(body_maps) | set(heartbeats),
            key=lambda seat_id: (_SEAT_ORDER.get(seat_id, 99), seat_id),
        )
        if not seat_ids:
            return SeatPersonSenseLiveStatus(
                available=False,
                state="UNAVAILABLE",
                message="Seat person-sense evidence awaiting Runtime",
            )

        seats = []
        for seat_id in seat_ids:
            body_map = body_maps.get(seat_id)
            heartbeat = heartbeats.get(seat_id)
            body_state = body_map["state"] if body_map else "UNAVAILABLE"
            heartbeat_state = heartbeat["state"] if heartbeat else "UNAVAILABLE"
            state = _combined_state(body_state, heartbeat_state)
            body_projection = body_map["projection"] if body_map else {}
            heartbeat_projection = heartbeat["projection"] if heartbeat else {}
            seats.append(
                SeatPersonSenseLiveSeat(
                    seat_id=seat_id,
                    state=state,
                    body_map_state=body_state,
                    heartbeat_state=heartbeat_state,
                    main_active=int(body_projection.get("main_active", 0)),
                    main_total=int(body_projection.get("main_total", 0)),
                    bolster_active=int(body_projection.get("bolster_active", 0)),
                    bolster_total=int(body_projection.get("bolster_total", 0)),
                    edge_active=int(body_projection.get("edge_active", 0)),
                    edge_total=int(body_projection.get("edge_total", 0)),
                    movement_detected=bool(
                        body_projection.get("movement_detected", False)
                    ),
                    movement_intensity=float(
                        body_projection.get("movement_intensity", 0.0)
                    ),
                    movement_topology_complete=bool(
                        body_projection.get("movement_topology_complete", False)
                    ),
                    heartbeat_bpm=heartbeat_projection.get("heartbeat_bpm"),
                    heartbeat_confidence=float(
                        heartbeat_projection.get("heartbeat_confidence", 0.0)
                    ),
                    heartbeat_signal_quality=float(
                        heartbeat_projection.get("signal_quality", 0.0)
                    ),
                    message=_seat_message(state, body_state, heartbeat_state),
                )
            )

        aggregate = "ONLINE"
        if all(seat.state == "FAILED" for seat in seats):
            aggregate = "FAILED"
        elif any(seat.state in {"FAILED", "DEGRADED"} for seat in seats):
            aggregate = "DEGRADED"
        elif any(seat.state == "PARTIAL" for seat in seats):
            aggregate = "PARTIAL"
        return SeatPersonSenseLiveStatus(
            available=True,
            state=aggregate,
            seats=tuple(seats),
            message=(
                "%d seat person-sense map%s observed; no identity or medical state inferred"
                % (len(seats), "" if len(seats) == 1 else "s")
            ),
        )
    except FileNotFoundError:
        message = "Seat person-sense evidence awaiting Runtime snapshot"
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        message = "Seat person senses unavailable: %s" % exc
    return SeatPersonSenseLiveStatus(
        available=False, state="UNAVAILABLE", message=message
    )


def _sensor_state(sensor, health_by_module, current: float) -> str:
    health = health_by_module.get(sensor.module_id)
    if health is not None and health.state_after == "FAILED":
        return "FAILED"
    if sensor.freshness(current) == "stale":
        return "STALE"
    state = sensor.health_state.upper()
    if state not in {"ONLINE", "DEGRADED"}:
        raise ValueError("unsupported seat person-sense health state")
    return state


def _validate_body_map(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    _false_claims(
        payload,
        (
            "heartbeat_observed_by_this_adapter",
            "missing_heartbeat_means_absent",
            "person_presence_inferred",
            "seat_occupancy_inferred",
            "occupant_posture_inferred",
            "occupant_identity_inferred",
            "heartbeat_measured_by_pressure",
            "medical_state_inferred",
            "emergency_condition_inferred",
            "grants_authority",
        ),
    )
    if payload.get("read_only") is not True:
        raise ValueError("seat body-map evidence must remain read-only")
    if payload.get("person_sense_family") != "seat_person_sense":
        raise ValueError("seat body-map family is invalid")
    if payload.get("fusion_role") != "body_contact_and_movement_map":
        raise ValueError("seat body-map fusion role is invalid")

    mapped_pads = payload.get("mapped_pads")
    if not isinstance(mapped_pads, list) or not 1 <= len(mapped_pads) <= 32:
        raise ValueError("seat body map requires bounded mapped pads")
    if _required_integer(payload, "pad_count", 1, 32) != len(mapped_pads):
        raise ValueError("seat body-map pad count contradicts mapped pads")

    role_counts = _role_counts(payload.get("role_counts"), "role_counts")
    active_counts = _role_counts(
        payload.get("active_role_counts"), "active_role_counts", allow_missing=True
    )
    counted_roles = {role: 0 for role in _ROLES}
    counted_active = {role: 0 for role in _ROLES}
    seen = set()
    for index, pad in enumerate(mapped_pads):
        if not isinstance(pad, Mapping):
            raise ValueError("mapped pad %d must be an object" % index)
        pad_id = _required_text(pad, "pad_id")
        if pad_id in seen:
            raise ValueError("duplicate mapped pad ID")
        seen.add(pad_id)
        role = _required_text(pad, "role").upper()
        if role not in _ROLES:
            raise ValueError("unsupported mapped pad role")
        _required_text(pad, "surface")
        _required_text(pad, "side")
        _finite_number(pad.get("movement_weight"), 0.0, 100.0, "movement_weight")
        active = _required_bool(pad, "active")
        counted_roles[role] += 1
        if active:
            counted_active[role] += 1
    for role in _ROLES:
        if role_counts.get(role, 0) != counted_roles[role]:
            raise ValueError("body-map role count contradicts mapped pads")
        if active_counts.get(role, 0) != counted_active[role]:
            raise ValueError("body-map active-role count contradicts mapped pads")
    if counted_roles["MAIN_LOAD"] < 1:
        raise ValueError("body map must contain a main load pad")

    movement_detected = _required_bool(payload, "movement_detected")
    baseline = _required_bool(payload, "baseline_established")
    changed_pad_ids = _text_list(payload, "changed_pad_ids", 32)
    _text_list(payload, "changed_roles", 3)
    _text_list(payload, "changed_surfaces", 32)
    if movement_detected != bool(changed_pad_ids):
        raise ValueError("movement summary contradicts changed pads")
    if not baseline and movement_detected:
        raise ValueError("movement cannot be asserted before baseline")
    movement_intensity = _finite_number(
        payload.get("movement_intensity"), 0.0, 1.0, "movement_intensity"
    )
    if not movement_detected and movement_intensity != 0.0:
        raise ValueError("no movement must use zero movement intensity")

    return {
        "main_total": counted_roles["MAIN_LOAD"],
        "main_active": counted_active["MAIN_LOAD"],
        "bolster_total": counted_roles["SIDE_BOLSTER"],
        "bolster_active": counted_active["SIDE_BOLSTER"],
        "edge_total": counted_roles["EDGE_MOTION"],
        "edge_active": counted_active["EDGE_MOTION"],
        "movement_detected": movement_detected,
        "movement_intensity": movement_intensity,
        "movement_topology_complete": _required_bool(
            payload, "movement_topology_complete"
        ),
    }


def _validate_heartbeat(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    _false_claims(
        payload,
        (
            "missing_heartbeat_means_absent",
            "heartbeat_signal_is_medical_diagnosis",
            "person_presence_inferred",
            "seat_occupancy_inferred",
            "occupant_identity_inferred",
            "medical_state_inferred",
            "emergency_condition_inferred",
            "grants_authority",
        ),
    )
    if payload.get("read_only") is not True:
        raise ValueError("seat heartbeat evidence must remain read-only")
    if payload.get("person_sense_family") != "seat_person_sense":
        raise ValueError("seat heartbeat family is invalid")
    if payload.get("fusion_role") != "heartbeat_signal":
        raise ValueError("seat heartbeat fusion role is invalid")
    signal = _required_bool(payload, "signal_detected")
    bpm = payload.get("heartbeat_bpm")
    confidence = _finite_number(
        payload.get("heartbeat_confidence"), 0.0, 1.0, "heartbeat_confidence"
    )
    quality = _finite_number(
        payload.get("signal_quality"), 0.0, 1.0, "signal_quality"
    )
    _required_integer(payload, "measurement_window_ms", 100, 60000)
    if signal:
        bpm = _finite_number(bpm, 1.0, 300.0, "heartbeat_bpm")
        if confidence <= 0.0 or quality <= 0.0:
            raise ValueError("heartbeat signal requires positive quality and confidence")
    else:
        if bpm is not None or confidence != 0.0:
            raise ValueError("no heartbeat signal cannot carry BPM or confidence")
    return {
        "heartbeat_bpm": bpm,
        "heartbeat_confidence": confidence,
        "signal_quality": quality,
    }


def _combined_state(body_state: str, heartbeat_state: str) -> str:
    states = {body_state, heartbeat_state}
    if "FAILED" in states and states == {"FAILED"}:
        return "FAILED"
    if states & {"FAILED", "STALE", "DEGRADED"}:
        return "DEGRADED"
    if "UNAVAILABLE" in states:
        return "PARTIAL"
    return "ONLINE"


def _seat_message(state: str, body_state: str, heartbeat_state: str) -> str:
    if state == "FAILED":
        return "Seat person-sense witnesses failed"
    if state == "DEGRADED":
        return "Seat person-sense evidence is degraded or stale"
    if state == "PARTIAL":
        return "Seat person-sense evidence is partial; missing data is not inferred"
    return "Body-map and heartbeat witnesses online; no diagnosis inferred"


def _false_claims(payload: Mapping[str, Any], keys: Tuple[str, ...]) -> None:
    for key in keys:
        if payload.get(key) is not False:
            raise ValueError("seat person-sense %s must remain false" % key)


def _role_counts(value: Any, label: str, allow_missing: bool = False) -> Dict[str, int]:
    if not isinstance(value, Mapping):
        raise ValueError("%s must be an object" % label)
    unknown = set(value) - _ROLES
    if unknown:
        raise ValueError("%s has unsupported roles" % label)
    result = {}
    for role in _ROLES:
        if role not in value:
            if allow_missing:
                continue
            result[role] = 0
            continue
        result[role] = _bounded_int_value(value[role], 0, 32, label)
    return result


def _text_list(payload: Mapping[str, Any], key: str, maximum: int) -> Tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError("%s must be a bounded list" % key)
    result = []
    seen = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("%s entries must be text" % key)
        text = item.strip()
        if text in seen:
            raise ValueError("%s entries must be unique" % key)
        seen.add(text)
        result.append(text)
    return tuple(result)


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
        raise ValueError("seat person-sense %s must be non-empty text" % key)
    return value.strip()


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError("seat person-sense %s must be boolean" % key)
    return value


def _required_integer(
    payload: Mapping[str, Any], key: str, minimum: int, maximum: int
) -> int:
    if key not in payload:
        raise ValueError("seat person-sense %s is required" % key)
    return _bounded_int_value(payload[key], minimum, maximum, key)


def _bounded_int_value(value: Any, minimum: int, maximum: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("seat person-sense %s must be an integer" % label)
    if not minimum <= value <= maximum:
        raise ValueError("seat person-sense %s is outside bounds" % label)
    return value


def _finite_number(value: Any, minimum: float, maximum: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("seat person-sense %s must be numeric" % label)
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError("seat person-sense %s is outside bounds" % label)
    return result
