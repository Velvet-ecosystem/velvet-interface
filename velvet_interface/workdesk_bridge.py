# SPDX-License-Identifier: GPL-3.0-only
"""Narrow Founder presentation bridge for offline, evidence-labelled work cards."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

class WorkDeskUnavailable(RuntimeError):
    pass

class WorkDeskBridge:
    """No network, subprocess, credential or execution authority."""
    def __init__(self, snapshot_path: Path) -> None:
        self.snapshot_path = Path(snapshot_path).expanduser()

    def read(self) -> Dict[str, Any]:
        try:
            from services.founder_work_desk import load_workdesk_file, workdesk_report
        except ImportError as exc:
            raise WorkDeskUnavailable("Velvet Runtime Work Desk module is not installed") from exc
        try:
            report = workdesk_report(load_workdesk_file(self.snapshot_path))
        except (OSError, RuntimeError, ValueError, UnicodeError) as exc:
            raise WorkDeskUnavailable("offline Work Desk unavailable: %s" % exc) from exc
        if (report.get("schema") != "velvet.runtime.workdesk.report.v1"
                or report.get("authority") != "none" or report.get("read_only") is not True
                or report.get("mode") not in {"ghost", "owner_export"}):
            raise WorkDeskUnavailable("untrusted Work Desk report contract")
        return report
