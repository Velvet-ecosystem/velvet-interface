# SPDX-License-Identifier: GPL-3.0-only
"""Read-only GNSS projection from the Runtime body-state snapshot."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from velvet_interface.core.body_state import BodyStateStore


BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"


@dataclass(frozen=True)
class GnssLiveStatus:
    available: bool
    state: str
    fix_label: str
    freshness: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    satellites: Optional[int] = None
    horizontal_dilution: Optional[float] = None
    altitude_m: Optional[float] = None
    speed_kmh: Optional[float] = None
    course_deg: Optional[float] = None
    gnss_utc: Optional[str] = None
    receipt_id: Optional[str] = None
    message: str = ""


def load_gnss_live_status(
    body_path: Path,
    now_monotonic: Optional[float] = None,
) -> GnssLiveStatus:
    try:
        document = json.loads(Path(body_path).read_text(encoding="utf-8"))
        _validate_snapshot(document)
        store = BodyStateStore()
        store.apply_many(document["records"])
        current = time.monotonic() if now_monotonic is None else float(now_monotonic)
        body = store.snapshot(current)
        sensor = next(
            (
                item
                for item in body.sensors
                if item.sensor_type == "gnss_fix" or item.module_id == "gnss-main"
            ),
            None,
        )
        health = next(
            (item for item in body.health_events if item.module_id == "gnss-main"),
            None,
        )
        if sensor is None:
            if health is not None and health.state_after == "FAILED":
                detail = str(health.diagnostic_payload.get("detail", "GNSS failed"))
                return GnssLiveStatus(
                    available=True,
                    state="FAILED",
                    fix_label="NO DATA",
                    freshness="unknown",
                    receipt_id=health.receipt_id,
                    message=detail,
                )
            return GnssLiveStatus(
                available=False,
                state="UNAVAILABLE",
                fix_label="NO DATA",
                freshness="unknown",
                message="GNSS evidence awaiting Runtime",
            )

        payload = sensor.payload
        freshness = sensor.freshness(current)
        has_fix = payload.get("has_fix") is True
        state = sensor.health_state
        if health is not None and health.state_after == "FAILED":
            state = "FAILED"
        elif freshness == "stale":
            state = "STALE"

        return GnssLiveStatus(
            available=True,
            state=state,
            fix_label="FIX" if has_fix else "NO FIX",
            freshness=freshness,
            latitude=_optional_number(payload, "latitude") if has_fix else None,
            longitude=_optional_number(payload, "longitude") if has_fix else None,
            satellites=_optional_int(payload, "satellites"),
            horizontal_dilution=_optional_number(payload, "horizontal_dilution"),
            altitude_m=_optional_number(payload, "altitude_m") if has_fix else None,
            speed_kmh=_optional_number(payload, "speed_kmh") if has_fix else None,
            course_deg=_optional_number(payload, "course_deg") if has_fix else None,
            gnss_utc=_optional_text(payload.get("gnss_utc")),
            receipt_id=sensor.receipt_id,
            message=_message(state, has_fix, freshness),
        )
    except FileNotFoundError:
        message = "GNSS evidence awaiting Runtime snapshot"
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        message = "GNSS unavailable: %s" % exc
    return GnssLiveStatus(
        available=False,
        state="UNAVAILABLE",
        fix_label="NO DATA",
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


def _optional_number(payload: Mapping[str, Any], key: str) -> Optional[float]:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("GNSS %s must be numeric" % key)
    return float(value)


def _optional_int(payload: Mapping[str, Any], key: str) -> Optional[int]:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("GNSS %s must be an integer" % key)
    return value


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("GNSS text field must be non-empty when present")
    return value.strip()


def _message(state: str, has_fix: bool, freshness: str) -> str:
    if state == "FAILED":
        return "Receiver failed"
    if freshness == "stale":
        return "Last genuine GNSS observation is stale"
    if not has_fix:
        return "Receiver online, waiting for navigation fix"
    return "Live read-only GNSS fix"
