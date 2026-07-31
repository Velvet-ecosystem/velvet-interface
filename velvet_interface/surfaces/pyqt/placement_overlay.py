# SPDX-License-Identifier: GPL-3.0-only
"""Transparent authoring overlay for Qt image surfaces."""

from __future__ import annotations

try:
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtGui import QColor, QPainter, QPen
    from PyQt5.QtWidgets import QWidget

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]


class QtPlacementOverlay(QWidget):
    """Draw press-point polygons and widget anchors above a background image."""

    def __init__(self, scene, parent) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for placement overlay")
        super().__init__(parent)
        self.scene = scene
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setGeometry(parent.rect())
        self.show()
        self.raise_()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        region_pen = QPen(QColor(255, 90, 90, 220))
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

        widget_pen = QPen(QColor(90, 190, 255, 220))
        widget_pen.setWidth(2)
        painter.setPen(widget_pen)
        for placement in self.scene.widget_placements:
            x, y, width, height = self.scene.widget_rect(placement)
            painter.drawRect(x, y, width, height)
            painter.drawText(x + 5, y + 16, str(placement["widget_id"]))
        painter.end()
