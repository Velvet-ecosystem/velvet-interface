# SPDX-License-Identifier: GPL-3.0-only
"""Protected owner-maintenance scene for Velvet's hidden Backroom layer.

The scene is a presentation boundary only. It does not create owner identity,
maintenance authority, Court grants, execution authority, or physical control.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from velvet_interface.core.scene import Scene


class VelvetsLegsScene(Scene):
    """Owner + maintenance gated hidden Founder workspace."""

    def __init__(
        self,
        *,
        access_provider: Any,
        physical_control_disabled_provider: Any,
        background_path: Optional[Path] = None,
        scene_id: str = "velvets_legs",
    ) -> None:
        super().__init__(scene_id)
        self.access_provider = access_provider
        self.physical_control_disabled_provider = physical_control_disabled_provider
        self.background_path = Path(background_path or "examples/assets/backroom.png")
        self._router = None
        self._surface = None
        self._widget = None
        self._rendered_access = None  # type: Optional[bool]

    def bind_router(self, router: Any) -> None:
        self._router = router

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        self._active = True
        access = self._has_access()
        if (
            self._widget is not None
            and self._rendered_access is not None
            and access != self._rendered_access
            and self._surface is not None
        ):
            invalidate = getattr(self._surface, "invalidate_scene", None)
            if callable(invalidate):
                invalidate(self.scene_id)
            self._widget = None

    def on_exit(self) -> None:
        self._active = False

    def render(self, surface: Any) -> Any:
        self._surface = surface
        access = self._has_access()
        self._rendered_access = access
        if not access:
            self._widget = self._render_locked(surface)
            return self._widget
        self._widget = self._render_unlocked(surface)
        return self._widget

    def _has_access(self) -> bool:
        try:
            return bool(self.access_provider())
        except Exception:
            return False

    def _physical_control_disabled(self) -> bool:
        try:
            return bool(self.physical_control_disabled_provider())
        except Exception:
            return False

    def _surface_studio_available(self) -> bool:
        if self._router is None:
            return False
        try:
            return "surface_studio" in self._router.list_scenes()
        except Exception:
            return False

    def _open_surface_studio(self) -> bool:
        if not self._has_access() or not self._surface_studio_available():
            return False
        return bool(self._router.navigate("surface_studio"))

    def _go_back(self) -> bool:
        if self._router is None:
            return False
        return bool(self._router.back())

    def _background_label(self, widget: Any, width: int, height: int) -> Any:
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtWidgets import QLabel

        label = QLabel(widget)
        label.setGeometry(0, 0, width, height)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: #07080c;")
        pixmap = QPixmap(str(self.background_path))
        if not pixmap.isNull():
            label.setPixmap(
                pixmap.scaled(
                    width,
                    height,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
        label.lower()
        return label

    def _render_locked(self, surface: Any) -> Any:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

        width, height = surface.get_dimensions()
        widget = QWidget()
        widget.setFixedSize(width, height)
        widget.setObjectName("velvetsLegsLocked")
        self._background_label(widget, width, height)

        panel = QWidget(widget)
        panel.setObjectName("lockedPanel")
        panel.setGeometry(int(width * 0.25), int(height * 0.25), int(width * 0.50), int(height * 0.50))
        panel.setStyleSheet(
            "QWidget#lockedPanel { background: rgba(7, 8, 12, 232); "
            "border: 1px solid rgba(216, 181, 106, 120); border-radius: 14px; color: #eee8df; }"
            "QLabel { background: transparent; border: none; }"
            "QLabel#title { color: #d8b56a; font-size: 28px; font-weight: bold; }"
            "QPushButton { min-width: 180px; min-height: 42px; }"
        )
        layout = QVBoxLayout(panel)
        layout.addStretch(1)
        title = QLabel("PROTECTED MAINTENANCE ACCESS")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        message = QLabel(
            "Verified owner presence and the protected maintenance unlock are both required.\n"
            "No maintenance tool or physical authority was opened."
        )
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        back = QPushButton("Back")
        back.clicked.connect(self._go_back)
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addWidget(back, alignment=Qt.AlignCenter)
        layout.addStretch(1)
        return widget

    def _render_unlocked(self, surface: Any) -> Any:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import (
            QGridLayout,
            QLabel,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )

        width, height = surface.get_dimensions()
        widget = QWidget()
        widget.setFixedSize(width, height)
        self._background_label(widget, width, height)

        panel = QWidget(widget)
        panel.setObjectName("legsPanel")
        panel.setGeometry(int(width * 0.16), int(height * 0.10), int(width * 0.68), int(height * 0.80))
        panel.setStyleSheet(
            "QWidget#legsPanel { background: rgba(7, 8, 12, 224); "
            "border: 1px solid rgba(216, 181, 106, 130); border-radius: 14px; color: #eee8df; }"
            "QLabel { background: transparent; border: none; }"
            "QLabel#title { color: #d8b56a; font-size: 30px; font-weight: bold; }"
            "QLabel#subtle { color: #aeb4c1; }"
            "QPushButton { min-height: 44px; padding: 6px 16px; }"
        )

        root = QVBoxLayout(panel)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(10)

        title = QLabel("VELVET'S LEGS")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Hidden owner-maintenance workspace")
        subtitle.setObjectName("subtle")
        subtitle.setAlignment(Qt.AlignCenter)
        root.addWidget(title)
        root.addWidget(subtitle)

        status = QGridLayout()
        status.addWidget(QLabel("Owner"), 0, 0)
        status.addWidget(QLabel("VERIFIED"), 0, 1)
        status.addWidget(QLabel("Maintenance"), 1, 0)
        status.addWidget(QLabel("UNLOCKED"), 1, 1)
        status.addWidget(QLabel("Authority"), 2, 0)
        status.addWidget(QLabel("PRESENTATION ONLY"), 2, 1)
        status.addWidget(QLabel("Physical control"), 3, 0)
        physical = "DISABLED" if self._physical_control_disabled() else "NOT PROVEN DISABLED"
        status.addWidget(QLabel(physical), 3, 1)
        root.addLayout(status)

        note = QLabel(
            "This room is the protected maintenance layer historically described as the Legs. "
            "Surface Studio is the first live tool placed behind this boundary. Learning Mode, "
            "White Room, Dream Layer, and deeper owner tools remain separate reviewed work."
        )
        note.setObjectName("subtle")
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignCenter)
        root.addWidget(note)
        root.addStretch(1)

        studio = QPushButton("Open Surface Studio")
        studio.setEnabled(self._surface_studio_available())
        studio.clicked.connect(self._open_surface_studio)
        back = QPushButton("Back to Backroom")
        back.clicked.connect(self._go_back)
        root.addWidget(studio)
        root.addWidget(back)
        return widget
