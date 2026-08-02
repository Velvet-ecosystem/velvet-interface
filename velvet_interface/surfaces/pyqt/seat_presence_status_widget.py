# SPDX-License-Identifier: GPL-3.0-only
"""Compact read-only aggregate seat-evidence widget."""

from __future__ import annotations

from pathlib import Path

try:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]

from velvet_interface.seat_presence_live_status import (
    load_seat_presence_live_status,
)
from velvet_interface.seat_pressure_live_status import (
    load_seat_pressure_live_status,
    seat_evidence_relationship,
)

_SEAT_ORDER = {
    "driver": 0,
    "front-passenger": 1,
    "rear-left": 2,
    "rear-right": 3,
}


class QtSeatPresenceStatusWidget(QWidget):
    """Display Runtime radar and pressure evidence without authority access."""

    def __init__(self, body_snapshot: Path, refresh_ms: int = 1000) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for seat presence status widget")
        if not 250 <= int(refresh_ms) <= 60000:
            raise ValueError("refresh_ms must be between 250 and 60000")
        super().__init__()
        self.body_snapshot = Path(body_snapshot)
        self.setStyleSheet(
            "QWidget { background: rgba(7, 8, 12, 205); color: #e8e3db; "
            "border: 1px solid rgba(216, 181, 106, 110); border-radius: 10px; }"
            "QLabel { background: transparent; border: none; }"
            "QLabel#state { color: #f2ede4; }"
            "QLabel#seats { color: #c7ccd6; }"
            "QLabel#message { color: #9fa6b5; }"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(4)
        title = QLabel("SEAT EVIDENCE")
        title.setFont(QFont("Sans Serif", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)
        self.state = QLabel("UNAVAILABLE")
        self.state.setObjectName("state")
        self.state.setAlignment(Qt.AlignCenter)
        root.addWidget(self.state)
        self.seats = QLabel("Awaiting seat evidence")
        self.seats.setObjectName("seats")
        self.seats.setTextFormat(Qt.PlainText)
        self.seats.setWordWrap(True)
        root.addWidget(self.seats)
        self.message = QLabel("Occupancy is not inferred")
        self.message.setObjectName("message")
        self.message.setTextFormat(Qt.PlainText)
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignCenter)
        root.addWidget(self.message)
        self.timer = QTimer(self)
        self.timer.setInterval(int(refresh_ms))
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
        radar_status = load_seat_presence_live_status(self.body_snapshot)
        pressure_status = load_seat_pressure_live_status(self.body_snapshot)
        radar_by_seat = {seat.seat_id: seat for seat in radar_status.seats}
        pressure_by_seat = {
            seat.seat_id: seat for seat in pressure_status.seats
        }
        seat_ids = sorted(
            set(radar_by_seat) | set(pressure_by_seat),
            key=lambda seat_id: (_SEAT_ORDER.get(seat_id, 99), seat_id),
        )

        states = {radar_status.state, pressure_status.state}
        if states == {"UNAVAILABLE"}:
            aggregate = "UNAVAILABLE"
        elif "FAILED" in states:
            aggregate = "DEGRADED" if len(seat_ids) else "FAILED"
        elif "DEGRADED" in states:
            aggregate = "DEGRADED"
        else:
            aggregate = "ONLINE"
        self.state.setText(aggregate)

        lines = []
        for seat_id in seat_ids:
            radar = radar_by_seat.get(seat_id)
            pressure = pressure_by_seat.get(seat_id)
            radar_state = radar.state if radar is not None else "UNAVAILABLE"
            pressure_state = (
                pressure.state if pressure is not None else "UNAVAILABLE"
            )
            movement = (
                radar.movement_state if radar is not None else "UNKNOWN"
            )
            distance = (
                "-"
                if radar is None or radar.detection_distance_cm is None
                else "%d cm" % radar.detection_distance_cm
            )
            pads = (
                "-"
                if pressure is None
                else "%d/%d %s"
                % (
                    pressure.active_pad_count,
                    pressure.pad_count,
                    pressure.lateral_state,
                )
            )
            relationship = seat_evidence_relationship(
                radar_state, pressure_state
            )
            lines.append(
                "%s | R %s %s %s | P %s %s | %s"
                % (
                    seat_id,
                    radar_state,
                    movement,
                    distance,
                    pressure_state,
                    pads,
                    relationship,
                )
            )
        self.seats.setText(
            "\n".join(lines) if lines else "Awaiting seat evidence"
        )
        if seat_ids:
            self.message.setText(
                "%d seat%s observed; radar and pressure remain evidence only"
                % (len(seat_ids), "" if len(seat_ids) == 1 else "s")
            )
        else:
            self.message.setText(
                "Radar and pressure evidence awaiting Runtime"
            )
