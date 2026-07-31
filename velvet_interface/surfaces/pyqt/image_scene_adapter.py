# SPDX-License-Identifier: GPL-3.0-only
"""PyQt5 renderer for image-first Velvet surfaces."""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping, Optional

try:
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QPixmap
    from PyQt5.QtWidgets import QLabel, QWidget

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]

from velvet_interface.core.surface import Surface
from velvet_interface.scene_system.image_scene import ImageScene

logger = logging.getLogger(__name__)


class QtImageSceneWidget(QWidget):
    """Render one background plus explicit press points and widgets.

    ``widget_provider`` is an explicit registry or callable. A manifest can place
    a widget only when trusted application code has registered that widget ID.
    Missing widgets stay absent and are never replaced with synthetic values.

    ``placement_debug`` draws authoring outlines. ``coordinate_sink`` receives
    normalized click coordinates so a background can be mapped directly on the
    real target display.
    """

    def __init__(
        self,
        scene: ImageScene,
        surface: Surface,
        router: Any = None,
        widget_provider: Any = None,
        presentation_mode: str = "owner",
        placement_debug: bool = False,
        coordinate_sink: Optional[Callable[[str, tuple], None]] = None,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for Qt image scene adapter")
        super().__init__()

        self.scene = scene
        self.surface = surface
        self.router = router
        self.widget_provider = widget_provider
        self.presentation_mode = str(presentation_mode).strip() or "owner"
        self.placement_debug = bool(placement_debug)
        self.coordinate_sink = coordinate_sink
        self._placed_widgets = []

        target_width, target_height = surface.get_dimensions()
        scene.setup_scaling((target_width, target_height))
        self.setFixedSize(target_width, target_height)
        self.setMouseTracking(True)

        self.background_label = QLabel(self)
        self.background_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.background_label.setAlignment(Qt.AlignCenter)
        self.background_label.setTextFormat(Qt.PlainText)
        self._load_background()
        self._place_widgets()
        logger.debug("Qt image surface created for %s", scene.scene_id)

    def _load_background(self) -> None:
        if self.scene.scaler is None:
            raise RuntimeError("scene transform has not been configured")
        x, y, width, height = self.scene.scaler.get_letterbox_rect()
        self.background_label.setGeometry(x, y, width, height)

        if not self.scene.background_path:
            self._show_background_error("Background not configured")
            return
        pixmap = QPixmap(str(self.scene.background_path))
        if pixmap.isNull():
            logger.warning("Failed to load background: %s", self.scene.background_path)
            self._show_background_error("Background unavailable")
            return

        scaled = pixmap.scaled(
            width,
            height,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation,
        )
        self.background_label.setPixmap(scaled)
        self.background_label.setToolTip(self.scene.background_alt_text)
        self.background_label.lower()
        logger.debug("Background loaded: %s", self.scene.background_path)

    def _show_background_error(self, message: str) -> None:
        self.background_label.setPixmap(QPixmap())
        self.background_label.setText(message)
        self.background_label.setFont(QFont("Sans Serif", 12))
        self.background_label.setStyleSheet(
            "background: #07080c; color: #8d93a3; border: 1px solid #2b2e39;"
        )

    def _place_widgets(self) -> None:
        for placement in self.scene.widget_placements:
            visible_in = placement.get("visible_in", ())
            if visible_in and self.presentation_mode not in visible_in:
                continue
            widget_id = str(placement["widget_id"])
            widget = self._resolve_widget(widget_id)
            if widget is None:
                logger.info("Widget not registered for surface: %s", widget_id)
                continue

            x, y, width, height = self.scene.widget_rect(placement)
            if hasattr(widget, "render") and not isinstance(widget, QWidget):
                widget = widget.render(self.surface, x, y)
            if not isinstance(widget, QWidget):
                raise TypeError(
                    "widget provider must return QWidget or a Widget rendering to QWidget"
                )
            widget.setParent(self)
            widget.setGeometry(x, y, width, height)
            widget.setProperty("velvet_widget_id", widget_id)
            widget.show()
            widget.raise_()
            self._placed_widgets.append(widget)

    def _resolve_widget(self, widget_id: str) -> Any:
        provider = self.widget_provider
        if provider is None:
            return None
        if isinstance(provider, Mapping):
            candidate = provider.get(widget_id)
        elif callable(provider):
            candidate = provider(widget_id)
        else:
            raise TypeError("widget_provider must be a mapping or callable")
        if callable(candidate) and not isinstance(candidate, QWidget):
            try:
                return candidate()
            except TypeError:
                return candidate
        return candidate

    def mousePressEvent(self, event: Any) -> None:
        x = float(event.x())
        y = float(event.y())
        normalized = self.scene.normalized_point(x, y)
        if normalized is not None and self.coordinate_sink is not None:
            self.coordinate_sink(self.scene.scene_id, normalized)

        action = self.scene.handle_click(x, y)
        if action:
            self._handle_action(action)
        super().mousePressEvent(event)

    def _handle_action(self, action: str) -> None:
        if action.startswith("navigate:"):
            target_scene = action.split(":", 1)[1]
            if self.router is not None:
                logger.info("Navigating to: %s", target_scene)
                self.router.navigate(target_scene)
            else:
                logger.warning("No router available for navigation: %s", target_scene)
        elif action.startswith("emit:"):
            event_name = action.split(":", 1)[1]
            self.scene.handle_event(
                event_name,
                {
                    "source": "surface_press_point",
                    "scene_id": self.scene.scene_id,
                    "read_only": True,
                    "actuation_granted": False,
                    "actuation_performed": False,
                },
            )
        else:
            logger.warning("Rejected unsupported surface action: %s", action)

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        if self.placement_debug:
            self._draw_placement_overlay()

    def _draw_placement_overlay(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        region_pen = QPen(QColor(255, 90, 90, 210))
        region_pen.setWidth(2)
        painter.setPen(region_pen)
        for region in self.scene.region_manager.regions:
            points = [
                QPoint(int(round(x)), int(round(y)))
                for x, y in self.scene.scaled_region_polygon(region)
            ]
            for index, point in enumerate(points):
                painter.drawLine(point, points[(index + 1) % len(points)])
            if points:
                painter.drawText(points[0] + QPoint(5, -5), region.name)

        widget_pen = QPen(QColor(90, 190, 255, 210))
        widget_pen.setWidth(2)
        painter.setPen(widget_pen)
        for placement in self.scene.widget_placements:
            x, y, width, height = self.scene.widget_rect(placement)
            painter.drawRect(x, y, width, height)
            painter.drawText(x + 5, y + 16, str(placement["widget_id"]))
        painter.end()
