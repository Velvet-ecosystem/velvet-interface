# SPDX-License-Identifier: GPL-3.0-only
"""Compact read-only microphone input-health widget for Velvet surfaces."""

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

from velvet_interface.microphone_input_live_status import (
    load_microphone_input_live_status,
)


class QtMicrophoneInputStatusWidget(QWidget):
    """Display microphone capture health without opening audio hardware."""

    def __init__(
        self,
        body_snapshot: Path,
        refresh_ms: int = 1000,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for microphone input status widget")
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
            "QLabel#channels { color: #aeb5c3; }"
            "QLabel#message { color: #bfc5d2; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(4)
        title = QLabel("MICROPHONE INPUT")
        title.setFont(QFont("Sans Serif", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(2)
        for row, label_text in enumerate(
            ("State", "Device", "Channels", "Rate", "Activity", "Freshness")
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

        self.channel_summary = QLabel("No channel evidence")
        self.channel_summary.setObjectName("channels")
        self.channel_summary.setTextFormat(Qt.PlainText)
        self.channel_summary.setWordWrap(True)
        self.channel_summary.setAlignment(Qt.AlignCenter)
        root.addWidget(self.channel_summary)

        self.message = QLabel("Awaiting microphone input-health evidence")
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
        status = load_microphone_input_live_status(self.body_snapshot)
        self._values["State"].setText(status.state)
        self._values["Device"].setText(status.device_alias)
        self._values["Channels"].setText(
            "-" if status.channel_count == 0 else str(status.channel_count)
        )
        self._values["Rate"].setText(
            "-" if status.sample_rate_hz == 0 else "%d Hz" % status.sample_rate_hz
        )
        self._values["Activity"].setText(
            "%d active / %d quiet"
            % (status.active_channels, status.quiet_channels)
            if status.channel_count
            else "-"
        )
        self._values["Freshness"].setText(status.freshness.upper())
        if status.channels:
            self.channel_summary.setText(
                " | ".join(
                    "%s: %s" % (channel.label, channel.state)
                    for channel in status.channels
                )
            )
        else:
            self.channel_summary.setText("No channel evidence")
        self.message.setText(status.message)
