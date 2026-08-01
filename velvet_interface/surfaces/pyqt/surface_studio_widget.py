# SPDX-License-Identifier: GPL-3.0-only
"""On-device PyQt Surface Studio for Velvet maintenance mode."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

try:
    from PyQt5.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QRect, Qt
    from PyQt5.QtGui import QColor, QFont, QKeySequence, QPainter, QPen, QPixmap
    from PyQt5.QtWidgets import (
        QComboBox,
        QColorDialog,
        QFileDialog,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore

from velvet_interface.scene_system.authoring import SurfaceLayoutAuthoringSession
from velvet_interface.scene_system.surface_workspace import (
    SurfacePromotionContext,
    SurfacePromotionResult,
    SurfaceWorkspace,
)


PromotionContextProvider = Callable[[], SurfacePromotionContext]
PromotionCallback = Callable[[SurfacePromotionResult], None]
BackCallback = Callable[[], Any]


class QtSurfaceStudioWidget(QWidget):
    """A bounded full-screen editor for artwork, presses, and widgets.

    The editor writes only to ``SurfaceWorkspace`` drafts until the Promote
    button passes the separate maintenance/owner/stationary/control-disabled
    evidence gate.
    """

    MODES = (
        ("Inspect", "inspect"),
        ("Press Point", "press"),
        ("Widget", "widget"),
        ("Background Panel", "panel"),
        ("Background Text", "text"),
    )

    def __init__(
        self,
        workspace: SurfaceWorkspace,
        target_size: Tuple[int, int],
        promotion_context_provider: PromotionContextProvider,
        on_promoted: Optional[PromotionCallback] = None,
        on_back: Optional[BackCallback] = None,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is required for Surface Studio")
        super().__init__()
        self.workspace = workspace
        self.target_size = target_size
        self.promotion_context_provider = promotion_context_provider
        self.on_promoted = on_promoted
        self.on_back = on_back
        self.session = None  # type: Optional[SurfaceLayoutAuthoringSession]

        self.setObjectName("surfaceStudio")
        self.setFixedSize(*target_size)
        self.setStyleSheet(
            "QWidget#surfaceStudio { background: #08090d; color: #eee8df; }"
            "QPushButton, QComboBox { min-height: 34px; padding: 3px 10px; }"
            "QLabel#studioStatus { color: #d8b56a; padding: 4px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        first_row = QHBoxLayout()
        self.draft_selector = QComboBox()
        self.open_button = QPushButton("Open Draft")
        self.import_button = QPushButton("New From Image")
        self.blank_button = QPushButton("New Blank")
        self.save_button = QPushButton("Save Draft")
        self.promote_button = QPushButton("Promote Live")
        self.back_button = QPushButton("Back")
        for widget in (
            QLabel("Surface:"),
            self.draft_selector,
            self.open_button,
            self.import_button,
            self.blank_button,
            self.save_button,
            self.promote_button,
            self.back_button,
        ):
            first_row.addWidget(widget)
        first_row.addStretch(1)
        root.addLayout(first_row)

        second_row = QHBoxLayout()
        self.mode_selector = QComboBox()
        for label, value in self.MODES:
            self.mode_selector.addItem(label, value)
        self.remove_press_button = QPushButton("Remove Press")
        self.remove_widget_button = QPushButton("Remove Widget")
        self.toggle_overlay_button = QPushButton("Hide Guides")
        self.status_label = QLabel("Create or open a draft")
        self.status_label.setObjectName("studioStatus")
        for widget in (
            QLabel("Tool:"),
            self.mode_selector,
            self.remove_press_button,
            self.remove_widget_button,
            self.toggle_overlay_button,
            self.status_label,
        ):
            second_row.addWidget(widget)
        second_row.addStretch(1)
        root.addLayout(second_row)

        canvas_height = max(240, target_size[1] - 104)
        self.canvas = _SurfaceStudioCanvas(
            studio=self,
            target_size=(target_size[0] - 16, canvas_height),
        )
        root.addWidget(self.canvas)

        self.open_button.clicked.connect(self.open_selected_draft)
        self.import_button.clicked.connect(self.new_from_image)
        self.blank_button.clicked.connect(self.new_blank)
        self.save_button.clicked.connect(self.save_draft)
        self.promote_button.clicked.connect(self.promote_live)
        self.back_button.clicked.connect(self._go_back)
        self.mode_selector.currentIndexChanged.connect(self._mode_changed)
        self.remove_press_button.clicked.connect(self.remove_press)
        self.remove_widget_button.clicked.connect(self.remove_widget)
        self.toggle_overlay_button.clicked.connect(self.toggle_guides)

        self.refresh_drafts()
        self._set_controls_enabled(False)

    def refresh_drafts(self, select_name: Optional[str] = None) -> None:
        current = select_name or self.draft_selector.currentText()
        self.draft_selector.blockSignals(True)
        self.draft_selector.clear()
        self.draft_selector.addItems(list(self.workspace.list_drafts()))
        if current:
            index = self.draft_selector.findText(current)
            if index >= 0:
                self.draft_selector.setCurrentIndex(index)
        self.draft_selector.blockSignals(False)

    def open_selected_draft(self) -> None:
        name = self.draft_selector.currentText().strip()
        if not name:
            self._status("No saved draft selected")
            return
        try:
            self._set_session(self.workspace.load_draft(name))
            self._status("Opened draft %s" % name)
        except (OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Draft unavailable", str(exc))

    def new_from_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choose surface artwork",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg)",
        )
        if not filename:
            return
        name = self._ask_surface_name()
        if not name:
            return
        probe = QPixmap(filename)
        if probe.isNull():
            QMessageBox.warning(self, "Artwork rejected", "The selected image cannot be decoded.")
            return
        try:
            managed = self.workspace.import_background(Path(filename), name)
            session = self.workspace.create_session(
                name,
                managed,
                (probe.width(), probe.height()),
                fit_mode="cover",
            )
            self._set_session(session)
            self.save_draft()
            self._status("Imported artwork for %s" % name)
        except (OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Artwork rejected", str(exc))

    def new_blank(self) -> None:
        name = self._ask_surface_name()
        if not name:
            return
        width, accepted = QInputDialog.getInt(
            self, "Background width", "Width:", 1280, 320, 8192, 1
        )
        if not accepted:
            return
        height, accepted = QInputDialog.getInt(
            self, "Background height", "Height:", 720, 240, 8192, 1
        )
        if not accepted:
            return
        color = QColorDialog.getColor(QColor("#07080c"), self, "Background colour")
        if not color.isValid():
            return
        pixmap = QPixmap(width, height)
        pixmap.fill(color)
        try:
            managed = self.workspace.create_blank_background(name, _pixmap_png_bytes(pixmap))
            session = self.workspace.create_session(
                name,
                managed,
                (width, height),
                fit_mode="cover",
            )
            self._set_session(session)
            self.save_draft()
            self._status("Created blank background for %s" % name)
        except (OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Background rejected", str(exc))

    def save_draft(self) -> None:
        if self.session is None:
            return
        try:
            path = self.workspace.save_draft(self.session)
            self.refresh_drafts(self.session.name)
            self._status("Saved %s" % path.name)
        except (OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Draft not saved", str(exc))

    def promote_live(self) -> None:
        if self.session is None:
            return
        self.save_draft()
        answer = QMessageBox.question(
            self,
            "Promote active surface",
            "Replace the active '%s' surface with this validated draft?\n\n"
            "Promotion requires maintenance unlock, owner presence, a stationary "
            "vehicle, and physical control disabled." % self.session.name,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            context = self.promotion_context_provider()
            result = self.workspace.promote(self.session.name, context)
        except (OSError, PermissionError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Promotion blocked", str(exc))
            self._status("Promotion blocked")
            return
        self._status("Promoted %s with receipt %s" % (result.surface_name, result.receipt_id))
        if self.on_promoted is not None:
            self.on_promoted(result)

    def remove_press(self) -> None:
        if self.session is None or not self.session.press_points:
            return
        values = [item.point_id for item in self.session.press_points]
        value, accepted = QInputDialog.getItem(
            self, "Remove press point", "Press point:", values, 0, False
        )
        if accepted and value:
            self.session.remove_press_point(str(value))
            self.canvas.update()
            self._status("Removed press point %s" % value)

    def remove_widget(self) -> None:
        if self.session is None or not self.session.widgets:
            return
        values = [item.widget_id for item in self.session.widgets]
        value, accepted = QInputDialog.getItem(
            self, "Remove widget", "Widget:", values, 0, False
        )
        if accepted and value:
            self.session.remove_widget(str(value))
            self.canvas.update()
            self._status("Removed widget %s" % value)

    def toggle_guides(self) -> None:
        self.canvas.guides_visible = not self.canvas.guides_visible
        self.toggle_overlay_button.setText(
            "Hide Guides" if self.canvas.guides_visible else "Show Guides"
        )
        self.canvas.update()

    def commit_press_point(self) -> None:
        if self.session is None:
            return
        if len(self.canvas.draft_points) < 3:
            QMessageBox.information(self, "Press point", "Add at least three vertices.")
            return
        point_id, accepted = QInputDialog.getText(
            self, "Press point", "Press point ID:"
        )
        if not accepted or not point_id.strip():
            return
        action, accepted = QInputDialog.getText(
            self,
            "Press action",
            "Action, navigate:<scene> or emit:<event>:",
            text="navigate:",
        )
        if not accepted:
            return
        try:
            self.session.add_press_point_from_target(
                point_id.strip(),
                action.strip(),
                self.canvas.draft_points,
                self.canvas.target_size,
                accessibility_label=point_id.strip().replace("_", " "),
            )
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Press point rejected", str(exc))
            return
        self.canvas.draft_points = []
        self.canvas.update()
        self._status("Placed press point %s" % point_id.strip())

    def commit_widget(self, rect: Tuple[float, float, float, float]) -> None:
        if self.session is None:
            return
        widget_id, accepted = QInputDialog.getText(
            self, "Widget placement", "Registered widget ID:"
        )
        if not accepted or not widget_id.strip():
            return
        try:
            self.session.add_widget_from_target(
                widget_id.strip(), rect, self.canvas.target_size
            )
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Widget rejected", str(exc))
            return
        self.canvas.update()
        self._status("Placed widget %s" % widget_id.strip())

    def commit_panel(self, rect: Tuple[float, float, float, float]) -> None:
        if self.session is None:
            return
        colour = QColorDialog.getColor(QColor(20, 22, 30, 190), self, "Panel colour")
        if not colour.isValid():
            return
        alpha, accepted = QInputDialog.getInt(
            self, "Panel opacity", "Opacity 0-255:", 190, 0, 255, 1
        )
        if not accepted:
            return
        colour.setAlpha(alpha)
        self._paint_background_rect(rect, colour)

    def commit_text(self, target_point: Tuple[float, float]) -> None:
        if self.session is None:
            return
        text, accepted = QInputDialog.getText(self, "Background text", "Text:")
        if not accepted or not text:
            return
        size, accepted = QInputDialog.getInt(
            self, "Text size", "Font size:", 32, 8, 240, 1
        )
        if not accepted:
            return
        colour = QColorDialog.getColor(QColor("#f2ede4"), self, "Text colour")
        if not colour.isValid():
            return
        self._paint_background_text(target_point, text, size, colour)

    def _paint_background_rect(
        self,
        target_rect: Tuple[float, float, float, float],
        colour: QColor,
    ) -> None:
        if self.session is None:
            return
        transform = self.session.scaler(self.canvas.target_size)
        x, y, width, height = target_rect
        first = transform.unscale_point(x, y)
        second = transform.unscale_point(x + width, y + height)
        pixmap = QPixmap(self.session.background_path)
        painter = QPainter(pixmap)
        painter.fillRect(
            QRect(
                int(round(first[0])),
                int(round(first[1])),
                max(1, int(round(second[0] - first[0]))),
                max(1, int(round(second[1] - first[1]))),
            ),
            colour,
        )
        painter.end()
        self._replace_background_pixmap(pixmap, "Painted background panel")

    def _paint_background_text(
        self,
        target_point: Tuple[float, float],
        text: str,
        size: int,
        colour: QColor,
    ) -> None:
        if self.session is None:
            return
        transform = self.session.scaler(self.canvas.target_size)
        base_x, base_y = transform.unscale_point(*target_point)
        pixmap = QPixmap(self.session.background_path)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(colour)
        painter.setFont(QFont("Sans Serif", size))
        painter.drawText(QPoint(int(round(base_x)), int(round(base_y))), text)
        painter.end()
        self._replace_background_pixmap(pixmap, "Painted background text")

    def _replace_background_pixmap(self, pixmap: QPixmap, status: str) -> None:
        if self.session is None:
            return
        try:
            managed = self.workspace.create_blank_background(
                self.session.name, _pixmap_png_bytes(pixmap)
            )
        except (OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Background not saved", str(exc))
            return
        self.session.background_path = str(managed)
        self.canvas.set_session(self.session)
        self._status(status)

    def _set_session(self, session: SurfaceLayoutAuthoringSession) -> None:
        self.session = session
        self.canvas.set_session(session)
        self._set_controls_enabled(True)
        self.refresh_drafts(session.name)
        self._status(
            "%s | %d presses | %d widgets"
            % (session.name, len(session.press_points), len(session.widgets))
        )

    def _set_controls_enabled(self, enabled: bool) -> None:
        for widget in (
            self.save_button,
            self.promote_button,
            self.mode_selector,
            self.remove_press_button,
            self.remove_widget_button,
            self.toggle_overlay_button,
        ):
            widget.setEnabled(enabled)

    def _mode_changed(self) -> None:
        self.canvas.mode = str(self.mode_selector.currentData())
        self.canvas.draft_points = []
        self.canvas.drag_start = None
        self.canvas.drag_current = None
        self.canvas.update()
        self._status("Tool: %s" % self.mode_selector.currentText())

    def _ask_surface_name(self) -> Optional[str]:
        value, accepted = QInputDialog.getText(
            self, "Surface name", "Lowercase surface name:"
        )
        if not accepted or not value.strip():
            return None
        return value.strip()

    def _status(self, text: str) -> None:
        self.status_label.setText(text)

    def _go_back(self) -> None:
        if self.on_back is not None:
            self.on_back()

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.Save):
            self.save_draft()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.canvas.mode == "press":
                self.commit_press_point()
                return
        if event.key() == Qt.Key_Escape:
            self.canvas.draft_points = []
            self.canvas.drag_start = None
            self.canvas.drag_current = None
            self.canvas.update()
            self._status("Unfinished shape cleared")
            return
        super().keyPressEvent(event)


class _SurfaceStudioCanvas(QWidget):
    def __init__(
        self,
        studio: QtSurfaceStudioWidget,
        target_size: Tuple[int, int],
    ) -> None:
        super().__init__(studio)
        self.studio = studio
        self.target_size = target_size
        self.session = None  # type: Optional[SurfaceLayoutAuthoringSession]
        self.background = QPixmap()
        self.mode = "inspect"
        self.guides_visible = True
        self.draft_points = []  # type: List[Tuple[float, float]]
        self.drag_start = None  # type: Optional[Tuple[float, float]]
        self.drag_current = None  # type: Optional[Tuple[float, float]]
        self.setFixedSize(*target_size)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

    def set_session(self, session: SurfaceLayoutAuthoringSession) -> None:
        self.session = session
        self.background = QPixmap(session.background_path)
        self.draft_points = []
        self.drag_start = None
        self.drag_current = None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#040509"))
        if self.session is None or self.background.isNull():
            painter.setPen(QColor("#8d93a3"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Open or create a surface draft")
            painter.end()
            return

        transform = self.session.scaler(self.target_size)
        image_x, image_y, image_width, image_height = transform.get_letterbox_rect()
        scaled = self.background.scaled(
            image_width,
            image_height,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation,
        )
        painter.drawPixmap(image_x, image_y, scaled)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.guides_visible:
            self._draw_existing_guides(painter, transform)
        self._draw_draft(painter)
        painter.end()

    def _draw_existing_guides(self, painter: QPainter, transform: Any) -> None:
        if self.session is None:
            return
        press_pen = QPen(QColor(255, 90, 90, 220))
        press_pen.setWidth(2)
        painter.setPen(press_pen)
        for press in self.session.press_points:
            points = []
            for base_x, base_y in press.base_polygon(self.session.base_resolution):
                x, y = transform.scale_point(base_x, base_y)
                points.append(QPoint(int(round(x)), int(round(y))))
            _draw_polygon(painter, points)
            if points:
                painter.drawText(points[0] + QPoint(5, -5), press.point_id)

        widget_pen = QPen(QColor(90, 190, 255, 220))
        widget_pen.setWidth(2)
        painter.setPen(widget_pen)
        for widget in self.session.widgets:
            rect = transform.scale_rect(*widget.base_rect(self.session.base_resolution))
            painter.drawRect(*rect)
            painter.drawText(rect[0] + 5, rect[1] + 16, widget.widget_id)

    def _draw_draft(self, painter: QPainter) -> None:
        draft_pen = QPen(QColor(255, 215, 90, 240))
        draft_pen.setWidth(3)
        painter.setPen(draft_pen)
        points = [QPoint(int(x), int(y)) for x, y in self.draft_points]
        for index in range(1, len(points)):
            painter.drawLine(points[index - 1], points[index])
        for point in points:
            painter.drawEllipse(point, 4, 4)
        if self.drag_start is not None and self.drag_current is not None:
            painter.drawRect(_target_rect(self.drag_start, self.drag_current))

    def mousePressEvent(self, event) -> None:
        if self.session is None or event.button() != Qt.LeftButton:
            return
        position = (float(event.x()), float(event.y()))
        if self.session.normalized_point(position[0], position[1], self.target_size) is None:
            self.studio._status("Pointer is outside the background content")
            return
        if self.mode == "press":
            self.draft_points.append(position)
        elif self.mode in {"widget", "panel"}:
            self.drag_start = position
            self.drag_current = position
        elif self.mode == "text":
            self.studio.commit_text(position)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if self.drag_start is not None:
            self.drag_current = (float(event.x()), float(event.y()))
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.LeftButton or self.drag_start is None:
            return
        end = (float(event.x()), float(event.y()))
        rect = _target_rect_tuple(self.drag_start, end)
        self.drag_start = None
        self.drag_current = None
        if rect[2] < 5 or rect[3] < 5:
            self.update()
            return
        if self.mode == "widget":
            self.studio.commit_widget(rect)
        elif self.mode == "panel":
            self.studio.commit_panel(rect)
        self.update()

    def mouseDoubleClickEvent(self, event) -> None:
        if self.mode == "press" and len(self.draft_points) >= 3:
            self.studio.commit_press_point()


def _draw_polygon(painter: QPainter, points: List[QPoint]) -> None:
    if len(points) < 2:
        return
    for index, point in enumerate(points):
        painter.drawLine(point, points[(index + 1) % len(points)])


def _target_rect(
    first: Tuple[float, float], second: Tuple[float, float]
) -> QRect:
    x, y, width, height = _target_rect_tuple(first, second)
    return QRect(int(x), int(y), int(width), int(height))


def _target_rect_tuple(
    first: Tuple[float, float], second: Tuple[float, float]
) -> Tuple[float, float, float, float]:
    left = min(first[0], second[0])
    top = min(first[1], second[1])
    return (
        left,
        top,
        abs(second[0] - first[0]),
        abs(second[1] - first[1]),
    )


def _pixmap_png_bytes(pixmap: QPixmap) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.WriteOnly):
        raise RuntimeError("cannot open PNG memory buffer")
    try:
        if not pixmap.save(buffer, "PNG"):
            raise RuntimeError("cannot encode surface background as PNG")
        return bytes(data)
    finally:
        buffer.close()
