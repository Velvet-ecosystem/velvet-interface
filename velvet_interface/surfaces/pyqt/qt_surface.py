# SPDX-License-Identifier: GPL-3.0-only
"""PyQt5 surface implementation for standard and image-first scenes."""

from __future__ import annotations

import logging
from typing import Any, Optional, Tuple

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont, QPixmap
    from PyQt5.QtWidgets import QLabel, QPushButton, QStackedWidget, QWidget

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    PYQT_AVAILABLE = False

from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface

logger = logging.getLogger(__name__)


class QtSurface(Surface):
    """Qt surface with a router-bound image-scene adapter."""

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        widget_provider: Any = None,
        presentation_mode: str = "owner",
        placement_debug: bool = False,
        coordinate_sink: Any = None,
    ) -> None:
        super().__init__("qt")
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is not installed. Install with: pip install PyQt5")
        if width < 1 or height < 1:
            raise ValueError("surface dimensions must be positive")

        self.width = int(width)
        self.height = int(height)
        self.container = None  # type: Optional[QStackedWidget]
        self._scene_widgets = {}  # type: dict[str, QWidget]
        self._router = None
        self.widget_provider = widget_provider
        self.presentation_mode = str(presentation_mode).strip() or "owner"
        self.placement_debug = bool(placement_debug)
        self.coordinate_sink = coordinate_sink

    def initialize(self) -> None:
        self.container = QStackedWidget()
        self.container.setFixedSize(self.width, self.height)
        logger.info("Qt surface initialized (%dx%d)", self.width, self.height)

    def bind_router(self, router: Any) -> None:
        """Bind navigation without giving scenes access to Runtime authority."""

        self._router = router

    def show_scene(self, scene: Scene) -> QWidget:
        if self.container is None:
            raise RuntimeError("Surface not initialized. Call initialize() first.")

        if scene.scene_id in self._scene_widgets:
            widget = self._scene_widgets[scene.scene_id]
        else:
            from velvet_interface.scene_system.image_scene import ImageScene

            if isinstance(scene, ImageScene):
                from velvet_interface.surfaces.pyqt.image_scene_adapter import (
                    QtImageSceneWidget,
                )

                widget = QtImageSceneWidget(
                    scene=scene,
                    surface=self,
                    router=self._router,
                    widget_provider=self.widget_provider,
                    presentation_mode=self.presentation_mode,
                    placement_debug=self.placement_debug,
                    coordinate_sink=self.coordinate_sink,
                )
            else:
                widget = scene.render(self)
            if not isinstance(widget, QWidget):
                raise TypeError("Qt scenes must render QWidget instances")
            self._scene_widgets[scene.scene_id] = widget
            self.container.addWidget(widget)

        self.container.setCurrentWidget(widget)
        logger.debug("Showing scene: %s", scene.scene_id)
        return widget

    def hide_scene(self, scene: Scene) -> None:
        logger.debug("Hiding scene: %s", scene.scene_id)

    def show_text(
        self,
        text: str,
        x: int,
        y: int,
        font_size: int = 14,
        color: Optional[str] = None,
    ) -> QLabel:
        label = QLabel(text)
        label.setFont(QFont("Arial", font_size))
        label.move(x, y)
        if color:
            label.setStyleSheet("color: %s;" % color)
        return label

    def show_button(
        self,
        label: str,
        x: int,
        y: int,
        width: int,
        height: int,
        on_click: Any = None,
    ) -> QPushButton:
        button = QPushButton(label)
        button.setGeometry(x, y, width, height)
        if on_click:
            button.clicked.connect(on_click)
        return button

    def show_image(
        self,
        image_path: str,
        x: int,
        y: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> QLabel:
        label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            if width and height:
                pixmap = pixmap.scaled(
                    width,
                    height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            label.setPixmap(pixmap)
        else:
            logger.warning("Failed to load image: %s", image_path)
        label.move(x, y)
        return label

    def clear(self) -> None:
        if self.container is not None:
            while self.container.count() > 0:
                widget = self.container.widget(0)
                self.container.removeWidget(widget)
                widget.deleteLater()
            self._scene_widgets.clear()
            logger.debug("Surface cleared")

    def get_dimensions(self) -> Tuple[int, int]:
        return (self.width, self.height)

    def get_container(self) -> QStackedWidget:
        if self.container is None:
            raise RuntimeError("Surface not initialized")
        return self.container
