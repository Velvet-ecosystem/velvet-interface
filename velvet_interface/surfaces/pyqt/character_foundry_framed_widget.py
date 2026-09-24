# SPDX-License-Identifier: GPL-3.0-only
"""Parchment-fitted presentation wrapper for the live Character Foundry."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QWidget

from velvet_interface.foundry_bridge import FoundryBridge
from velvet_interface.surfaces.pyqt.character_foundry_widget import (
    QtCharacterFoundryWidget,
)


BackCallback = Callable[[], Any]

# Character Foundry needs more horizontal room than the read-only Forge pages,
# but still belongs visually inside the same parchment family.
_CHARACTER_FOUNDRY_FRAME = (0.10, 0.15, 0.80, 0.67)


class _TransparentCharacterFoundryWidget(QtCharacterFoundryWidget):
    """Character Foundry content without its own second copy of the parchment."""

    def paintEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        # The parent wrapper owns the shared Forge scroll artwork.
        return None


class QtCharacterFoundryFramedWidget(QWidget):
    """Render Character Foundry as a fitted workbench over the Forge scroll."""

    def __init__(
        self,
        bridge: FoundryBridge,
        target_size: Tuple[int, int],
        background_path: Path,
        on_back: Optional[BackCallback] = None,
    ) -> None:
        super().__init__()
        self._background = QPixmap(str(background_path))
        self.setFixedSize(*target_size)
        self.setObjectName("characterFoundryFrame")

        x, y, width, height = _CHARACTER_FOUNDRY_FRAME
        frame_width = max(1, int(round(self.width() * width)))
        frame_height = max(1, int(round(self.height() * height)))
        self.workbench = _TransparentCharacterFoundryWidget(
            bridge=bridge,
            target_size=(frame_width, frame_height),
            background_path=background_path,
            on_back=on_back,
        )
        self.workbench.setParent(self)
        self.workbench.setAttribute(Qt.WA_TranslucentBackground, True)
        self.workbench.setAutoFillBackground(False)
        self.workbench.setStyleSheet(
            self.workbench.styleSheet()
            + "QLabel#foundryTitle { font-size:24px; }"
            + "QLabel#foundrySection { font-size:15px; }"
            + "QPushButton { min-height:28px; padding:2px 7px; }"
            + "QTabBar::tab { padding:3px 6px; }"
        )
        self._position_workbench()

    def _position_workbench(self) -> None:
        x, y, width, height = _CHARACTER_FOUNDRY_FRAME
        self.workbench.setGeometry(
            int(round(self.width() * x)),
            int(round(self.height() * y)),
            max(1, int(round(self.width() * width))),
            max(1, int(round(self.height() * height))),
        )
        self.workbench.raise_()

    def resizeEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        if hasattr(self, "workbench"):
            self._position_workbench()

    def paintEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        if self._background.isNull():
            painter.fillRect(self.rect(), Qt.black)
            return
        scaled = self._background.scaled(
            self.size(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation,
        )
        painter.drawPixmap(0, 0, scaled)

    def refresh_candidates(self) -> None:
        self.workbench.refresh_candidates()
