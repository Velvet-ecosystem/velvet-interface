# SPDX-License-Identifier: GPL-3.0-only
"""Ambient evidence-only Velvet presence layer for the Founder home surface."""

from __future__ import annotations

from pathlib import Path

try:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QColor, QPainter, QPen
    from PyQt5.QtWidgets import QWidget

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]

from velvet_interface.velvet_presence_live_status import (
    VelvetPresenceStatus,
    load_velvet_presence_status,
)


class QtVelvetPresenceWidget(QWidget):
    """Draw a non-interactive local-presence orb from verified local evidence."""

    _STATE_COLORS = {
        "READY": (216, 181, 106),
        "AWAKE": (116, 162, 210),
        "DEGRADED": (201, 111, 94),
        "WAITING": (125, 130, 140),
    }

    def __init__(
        self,
        boot_snapshot: Path,
        conversation_socket: Path,
        refresh_ms: int = 1000,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for Velvet presence widget")
        if not 250 <= int(refresh_ms) <= 60000:
            raise ValueError("refresh_ms must be between 250 and 60000")
        super().__init__()
        self.boot_snapshot = Path(boot_snapshot)
        self.conversation_socket = Path(conversation_socket)
        self._status = VelvetPresenceStatus(
            state="WAITING",
            runtime_state="UNKNOWN",
            conversation_available=False,
            message="Awaiting local Runtime evidence",
        )

        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        self.timer = QTimer(self)
        self.timer.setInterval(int(refresh_ms))
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
        self._status = load_velvet_presence_status(
            self.boot_snapshot,
            self.conversation_socket,
        )
        self.setToolTip(self._status.message)
        self.setAccessibleName("Velvet presence: %s" % self._status.state)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rgb = self._STATE_COLORS.get(
            self._status.state,
            self._STATE_COLORS["WAITING"],
        )
        width = max(1, self.width())
        height = max(1, self.height())
        diameter = max(12, min(width, height) - 18)
        left = (width - diameter) // 2
        top = (height - diameter) // 2

        outer = QColor(*rgb, 52)
        middle = QColor(*rgb, 118)
        core = QColor(*rgb, 205)

        painter.setPen(QPen(outer, 8))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(left - 4, top - 4, diameter + 8, diameter + 8)

        painter.setPen(QPen(middle, 2))
        painter.setBrush(middle)
        painter.drawEllipse(left, top, diameter, diameter)

        inner = max(6, int(diameter * 0.46))
        inner_left = (width - inner) // 2
        inner_top = (height - inner) // 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(core)
        painter.drawEllipse(inner_left, inner_top, inner, inner)
        painter.end()
