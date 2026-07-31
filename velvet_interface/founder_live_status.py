# SPDX-License-Identifier: GPL-3.0-only
"""Read-only combined boot and body status for the Founder surface."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from velvet_interface.boot_status import BootStatusViewModel, load_boot_snapshot
from velvet_interface.core.body_state import BodyStateStore


BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"


@dataclass(frozen=True)
class FounderLiveStatus:
    """One evidence-backed frame for the Founder Runtime window."""

    boot: BootStatusViewModel
    body_available: bool
    body_presence: str
    body_summary: str
    sensor_count: int
    health_event_count: int
    receipt_count: int
    body_error: Optional[str] = None

    def rows(self) -> Tuple[Tuple[str, str], ...]:
        body_value = (
            self.body_presence.upper() if self.body_available else "UNAVAILABLE"
        )
        return (
            ("Continuity", self.boot.continuity),
            ("Court", self.boot.court),
            ("Runtime", self.boot.runtime),
            ("Routes", self.boot.routes),
            ("Body", body_value),
            ("Sensors", str(self.sensor_count)),
            ("Health", str(self.health_event_count)),
            ("Receipts", str(self.receipt_count)),
            ("Physical Control", self.boot.physical_control),
        )

    @property
    def message(self) -> str:
        if self.body_error:
            return "%s | %s" % (self.boot.message, self.body_error)
        if self.body_summary:
            return "%s | %s" % (self.boot.message, self.body_summary)
        return self.boot.message


def load_founder_live_status(
    boot_path: Path,
    body_path: Path,
    now_monotonic: Optional[float] = None,
) -> FounderLiveStatus:
    """Load one safe Founder frame from two independent local snapshots."""

    boot = load_boot_snapshot(Path(boot_path))
    try:
        document = json.loads(Path(body_path).read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("body snapshot root must be an object")
        if document.get("schema") != BODY_STATE_SNAPSHOT_SCHEMA:
            raise ValueError("unsupported body snapshot schema")
        if document.get("read_only") is not True:
            raise ValueError("body snapshot must be read-only")
        if document.get("authority", "none") != "none":
            raise ValueError("body snapshot cannot carry authority")
        if (
            document.get("actuation_granted") is not False
            or document.get("actuation_performed") is not False
        ):
            raise ValueError("body snapshot cannot claim actuation")

        records = document.get("records")
        if not isinstance(records, list):
            raise ValueError("body snapshot records must be a list")

        store = BodyStateStore()
        store.apply_many(records)
        current_monotonic = (
            time.monotonic() if now_monotonic is None else now_monotonic
        )
        body = store.snapshot(current_monotonic)
        return FounderLiveStatus(
            boot=boot,
            body_available=True,
            body_presence=body.presence_state,
            body_summary=body.summary,
            sensor_count=len(body.sensors),
            health_event_count=len(body.health_events),
            receipt_count=len(body.receipt_ids),
        )
    except FileNotFoundError:
        body_error = "Body state awaiting Runtime snapshot"
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        body_error = "Body state unavailable: %s" % exc

    return FounderLiveStatus(
        boot=boot,
        body_available=False,
        body_presence="unavailable",
        body_summary="",
        sensor_count=0,
        health_event_count=0,
        receipt_count=0,
        body_error=body_error,
    )
