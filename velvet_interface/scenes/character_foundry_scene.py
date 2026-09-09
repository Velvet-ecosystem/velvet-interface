# SPDX-License-Identifier: GPL-3.0-only
"""Trusted built-in scene boundary for the Character Foundry.

This scene is registered by application code, never dynamically imported from a
surface manifest. It owns presentation access and navigation only. Candidate
semantics remain in Persona Continuity through ``FoundryBridge``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from velvet_interface.core.scene import Scene
from velvet_interface.foundry_bridge import FoundryBridge, FoundryUnavailable


class CharacterFoundryScene(Scene):
    """Protected full-screen entrance for the Character Foundry.

    The initial scene intentionally provides only a readiness shell. The final
    structured editor is a separate Interface change so placement and visual
    design can be reviewed without changing the backend boundary again.
    """

    def __init__(
        self,
        bridge: FoundryBridge,
        access_provider: Any,
        scene_id: str = "character_foundry",
    ) -> None:
        super().__init__(scene_id)
        self.bridge = bridge
        self.access_provider = access_provider
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
            self._widget = self._render_message(
                surface,
                "CHARACTER FOUNDRY LOCKED",
                "Open this workshop with verified owner presence or protected maintenance access.",
            )
            return self._widget

        try:
            draft_count = len(self.bridge.list_candidates())
        except (FoundryUnavailable, FileNotFoundError, TypeError, ValueError, OSError) as exc:
            self._widget = self._render_message(
                surface,
                "CHARACTER FOUNDRY UNAVAILABLE",
                str(exc),
            )
            return self._widget

        self._widget = self._render_message(
            surface,
            "CHARACTER FOUNDRY READY",
            "%d local draft%s available. The structured workshop surface is ready for UI design."
            % (draft_count, "" if draft_count == 1 else "s"),
        )
        return self._widget

    def _has_access(self) -> bool:
        try:
            return bool(self.access_provider())
        except Exception:
            return False

    def _render_message(self, surface: Any, title_text: str, message_text: str) -> Any:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

        width, height = surface.get_dimensions()
        widget = QWidget()
        widget.setFixedSize(width, height)
        widget.setObjectName("characterFoundryShell")
        widget.setStyleSheet(
            "QWidget#characterFoundryShell { background: #08090d; color: #eee8df; }"
            "QLabel#foundryTitle { color: #d8b56a; font-size: 30px; }"
            "QLabel#foundryMessage { font-size: 16px; }"
            "QPushButton { min-width: 180px; min-height: 42px; }"
        )
        layout = QVBoxLayout(widget)
        layout.addStretch(1)
        title = QLabel(title_text)
        title.setObjectName("foundryTitle")
        title.setAlignment(Qt.AlignCenter)
        message = QLabel(message_text)
        message.setObjectName("foundryMessage")
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
