# SPDX-License-Identifier: GPL-3.0-only
"""Compact read-only lighting context widget."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

try:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]

from velvet_interface.lighting_live_status import load_lighting_live_status


class QtLightingContextWidget(QWidget):
    """Display real ambient-light context while fixture control stays unbound."""

    def __init__(self, body_snapshot: Path, refresh_ms: int = 1000) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for lighting context widget")
        if not 250 <= int(refresh_ms) <= 60000:
            raise ValueError("refresh_ms must be between 250 and 60000")
        super().__init__()
        self.body_snapshot = Path(body_snapshot)
        self._values = {}  # type: Dict[str, QLabel]
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.setStyleSheet(
            "QWidget { background: rgba(7, 8, 12, 185); color: #e8e3db; "
            "border: 1px solid rgba(216, 181, 106, 100); border-radius: 10px; }"
            "QLabel { background: transparent; border: none; }"
            "QLabel#label { color: #8d93a3; }"
            "QLabel#value { color: #f2ede4; }"
            "QLabel#message { color: #bfc5d2; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 9, 12, 9)
        root.setSpacing(3)
        title = QLabel("LIGHTING CONTEXT")
        title.setFont(QFont("Sans Serif", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(1)
        for row, label_text in enumerate(
            ("State", "Ambient", "Freshness", "Observer", "Fixtures", "Control")
        ):
            label = QLabel(label_text)
            label.setObjectName("label")
            value = QLabel("-")
            value.setObjectName("value")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, row, 0)
            grid.addWidget(value, row, 1)
            self._values[label_text] = value
        root.addLayout(grid)

        self.message = QLabel("Awaiting ambient-light evidence")
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
        status = load_lighting_live_status(self.body_snapshot)
        self._values["State"].setText(status.state)
        self._values["Ambient"].setText(
            "-"
            if status.ambient_light_lux is None
            else "%.0f lx" % status.ambient_light_lux
        )
        self._values["Freshness"].setText(status.freshness.upper())
        self._values["Observer"].setText(status.observer or "-")
        self._values["Fixtures"].setText(status.lighting_observer_state)
        self._values["Control"].setText(status.physical_control_state)
        self.message.setText(status.message)
