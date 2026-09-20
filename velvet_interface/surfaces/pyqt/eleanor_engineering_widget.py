# SPDX-License-Identifier: GPL-3.0-only
"""Read-only Eleanor Engineering workbench for Founder."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Optional, Tuple
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
from velvet_interface.eleanor_bridge import EleanorBridge, EleanorUnavailable

class QtEleanorEngineeringWidget(QWidget):
    def __init__(self, bridge: EleanorBridge, target_size: Tuple[int, int], background_path: Path, on_back: Optional[Callable[[], Any]] = None) -> None:
        super().__init__()
        self.bridge, self.on_back = bridge, on_back
        self._background = QPixmap(str(background_path))
        self.setFixedSize(*target_size)
        self.setObjectName("eleanorWorkbench")
        self.setStyleSheet(
            "QWidget#eleanorWorkbench { color:#24180f; }"
            "QWidget#eleanorPanel { background:rgba(246,235,211,220); border:1px solid rgba(78,51,28,150); border-radius:10px; }"
            "QLabel#eleanorTitle { font-size:27px; font-weight:600; color:#3a2415; }"
            "QLabel#eleanorSection { font-size:16px; font-weight:600; color:#4e321c; }"
            "QTextEdit,QTableWidget { background:rgba(255,252,244,235); color:#21170f; }"
            "QPushButton { min-height:34px; padding:4px 10px; }"
        )
        root = QVBoxLayout(self); root.setContentsMargins(22,18,22,18)
        header = QHBoxLayout()
        title = QLabel("ELEANOR ENGINEERING"); title.setObjectName("eleanorTitle")
        self.status = QLabel("Read-only engineering workbench")
        self.refresh_button, self.back = QPushButton("Refresh"), QPushButton("Back")
        header.addWidget(title); header.addWidget(self.status,1); header.addWidget(self.refresh_button); header.addWidget(self.back)
        root.addLayout(header)
        body = QHBoxLayout()
        left = self._panel(); ll = QVBoxLayout(left)
        section = QLabel("Validation"); section.setObjectName("eleanorSection")
        self.validation = QTextEdit(); self.validation.setReadOnly(True)
        ll.addWidget(section); ll.addWidget(self.validation,1)
        right = self._panel(); rl = QVBoxLayout(right)
        ct = QLabel("Requirement Coverage"); ct.setObjectName("eleanorSection")
        self.coverage = QTableWidget(0,4); self.coverage.setHorizontalHeaderLabels(["Requirement","Priority","Status","Coverage"])
        self.coverage.horizontalHeader().setStretchLastSection(True)
        rl.addWidget(ct); rl.addWidget(self.coverage,1)
        guard = QLabel("AUTHORITY: PRESENTATION ONLY\nPhysical execution: DISABLED\nFabrication release: DISABLED\nVehicle installation: DISABLED\nUnattended machine execution: DISABLED")
        guard.setWordWrap(True); rl.addWidget(guard)
        body.addWidget(left,2); body.addWidget(right,3); root.addLayout(body,1)
        self.back.clicked.connect(self._go_back); self.refresh_button.clicked.connect(self.refresh)
        self.refresh()

    def _panel(self) -> QWidget:
        panel=QWidget(); panel.setObjectName("eleanorPanel"); return panel

    def paintEvent(self, event: Any) -> None:
        painter=QPainter(self)
        if self._background.isNull(): painter.fillRect(self.rect(),Qt.black); return
        scaled=self._background.scaled(self.size(),Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation)
        x=(scaled.width()-self.width())//2; y=(scaled.height()-self.height())//2
        painter.drawPixmap(0,0,scaled,x,y,self.width(),self.height())

    def refresh(self) -> None:
        try:
            validation, coverage = self.bridge.validate(), self.bridge.coverage()
        except (EleanorUnavailable,OSError,TypeError,ValueError) as exc:
            self.status.setText("Eleanor unavailable"); self.validation.setPlainText(str(exc)); self.coverage.setRowCount(0); return
        errors, warnings = int(validation.get("errors",0)), int(validation.get("warnings",0))
        lines=["errors=%d warnings=%d"%(errors,warnings)]
        for issue in validation.get("issues",[]):
            if isinstance(issue,dict): lines.append("%s %s: %s"%(str(issue.get("severity","")).upper(),issue.get("code",""),issue.get("message","")))
        self.validation.setPlainText("\n".join(lines))
        rows=coverage.get("requirements",[]); self.coverage.setRowCount(len(rows))
        for ri,row in enumerate(rows):
            for ci,value in enumerate((row.get("id",""),row.get("priority",""),row.get("requirement_status",""),row.get("coverage_state",""))):
                self.coverage.setItem(ri,ci,QTableWidgetItem(str(value)))
        self.status.setText("Eleanor online • %d requirements • errors=%d warnings=%d"%(len(rows),errors,warnings))

    def _go_back(self) -> None:
        if self.on_back is not None: self.on_back()
