# SPDX-License-Identifier: GPL-3.0-only
"""Owner-maintenance-gated Work Desk scene. Presentation only."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from velvet_interface.core.scene import Scene
from velvet_interface.workdesk_bridge import WorkDeskBridge

class VelourWorkDeskScene(Scene):
    def __init__(self, *, bridge: WorkDeskBridge, access_provider: Any,
                 scene_id: str = "velour_workdesk") -> None:
        super().__init__(scene_id)
        self.bridge = bridge
        self.access_provider = access_provider
        self._router = None
        self._widget = None

    def bind_router(self, router: Any) -> None:
        self._router = router

    def _has_access(self) -> bool:
        try:
            return self.access_provider() is True
        except Exception:
            return False

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        self._active = True
        if self._widget is not None and self._has_access():
            self._widget.refresh()

    def on_exit(self) -> None:
        self._active = False

    def render(self, surface: Any) -> Any:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
        width, height = surface.get_dimensions()
        widget = QWidget()
        widget.setFixedSize(width, height)
        widget.setStyleSheet(
            "QWidget { background:#151b25; color:#eee7dc; font-size:17px; }"
            "QLabel#header { color:#d8b56a; font-size:27px; font-weight:bold; }"
            "QPlainTextEdit { background:#232c37; color:#f4f1eb; padding:12px; }"
            "QPushButton { min-height:42px; padding:8px; }"
        )
        layout = QVBoxLayout(widget)
        title = QLabel("VELOUR | WORK & DECISION DESK")
        title.setObjectName("header")
        layout.addWidget(title)
        status = QLabel("")
        layout.addWidget(status)
        reader = QPlainTextEdit()
        reader.setReadOnly(True)
        layout.addWidget(reader, 1)
        def refresh() -> None:
            if not self._has_access():
                status.setText("LOCKED | OWNER MAINTENANCE REQUIRED")
                reader.setPlainText("No Work Desk information is available without owner maintenance access.")
                return
            try:
                report = self.bridge.read()
            except Exception:
                status.setText("UNAVAILABLE | NO VERIFIED LOCAL SNAPSHOT")
                reader.setPlainText("No trusted local Work Desk export is ready. Nothing was changed.")
                return
            state = "STALE" if report["stale"] else "SNAPSHOT"
            status.setText("%s | %s | READ ONLY | NO AUTHORITY" % (report["mode"].upper(), state))
            cards = []
            for item in report["items"]:
                cards.append(
                    "[%s / %s] %s\nFrom: %s | %s\nChanged: %s\nWhy: %s\nNext: %s\nEvidence: %s"
                    % (item["priority"].upper(), item["state"].upper(), item["title"],
                       item["source"], item["updated_at"], item["change"], item["why"],
                       item["next_action"], item["source_url"] or "local owner note")
                )
            reader.setPlainText("\n\n".join(cards) if cards else "No new or actionable Work Desk items.")
        widget.refresh = refresh
        button = QPushButton("Refresh local snapshot")
        button.clicked.connect(refresh)
        layout.addWidget(button)
        back = QPushButton("Back to Owner Maintenance")
        back.clicked.connect(lambda: self._router.back() if self._router else None)
        layout.addWidget(back)
        self._widget = widget
        refresh()
        return widget
