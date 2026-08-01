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
    editing, promotion, or physical authority.
    """

    def __init__(
        self,
        workspace: SurfaceWorkspace,
        maintenance_access_provider: Any,
        promotion_context_provider: Any,
        on_promoted: Any = None,
        scene_id: str = "surface_studio",
    ) -> None:
        super().__init__(scene_id)
        self.workspace = workspace
        self.maintenance_access_provider = maintenance_access_provider
        self.promotion_context_provider = promotion_context_provider
        self.on_promoted = on_promoted
        self._router = None
        self._widget = None

    def bind_router(self, router: Any) -> None:
        self._router = router

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        self._active = True
        if self._widget is not None:
            self._widget.set_maintenance_access(self._maintenance_access())
            self._widget.refresh_drafts()

    def on_exit(self) -> None:
        self._active = False

    def render(self, surface: Any) -> Any:
        from velvet_interface.surfaces.pyqt.surface_studio_widget import (
            QtSurfaceStudioWidget,
        )

        width, height = surface.get_dimensions()
        self._widget = QtSurfaceStudioWidget(
            workspace=self.workspace,
            target_size=(width, height),
            maintenance_access=self._maintenance_access(),
            promotion_context_provider=self.promotion_context_provider,
            on_promoted=self.on_promoted,
            on_back=self._go_back,
        )
        return self._widget

    def _maintenance_access(self) -> bool:
        try:
            return bool(self.maintenance_access_provider())
        except Exception:
            return False

    def _go_back(self) -> bool:
        if self._router is None:
            return False
        return bool(self._router.back())
