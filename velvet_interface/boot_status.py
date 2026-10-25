# SPDX-License-Identifier: GPL-3.0-only
"""Pure read-only adapter from Runtime boot snapshots to interface state."""

from __future__ import annotations

import json
import os
from velvet_interface.runtime_health import validate_live_status
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
    session_id: str = ""


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


def view_model_from_snapshot(snapshot: Dict[str, Any], *, live_status=None, now=None, boot_id=None, process_probe=None) -> BootStatusViewModel:
    doctor = snapshot.get("doctor") if isinstance(snapshot.get("doctor"), dict) else {}
    service = snapshot.get("service") if isinstance(snapshot.get("service"), dict) else {}

    preflight_ok = doctor.get("ready") is True
    doctor_state = _state_text(doctor.get("state"), "UNKNOWN")
    route_count = snapshot.get("route_count")
    routes = f"{route_count} READ-ONLY" if type(route_count) is int else "READ-ONLY"
    blocked_reasons = _collect_reasons(doctor)
    continuity = "UNVERIFIED" if preflight_ok else doctor_state
    court, runtime, session_id = "BLOCKED", "UNKNOWN", ""
    try:
        live = validate_live_status(live_status, now=now, boot_id=boot_id, process_probe=process_probe)
        continuity, court = "VERIFIED", "READY"
        runtime = "ACTIVE" if live['state'] == 'ready' and live['modules_healthy'] else "DEGRADED"
        session_id = live['session_id']
        message = "Waiting for Mister" if runtime == "ACTIVE" else "Runtime module health degraded"
    except (ValueError, OSError, TypeError, IndexError, KeyError) as exc:
        message = (blocked_reasons[0] if blocked_reasons else
                   ("Preflight passed; " if preflight_ok else "") + str(exc))
        blocked_reasons += (str(exc),)

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
        session_id=session_id,
    )


def load_boot_snapshot(path: Path, *, live_status_path=None) -> BootStatusViewModel:
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
    status_path = Path(live_status_path or os.environ.get('VELVET_RUNTIME_STATUS_PATH',
                                                        '/opt/velvet/state/runtime_status.json'))
    try:
        if status_path.stat().st_size > 64 * 1024:
            raise ValueError('oversized status')
        live = json.loads(status_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        live = None
    return view_model_from_snapshot(payload, live_status=live)
