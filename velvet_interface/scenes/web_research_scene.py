# SPDX-License-Identifier: GPL-3.0-only
"""Trusted built-in scene boundary for Velour's controlled research desk."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from velvet_interface.core.scene import Scene
from velvet_interface.web_research import DocumentProvider, SearchProvider


class WebResearchScene(Scene):
    """Presentation-only research shell using the reusable scroll artwork."""

    def __init__(
        self,
        *,
        search_provider: Optional[SearchProvider] = None,
        document_provider: Optional[DocumentProvider] = None,
        background_path: Optional[Path] = None,
        scene_id: str = "velour_web_research",
    ) -> None:
        super().__init__(scene_id)
        self.search_provider = search_provider
        self.document_provider = document_provider
        self.background_path = Path(background_path or "examples/assets/workspace_scroll.png")
        self._router = None
        self._widget = None

    def bind_router(self, router: Any) -> None:
        self._router = router

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        self._active = True

    def on_exit(self) -> None:
        self._active = False

    def render(self, surface: Any) -> Any:
        from velvet_interface.surfaces.pyqt.web_research_widget import QtWebResearchWidget

        width, height = surface.get_dimensions()
        self._widget = QtWebResearchWidget(
            target_size=(width, height),
            background_path=self.background_path,
            on_back=self._go_back,
            search_provider=self.search_provider,
            document_provider=self.document_provider,
        )
        return self._widget

    def _go_back(self) -> bool:
        if self._router is None:
            return False
        return bool(self._router.back())
