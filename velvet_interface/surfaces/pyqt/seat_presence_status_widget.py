# SPDX-License-Identifier: GPL-3.0-only
"""Compact read-only aggregate seat-presence widget."""

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

from velvet_interface.seat_presence_live_status import load_seat_presence_live_status


class QtSeatPresenceStatusWidget(QWidget):
    """Display Runtime seat-radar evidence without sensor or authority access."""

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
        title = QLabel("SEAT PRESENCE")
        title.setFont(QFont("Sans Serif", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)
        self.state = QLabel("UNAVAILABLE")
        self.state.setObjectName("state")
        self.state.setAlignment(Qt.AlignCenter)
        root.addWidget(self.state)
        self.seats = QLabel("Awaiting seat-radar evidence")
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
        status = load_seat_presence_live_status(self.body_snapshot)
        self.state.setText(status.state)
        lines = []
        for seat in status.seats:
            distance = "-" if seat.detection_distance_cm is None else "%d cm" % seat.detection_distance_cm
            lines.append(
                "%s | %s | %s | %s" % (
                    seat.seat_id, seat.state, seat.movement_state, distance
                )
            )
        self.seats.setText("\n".join(lines) if lines else "Awaiting seat-radar evidence")
        self.message.setText(status.message)
