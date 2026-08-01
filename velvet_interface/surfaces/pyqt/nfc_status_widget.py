# SPDX-License-Identifier: GPL-3.0-only
"""Compact verification-only contactless factor widget."""

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

from velvet_interface.nfc_live_status import load_nfc_live_status


class QtNfcStatusWidget(QWidget):
    """Display contactless evidence without claiming completed verification."""

    def __init__(self, body_snapshot: Path, refresh_ms: int = 500) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for NFC status widget")
        if not 250 <= int(refresh_ms) <= 60000:
            raise ValueError("refresh_ms must be between 250 and 60000")
        super().__init__()
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
        title = QLabel("NFC FACTOR")
        title.setFont(QFont("Sans Serif", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(2)
        for row, label_text in enumerate(
            ("State", "Reader", "Factor", "Label", "Role", "Freshness", "Confidence")
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

        self.message = QLabel("Awaiting contactless evidence")
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
        status = load_nfc_live_status(self.body_snapshot)
        self._values["State"].setText(status.state)
        self._values["Reader"].setText(status.reader_state)
        self._values["Factor"].setText(status.match_state)
        self._values["Label"].setText(status.label or "-")
        self._values["Role"].setText(status.role_hint or "-")
        self._values["Freshness"].setText(status.freshness.upper())
        self._values["Confidence"].setText(
            "-"
            if status.factor_confidence is None
            else "%.0f%%" % (status.factor_confidence * 100.0)
        )
        self.message.setText(status.message)
