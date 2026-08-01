# SPDX-License-Identifier: GPL-3.0-only
"""Trusted built-in scene for the on-device Velvet Surface Studio."""

from __future__ import annotations

from typing import Any, Dict, Optional

from velvet_interface.core.scene import Scene
from velvet_interface.scene_system.surface_workspace import SurfaceWorkspace


class SurfaceStudioScene(Scene):
    """Maintenance-only scene that hosts the trusted Surface Studio widget.

    This scene is registered by application code. It is never dynamically
    imported from a surface manifest, and its presence does not itself unlock
    editing, promotion, camera access, or physical authority.
    """

    def __init__(
        self,
        workspace: SurfaceWorkspace,
        maintenance_access_provider: Any,
        promotion_context_provider: Any,
        camera_frame_provider: Any = None,
        on_promoted: Any = None,
        scene_id: str = "surface_studio",
    ) -> None:
        super().__init__(scene_id)
        self.workspace = workspace
        self.maintenance_access_provider = maintenance_access_provider
        self.promotion_context_provider = promotion_context_provider
        self.camera_frame_provider = camera_frame_provider
        self.on_promoted = on_promoted
        self._router = None
        self._surface = None
        self._widget = None
        self._rendered_access = None  # type: Optional[bool]

    def bind_router(self, router: Any) -> None:
        self._router = router

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        self._active = True
        access = self._maintenance_access()
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
            refresh = getattr(self._widget, "refresh_drafts", None)
            if callable(refresh):
                refresh()

    def on_exit(self) -> None:
        self._active = False

    def render(self, surface: Any) -> Any:
        self._surface = surface
        access = self._maintenance_access()
        self._rendered_access = access
        if not access:
            self._widget = self._render_locked(surface)
            return self._widget

        from velvet_interface.surfaces.pyqt.surface_studio_widget import (
            QtSurfaceStudioWidget,
        )

        width, height = surface.get_dimensions()
        self._widget = QtSurfaceStudioWidget(
            workspace=self.workspace,
            target_size=(width, height),
            promotion_context_provider=self.promotion_context_provider,
            camera_frame_provider=self.camera_frame_provider,
            on_promoted=self.on_promoted,
            on_back=self._go_back,
        )
        return self._widget

    def _render_locked(self, surface: Any) -> Any:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

        width, height = surface.get_dimensions()
        widget = QWidget()
        widget.setFixedSize(width, height)
        widget.setStyleSheet(
            "QWidget { background: #07080c; color: #eee8df; }"
            "QLabel#title { color: #d8b56a; font-size: 28px; }"
            "QPushButton { min-width: 180px; min-height: 42px; }"
        )
        layout = QVBoxLayout(widget)
        layout.addStretch(1)
        title = QLabel("SURFACE STUDIO LOCKED")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        message = QLabel(
            "Open this workshop through Velvet's protected Maintenance entrance.\n"
            "No draft files or active surfaces were changed."
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

    def _maintenance_access(self) -> bool:
        try:
            return bool(self.maintenance_access_provider())
        except Exception:
            return False

    def _go_back(self) -> bool:
        if self._router is None:
            return False
        return bool(self._router.back())
