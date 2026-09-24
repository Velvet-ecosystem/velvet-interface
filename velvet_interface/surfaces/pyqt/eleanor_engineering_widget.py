# SPDX-License-Identifier: GPL-3.0-only
"""Read-only Eleanor Engineering workbench for Founder."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Optional, Tuple
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
from velvet_interface.eleanor_bridge import EleanorBridge, EleanorUnavailable

# Interactive workbench frame fitted to the inner parchment on the physical
# Founder display. This is intentionally wider than the Forge read-only ink
# frame because Eleanor needs room for a live validation pane and a table.
_ELEANOR_WORKBENCH_RECT = (0.13, 0.16, 0.74, 0.62)


class QtEleanorEngineeringWidget(QWidget):
    def __init__(self, bridge: EleanorBridge, target_size: Tuple[int, int], background_path: Path, on_back: Optional[Callable[[], Any]] = None) -> None:
        super().__init__()
        self.bridge, self.on_back = bridge, on_back
        self._background = QPixmap(str(background_path))
        self.setFixedSize(*target_size)
        self.setObjectName("eleanorWorkbench")
        self.setStyleSheet(
            "QWidget#eleanorWorkbench { color:#24180f; }"
            "QWidget#eleanorPanel { background:rgba(246,235,211,210); border:1px solid rgba(78,51,28,150); border-radius:10px; }"
            "QLabel#eleanorTitle { font-size:27px; font-weight:600; color:#3a2415; }"
            "QLabel#eleanorSection { font-size:16px; font-weight:600; color:#4e321c; }"
            "QTextEdit,QTableWidget { background:rgba(255,252,244,228); color:#21170f; }"
            "QPushButton { min-height:30px; padding:3px 9px; }"
        )

        self.content_frame = QWidget(self)
        self.content_frame.setAttribute(Qt.WA_TranslucentBackground, True)
        root = QVBoxLayout(self.content_frame)
        root.setContentsMargins(4, 2, 4, 4)
        root.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("ELEANOR ENGINEERING")
        title.setObjectName("eleanorTitle")
        self.status = QLabel("Read-only engineering workbench")
        self.refresh_button, self.back = QPushButton("Refresh"), QPushButton("Back")
        header.addWidget(title)
        header.addWidget(self.status, 1)
        header.addWidget(self.refresh_button)
        header.addWidget(self.back)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(8)
        left = self._panel()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(8, 6, 8, 8)
        section = QLabel("Validation")
        section.setObjectName("eleanorSection")
        self.validation = QTextEdit()
        self.validation.setReadOnly(True)
        ll.addWidget(section)
        ll.addWidget(self.validation, 1)

        right = self._panel()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 6, 8, 8)
        ct = QLabel("Requirement Coverage")
        ct.setObjectName("eleanorSection")
        self.coverage = QTableWidget(0, 4)
        self.coverage.setHorizontalHeaderLabels(["Requirement", "Priority", "Status", "Coverage"])
        self.coverage.horizontalHeader().setStretchLastSection(True)
        rl.addWidget(ct)
        rl.addWidget(self.coverage, 1)
        guard = QLabel(
            "AUTHORITY: PRESENTATION ONLY\n"
            "Physical execution: DISABLED\n"
            "Fabrication release: DISABLED\n"
            "Vehicle installation: DISABLED\n"
            "Unattended machine execution: DISABLED"
        )
        guard.setWordWrap(True)
        rl.addWidget(guard)

        body.addWidget(left, 2)
        body.addWidget(right, 3)
        root.addLayout(body, 1)

        self._position_content_frame()
        self.back.clicked.connect(self._go_back)
        self.refresh_button.clicked.connect(self.refresh)
        self.refresh()

    def _panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("eleanorPanel")
        return panel

    def _position_content_frame(self) -> None:
        x, y, width, height = _ELEANOR_WORKBENCH_RECT
        self.content_frame.setGeometry(
            int(round(self.width() * x)),
            int(round(self.height() * y)),
            max(1, int(round(self.width() * width))),
            max(1, int(round(self.height() * height))),
        )
        self.content_frame.raise_()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        if hasattr(self, "content_frame"):
            self._position_content_frame()

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        if self._background.isNull():
            painter.fillRect(self.rect(), Qt.black)
            return
        scaled = self._background.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = (scaled.width() - self.width()) // 2
        y = (scaled.height() - self.height()) // 2
        painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())

    def refresh(self) -> None:
        try:
            validation, coverage = self.bridge.validate(), self.bridge.coverage()
        except (EleanorUnavailable, OSError, TypeError, ValueError) as exc:
            self.status.setText("Eleanor unavailable")
            self.validation.setPlainText(str(exc))
            self.coverage.setRowCount(0)
            return
        errors, warnings = int(validation.get("errors", 0)), int(validation.get("warnings", 0))
        lines = ["errors=%d warnings=%d" % (errors, warnings)]
        for issue in validation.get("issues", []):
            if isinstance(issue, dict):
                lines.append(
                    "%s %s: %s"
                    % (
                        str(issue.get("severity", "")).upper(),
                        issue.get("code", ""),
                        issue.get("message", ""),
                    )
                )
        self.validation.setPlainText("\n".join(lines))
        rows = coverage.get("requirements", [])
        self.coverage.setRowCount(len(rows))
        for ri, row in enumerate(rows):
            for ci, value in enumerate(
                (
                    row.get("id", ""),
                    row.get("priority", ""),
                    row.get("requirement_status", ""),
                    row.get("coverage_state", ""),
                )
            ):
                self.coverage.setItem(ri, ci, QTableWidgetItem(str(value)))
        self.status.setText(
            "Eleanor online • %d requirements • errors=%d warnings=%d"
            % (len(rows), errors, warnings)
        )

    def _go_back(self) -> None:
        if self.on_back is not None:
            self.on_back()
