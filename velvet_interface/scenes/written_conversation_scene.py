# SPDX-License-Identifier: GPL-3.0-only
"""Trusted built-in scene for Velvet's local written conversation surface."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from velvet_interface.core.scene import Scene


class WrittenConversationScene(Scene):
    """Protected text surface with an injected, authority-free turn submitter.

    The scene knows nothing about Core, body-state storage, Court, or executors.
    Application code supplies a narrow callable that returns the already-final
    conversation reply mapping.
    """

    def __init__(
        self,
        *,
        submit_turn: Any,
        access_provider: Any,
        scene_id: str = "written_conversation",
    ) -> None:
        super().__init__(scene_id)
        if not callable(submit_turn):
            raise TypeError("submit_turn must be callable")
        if not callable(access_provider):
            raise TypeError("access_provider must be callable")
        self.submit_turn = submit_turn
        self.access_provider = access_provider
        self._router = None
        self._surface = None
        self._widget = None
        self._rendered_access = None  # type: Optional[bool]

    def bind_router(self, router: Any) -> None:
        self._router = router

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        self._active = True
        access = self._access_allowed()
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
            focus = getattr(self._widget, "focus_input", None)
            if callable(focus):
                focus()

    def on_exit(self) -> None:
        self._active = False

    def render(self, surface: Any) -> Any:
        self._surface = surface
        access = self._access_allowed()
        self._rendered_access = access
        if not access:
            self._widget = self._render_locked(surface)
            return self._widget

        from velvet_interface.surfaces.pyqt.written_conversation_widget import (
            QtWrittenConversationWidget,
        )

        width, height = surface.get_dimensions()
        self._widget = QtWrittenConversationWidget(
            submit_turn=self._submit_bounded,
            target_size=(width, height),
            on_back=self._go_back,
        )
        return self._widget

    def _submit_bounded(self, text: str) -> Mapping[str, Any]:
        if not self._access_allowed():
            raise PermissionError("written conversation access is no longer available")
        result = self.submit_turn(text)
        if not isinstance(result, Mapping):
            raise TypeError("written conversation submitter must return a mapping")
        return result

    def _access_allowed(self) -> bool:
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
        widget.setStyleSheet(
            "QWidget { background: #09090d; color: #eee8df; }"
            "QLabel#title { color: #d8b56a; font-size: 28px; }"
            "QPushButton { min-width: 180px; min-height: 42px; }"
        )
        layout = QVBoxLayout(widget)
        layout.addStretch(1)
        title = QLabel("WRITTEN CONVERSATION LOCKED")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        message = QLabel(
            "This local conversation surface requires verified owner or maintenance access.\n"
            "No conversation turn was submitted."
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
