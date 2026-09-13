# SPDX-License-Identifier: GPL-3.0-only
"""Trusted built-in scene boundary for Velour's read-only Library Reader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from velvet_interface.core.scene import Scene
from velvet_interface.library_preview import LocalLibraryPreviewProvider


class LibraryReaderScene(Scene):
    """Read-only full-screen library workspace using the reusable scroll asset."""

    def __init__(
        self,
        provider: LocalLibraryPreviewProvider,
        access_provider: Any,
        background_path: Optional[Path] = None,
        scene_id: str = "library_reader",
    ) -> None:
        super().__init__(scene_id)
        self.provider = provider
        self.access_provider = access_provider
        self.background_path = Path(background_path or "examples/assets/workspace_scroll.png")
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
        if access and self._widget is not None:
            refresh = getattr(self._widget, "refresh_items", None)
            if callable(refresh):
                refresh()

    def on_exit(self) -> None:
        self._active = False

    def render(self, surface: Any) -> Any:
        self._surface = surface
        access = self._has_access()
        self._rendered_access = access
        if not access:
            self._widget = self._render_locked(surface)
            return self._widget

        from velvet_interface.surfaces.pyqt.library_reader_widget import QtLibraryReaderWidget

        width, height = surface.get_dimensions()
        self._widget = QtLibraryReaderWidget(
            provider=self.provider,
            target_size=(width, height),
            background_path=self.background_path,
            on_back=self._go_back,
        )
        return self._widget

    def _has_access(self) -> bool:
        try:
            return bool(self.access_provider())
        except Exception:
            return False

    def _render_locked(self, surface: Any) -> Any:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

        width, height = surface.get_dimensions()
        widget = QWidget()
        widget.setFixedSize(width, height)
        widget.setObjectName("libraryReaderLocked")
        widget.setStyleSheet(
            "QWidget#libraryReaderLocked { background: #08090d; color: #eee8df; }"
            "QLabel#libraryReaderTitle { color: #d8b56a; font-size: 30px; }"
            "QPushButton { min-width: 180px; min-height: 42px; }"
        )
        layout = QVBoxLayout(widget)
        layout.addStretch(1)
        title = QLabel("VELOUR'S LIBRARY LOCKED")
        title.setObjectName("libraryReaderTitle")
        title.setAlignment(Qt.AlignCenter)
        message = QLabel(
            "Open the archive with verified owner presence or protected maintenance access.\n"
            "Library content was not changed."
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

    def _go_back(self) -> bool:
        if self._router is None:
            return False
        return bool(self._router.back())
