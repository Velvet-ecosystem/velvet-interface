#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Visual authoring tool for Velvet image surfaces.

Usage for a new surface:

    python examples/surface_layout_editor.py \
      --manifest surfaces/home.surface.yaml \
      --image assets/home.png \
      --name home --surface-size 1280x720

Left-click polygon vertices, then press Enter to name and bind the press point.
Right-drag a rectangle to place a registered widget ID. Ctrl+S saves. Escape
clears the unfinished polygon. The editor writes normalized coordinates, so the
layout follows the same image across Founder and later display resolutions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from velvet_interface.scene_system.authoring import SurfaceLayoutAuthoringSession


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Author a Velvet image surface")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--name", default="home")
    parser.add_argument("--fit", choices=("stretch", "contain", "cover"), default="cover")
    parser.add_argument("--surface-size", default="1280x720")
    return parser


def parse_size(value: str) -> Tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except (ValueError, AttributeError):
        raise argparse.ArgumentTypeError("surface-size must look like 1280x720")
    if width < 320 or height < 240 or width > 8192 or height > 8192:
        raise argparse.ArgumentTypeError("surface-size is outside supported bounds")
    return width, height


def run_editor(args: argparse.Namespace) -> int:
    try:
        from PyQt5.QtCore import QPoint, QRect, Qt
        from PyQt5.QtGui import QColor, QKeySequence, QPainter, QPen, QPixmap
        from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox, QWidget
    except ImportError as exc:
        print("PyQt5 is required: pip install 'velvet-interface[qt]'", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    manifest_path = args.manifest.expanduser().resolve()
    if manifest_path.is_file():
        session = SurfaceLayoutAuthoringSession.load(str(manifest_path))
    else:
        if args.image is None:
            print("--image is required when creating a new manifest", file=sys.stderr)
            return 2
        image_path = args.image.expanduser().resolve()
        pixmap_probe = QPixmap(str(image_path))
        if pixmap_probe.isNull():
            print("Cannot load background image: %s" % image_path, file=sys.stderr)
            return 2
        session = SurfaceLayoutAuthoringSession(
            name=args.name,
            background_path=str(image_path),
            base_resolution=(pixmap_probe.width(), pixmap_probe.height()),
            fit_mode=args.fit,
        )

    target_size = parse_size(args.surface_size)

    class SurfaceEditor(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.session = session
            self.output_path = manifest_path
            self.target_size = target_size
            self.transform = self.session.scaler(target_size)
            self.background = QPixmap(self.session.background_path)
            if self.background.isNull():
                raise RuntimeError("Background image became unavailable")
            self.draft_points = []  # type: List[Tuple[float, float]]
            self.drag_start = None  # type: Optional[Tuple[float, float]]
            self.drag_current = None  # type: Optional[Tuple[float, float]]
            self.setFixedSize(*target_size)
            self.setMouseTracking(True)
            self.setWindowTitle(self._title("Ready"))

        def _title(self, state: str) -> str:
            return "Velvet Surface Editor | %s | %s" % (self.session.name, state)

        def paintEvent(self, event) -> None:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor("#07080c"))
            image_x, image_y, image_width, image_height = self.transform.get_letterbox_rect()
            scaled = self.background.scaled(
                image_width,
                image_height,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation,
            )
            painter.drawPixmap(image_x, image_y, scaled)
            painter.setRenderHint(QPainter.Antialiasing, True)

            press_pen = QPen(QColor(255, 90, 90, 220))
            press_pen.setWidth(2)
            painter.setPen(press_pen)
            for point in self.session.press_points:
                target_points = []
                for base_x, base_y in point.base_polygon(self.session.base_resolution):
                    x, y = self.transform.scale_point(base_x, base_y)
                    target_points.append(QPoint(int(round(x)), int(round(y))))
                self._draw_polygon(painter, target_points)
                if target_points:
                    painter.drawText(target_points[0] + QPoint(5, -5), point.point_id)

            widget_pen = QPen(QColor(90, 190, 255, 220))
            widget_pen.setWidth(2)
            painter.setPen(widget_pen)
            for widget in self.session.widgets:
                rect = self.transform.scale_rect(*widget.base_rect(self.session.base_resolution))
                painter.drawRect(*rect)
                painter.drawText(rect[0] + 5, rect[1] + 16, widget.widget_id)

            draft_pen = QPen(QColor(255, 215, 90, 240))
            draft_pen.setWidth(3)
            painter.setPen(draft_pen)
            draft_qpoints = [QPoint(int(x), int(y)) for x, y in self.draft_points]
            for index in range(1, len(draft_qpoints)):
                painter.drawLine(draft_qpoints[index - 1], draft_qpoints[index])
            for point in draft_qpoints:
                painter.drawEllipse(point, 4, 4)

            if self.drag_start is not None and self.drag_current is not None:
                left = min(self.drag_start[0], self.drag_current[0])
                top = min(self.drag_start[1], self.drag_current[1])
                width = abs(self.drag_current[0] - self.drag_start[0])
                height = abs(self.drag_current[1] - self.drag_start[1])
                painter.drawRect(QRect(int(left), int(top), int(width), int(height)))
            painter.end()

        @staticmethod
        def _draw_polygon(painter, points) -> None:
            if len(points) < 2:
                return
            for index, point in enumerate(points):
                painter.drawLine(point, points[(index + 1) % len(points)])

        def mousePressEvent(self, event) -> None:
            position = (float(event.x()), float(event.y()))
            normalized = self.session.normalized_point(
                position[0], position[1], self.target_size
            )
            if normalized is None:
                self.setWindowTitle(self._title("Outside background"))
                return
            if event.button() == Qt.LeftButton:
                self.draft_points.append(position)
                self.setWindowTitle(
                    self._title("Point %.4f, %.4f" % normalized)
                )
                print("point: [%.6f, %.6f]" % normalized)
            elif event.button() == Qt.RightButton:
                self.drag_start = position
                self.drag_current = position
            self.update()

        def mouseMoveEvent(self, event) -> None:
            if self.drag_start is not None:
                self.drag_current = (float(event.x()), float(event.y()))
                self.update()

        def mouseReleaseEvent(self, event) -> None:
            if event.button() != Qt.RightButton or self.drag_start is None:
                return
            end = (float(event.x()), float(event.y()))
            left = min(self.drag_start[0], end[0])
            top = min(self.drag_start[1], end[1])
            width = abs(end[0] - self.drag_start[0])
            height = abs(end[1] - self.drag_start[1])
            self.drag_start = None
            self.drag_current = None
            if width < 5 or height < 5:
                self.update()
                return
            widget_id, accepted = QInputDialog.getText(
                self, "Widget placement", "Registered widget ID:"
            )
            if accepted and widget_id.strip():
                try:
                    self.session.add_widget_from_target(
                        widget_id.strip(),
                        (left, top, width, height),
                        self.target_size,
                    )
                    self.setWindowTitle(self._title("Placed widget %s" % widget_id))
                except ValueError as exc:
                    QMessageBox.warning(self, "Widget rejected", str(exc))
            self.update()

        def keyPressEvent(self, event) -> None:
            if event.matches(QKeySequence.Save):
                saved = self.session.save(str(self.output_path))
                self.setWindowTitle(self._title("Saved %s" % saved.name))
                return
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._commit_press_point()
                return
            if event.key() == Qt.Key_Escape:
                self.draft_points = []
                self.setWindowTitle(self._title("Draft cleared"))
                self.update()
                return
            super().keyPressEvent(event)

        def _commit_press_point(self) -> None:
            if len(self.draft_points) < 3:
                QMessageBox.information(
                    self, "Press point", "Add at least three left-click vertices."
                )
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
                    self.draft_points,
                    self.target_size,
                    accessibility_label=point_id.strip().replace("_", " "),
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Press point rejected", str(exc))
                return
            self.draft_points = []
            self.setWindowTitle(self._title("Placed press point %s" % point_id))
            self.update()

    app = QApplication(sys.argv)
    editor = SurfaceEditor()
    editor.show()
    return app.exec_()


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return run_editor(args)


if __name__ == "__main__":
    raise SystemExit(main())
