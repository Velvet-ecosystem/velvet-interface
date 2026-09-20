# SPDX-License-Identifier: GPL-3.0-only
"""Trusted presentation-only scene for Eleanor Engineering."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from velvet_interface.core.scene import Scene
from velvet_interface.eleanor_bridge import EleanorBridge

class EleanorEngineeringScene(Scene):
    def __init__(self, bridge: EleanorBridge, background_path: Optional[Path] = None, scene_id: str = "eleanor_engineering") -> None:
        super().__init__(scene_id)
        self.bridge = bridge
        self.background_path = Path(background_path or "examples/assets/workspace_scroll.png")
        self._router = None
        self._widget = None

    def bind_router(self, router: Any) -> None:
        self._router = router

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        self._active = True
        if self._widget is not None:
            self._widget.refresh()

    def on_exit(self) -> None:
        self._active = False

    def render(self, surface: Any) -> Any:
        from velvet_interface.surfaces.pyqt.eleanor_engineering_widget import QtEleanorEngineeringWidget
        width, height = surface.get_dimensions()
        self._widget = QtEleanorEngineeringWidget(
            bridge=self.bridge, target_size=(width, height),
            background_path=self.background_path, on_back=self._go_back,
        )
        return self._widget

    def _go_back(self) -> bool:
        return bool(self._router and self._router.back())
