# SPDX-License-Identifier: GPL-3.0-only
"""Pure read-only adapter from Runtime boot snapshots to interface state."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class BootStatusViewModel:
    title: str
    subtitle: str
    continuity: str
    court: str
    runtime: str
    routes: str
    physical_control: str
    message: str
    blocked_reasons: Tuple[str, ...]


def _state_text(value: Any, fallback: str = "UNKNOWN") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text.upper() if text else fallback


def _collect_reasons(doctor: Dict[str, Any]) -> Tuple[str, ...]:
    reasons = []
    for check in doctor.get("checks", []):
        if not isinstance(check, dict):
            continue
        if check.get("ok") is False:
            name = check.get("name", "startup check")
            detail = check.get("detail") or check.get("error") or "blocked"
            reasons.append(f"{name}: {detail}")
    for error in doctor.get("errors", []):
        reasons.append(str(error))
    return tuple(reasons)


def view_model_from_snapshot(snapshot: Dict[str, Any]) -> BootStatusViewModel:
    doctor = snapshot.get("doctor") if isinstance(snapshot.get("doctor"), dict) else {}
    service = snapshot.get("service") if isinstance(snapshot.get("service"), dict) else {}

    ready = bool(doctor.get("ready"))
    doctor_state = _state_text(doctor.get("state"), "BLOCKED")
    active_state = _state_text(service.get("active_state"), "UNKNOWN")
    sub_state = _state_text(service.get("sub_state"), "UNKNOWN")

    route_count = snapshot.get("route_count")
    routes = f"{route_count} READ-ONLY" if isinstance(route_count, int) else "READ-ONLY"

    continuity = "VERIFIED" if ready else doctor_state
    court = "READY" if ready else "BLOCKED"
    runtime = "ACTIVE" if active_state == "ACTIVE" and sub_state == "RUNNING" else active_state
    blocked_reasons = _collect_reasons(doctor)

    if ready:
        message = "Waiting for Mister"
    elif blocked_reasons:
        message = blocked_reasons[0]
    else:
        message = "Startup blocked"

    return BootStatusViewModel(
        title="VELVET",
        subtitle="Founder Runtime",
        continuity=continuity,
        court=court,
        runtime=runtime,
        routes=routes,
        physical_control="DISABLED",
        message=message,
        blocked_reasons=blocked_reasons,
    )


def load_boot_snapshot(path: Path) -> BootStatusViewModel:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        payload = {
            "doctor": {
                "ready": False,
                "state": "snapshot_missing",
                "errors": [f"Boot snapshot not found: {path}"],
            },
            "service": {"active_state": "unknown", "sub_state": "unknown"},
        }
    except (OSError, json.JSONDecodeError) as exc:
        payload = {
            "doctor": {
                "ready": False,
                "state": "snapshot_unreadable",
                "errors": [str(exc)],
            },
            "service": {"active_state": "unknown", "sub_state": "unknown"},
        }

    if not isinstance(payload, dict):
        payload = {
            "doctor": {
                "ready": False,
                "state": "snapshot_invalid",
                "errors": ["Boot snapshot root must be a JSON object"],
            },
            "service": {"active_state": "unknown", "sub_state": "unknown"},
        }
    return view_model_from_snapshot(payload)
