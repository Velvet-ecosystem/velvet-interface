# SPDX-License-Identifier: GPL-3.0-only
"""Compact evidence-backed Founder body widget for full image surfaces."""

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

from velvet_interface.founder_live_status import load_founder_live_status


class QtFounderBodyStatusWidget(QWidget):
    """Show real boot and body evidence without acquiring Runtime access."""

    def __init__(
        self,
        boot_snapshot: Path,
        body_snapshot: Path,
        refresh_ms: int = 1000,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for Founder body widget")
        if not 250 <= int(refresh_ms) <= 60000:
            raise ValueError("refresh_ms must be between 250 and 60000")
        super().__init__()

        self.boot_snapshot = Path(boot_snapshot)
        self.body_snapshot = Path(body_snapshot)
        self._values = {}  # type: Dict[str, QLabel]

        self.setStyleSheet(
            "QWidget { background: rgba(7, 8, 12, 205); color: #e8e3db; "
            "border: 1px solid rgba(216, 181, 106, 110); border-radius: 10px; }"
            "QLabel { background: transparent; border: none; }"
            "QLabel#label { color: #8d93a3; }"
            "QLabel#value { color: #f2ede4; }"
            "QLabel#message { color: #bfc5d2; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(4)
        title = QLabel("BODY")
        title.setFont(QFont("Sans Serif", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(2)
        for row, label_text in enumerate(
            ("Runtime", "Body", "Sensors", "Health", "Receipts", "Control")
        ):
            label = QLabel(label_text)
            label.setObjectName("label")
            value = QLabel("UNAVAILABLE")
            value.setObjectName("value")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, row, 0)
            grid.addWidget(value, row, 1)
            self._values[label_text] = value
        root.addLayout(grid)

        self.message = QLabel("Awaiting evidence")
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
        status = load_founder_live_status(
            self.boot_snapshot,
            self.body_snapshot,
        )
        self._values["Runtime"].setText(status.boot.runtime)
        self._values["Body"].setText(
            status.body_presence.upper() if status.body_available else "UNAVAILABLE"
        )
        self._values["Sensors"].setText(str(status.sensor_count))
        self._values["Health"].setText(str(status.health_event_count))
        self._values["Receipts"].setText(str(status.receipt_count))
        self._values["Control"].setText(status.boot.physical_control)
        self.message.setText(status.message)
