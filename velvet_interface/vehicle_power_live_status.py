# SPDX-License-Identifier: GPL-3.0-only
"""Read-only vehicle power projection from Runtime body-state evidence."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from velvet_interface.core.body_state import BodyStateStore


BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"


@dataclass(frozen=True)
class VehiclePowerLiveStatus:
    available: bool
    state: str
    freshness: str
    voltage_v: Optional[float] = None
    voltage_band: str = "UNKNOWN"
    ignition_state: str = "UNKNOWN"
    nominal_voltage_v: Optional[float] = None
    receipt_id: Optional[str] = None
    message: str = ""


def load_vehicle_power_live_status(
    body_path: Path,
    now_monotonic: Optional[float] = None,
) -> VehiclePowerLiveStatus:
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
                if item.sensor_type == "vehicle_power_state"
                or item.module_id == "vehicle-power-main"
            ),
            None,
        )
        health = next(
            (
                item
                for item in body.health_events
                if item.module_id == "vehicle-power-main"
            ),
            None,
        )

        if sensor is None:
            if health is not None and health.state_after == "FAILED":
                detail = str(
                    health.diagnostic_payload.get(
                        "detail", "Vehicle power input failed"
                    )
                )
                return VehiclePowerLiveStatus(
                    available=True,
                    state="FAILED",
                    freshness="unknown",
                    receipt_id=health.receipt_id,
                    message=detail,
                )
            return VehiclePowerLiveStatus(
                available=False,
                state="UNAVAILABLE",
                freshness="unknown",
                message="Vehicle power evidence awaiting Runtime",
            )

        payload = sensor.payload
        freshness = sensor.freshness(current)
        state = sensor.health_state
        if health is not None and health.state_after == "FAILED":
            state = "FAILED"
        elif freshness == "stale":
            state = "STALE"

        ignition_on = payload.get("ignition_on")
        if not isinstance(ignition_on, bool):
            raise ValueError("vehicle power ignition_on must be boolean")
        voltage_band = _required_text(payload, "voltage_band").upper()
        if voltage_band not in {"CRITICAL_LOW", "LOW", "NORMAL", "CHARGING", "HIGH"}:
            raise ValueError("unsupported vehicle voltage band")

        return VehiclePowerLiveStatus(
            available=True,
            state=state,
            freshness=freshness,
            voltage_v=_required_number(payload, "voltage_v"),
            voltage_band=voltage_band,
            ignition_state="ON" if ignition_on else "OFF",
            nominal_voltage_v=_optional_number(payload, "nominal_voltage_v"),
            receipt_id=sensor.receipt_id,
            message=_message(state, voltage_band, ignition_on, freshness),
        )
    except FileNotFoundError:
        message = "Vehicle power evidence awaiting Runtime snapshot"
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        message = "Vehicle power unavailable: %s" % exc
    return VehiclePowerLiveStatus(
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
        raise ValueError("vehicle power %s must be non-empty text" % key)
    return value.strip()


def _required_number(payload: Mapping[str, Any], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("vehicle power %s must be numeric" % key)
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("vehicle power %s must be finite and non-negative" % key)
    return number


def _optional_number(payload: Mapping[str, Any], key: str) -> Optional[float]:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("vehicle power %s must be numeric" % key)
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("vehicle power %s must be finite" % key)
    return number


def _message(state: str, band: str, ignition_on: bool, freshness: str) -> str:
    if state == "FAILED":
        return "Vehicle power input failed"
    if freshness == "stale":
        return "Last genuine vehicle power observation is stale"
    if band == "CRITICAL_LOW":
        return "Critical low supply voltage"
    if band == "LOW":
        return "Low supply voltage"
    if band == "HIGH":
        return "High supply voltage"
    if band == "CHARGING":
        return "Charging-range voltage; engine state not inferred"
    return "Ignition %s with normal supply voltage" % ("on" if ignition_on else "off")
