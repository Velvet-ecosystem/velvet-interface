# SPDX-License-Identifier: GPL-3.0-only
"""PyQt read-only Library Reader for the Founder surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

try:
    from PyQt5.QtCore import Qt, QUrl
    from PyQt5.QtGui import QPainter, QPixmap
    from PyQt5.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore

from velvet_interface.library_preview import LibraryPreviewItem, LocalLibraryPreviewProvider


BackCallback = Callable[[], Any]


class QtLibraryReaderWidget(QWidget):
    """Touch-friendly, authority-free reader over a bounded local preview provider."""

    def __init__(
        self,
        provider: LocalLibraryPreviewProvider,
        target_size: Tuple[int, int],
        background_path: Path,
        on_back: Optional[BackCallback] = None,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is required for Library Reader")
        super().__init__()
        self.provider = provider
        self.target_size = target_size
        self.background_path = Path(background_path)
        self.on_back = on_back
        self._background = QPixmap(str(self.background_path))
        self._items = {}  # type: Dict[str, LibraryPreviewItem]

        self.setObjectName("libraryReader")
        self.setFixedSize(*target_size)
        self.setStyleSheet(
            "QWidget#libraryReader { color: #24180f; }"
            "QWidget#libraryPanel { background: rgba(246, 235, 211, 218); border: 1px solid rgba(78, 51, 28, 150); border-radius: 10px; }"
            "QWidget#libraryViewport { background: rgba(255, 255, 255, 244); border: 1px solid rgba(70, 60, 48, 150); border-radius: 8px; }"
            "QLabel#libraryTitle { font-size: 27px; font-weight: 600; color: #3a2415; }"
            "QLabel#librarySection { font-size: 16px; font-weight: 600; color: #4e321c; }"
            "QLabel#libraryStatus { color: #67451f; padding: 4px; }"
            "QPushButton { min-height: 34px; padding: 4px 10px; }"
            "QLineEdit, QListWidget { background: rgba(255, 252, 244, 235); color: #21170f; }"
            "QTextBrowser { background: white; color: #171717; border: none; padding: 10px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("VELOUR'S LIBRARY")
        title.setObjectName("libraryTitle")
        self.status_label = QLabel("Read-only local archive")
        self.status_label.setObjectName("libraryStatus")
        self.back_button = QPushButton("Back")
        header.addWidget(title)
        header.addWidget(self.status_label, 1)
        header.addWidget(self.back_button)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(10)
        body.addWidget(self._build_catalog_panel(), 3)
        body.addWidget(self._build_reader_panel(), 7)
        body.addWidget(self._build_metadata_panel(), 3)
        root.addLayout(body, 1)

        self.search_box.returnPressed.connect(self.refresh_items)
        self.refresh_button.clicked.connect(self.refresh_items)
        self.item_list.itemDoubleClicked.connect(lambda _item: self.open_selected())
        self.open_button.clicked.connect(self.open_selected)
        self.back_button.clicked.connect(self._go_back)
        self.refresh_items()

    def paintEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        if self._background.isNull():
            painter.fillRect(self.rect(), Qt.black)
            return
        scaled = self._background.scaled(
            self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        x = (scaled.width() - self.width()) // 2
        y = (scaled.height() - self.height()) // 2
        painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())

    def _panel(self, object_name: str = "libraryPanel") -> QWidget:
        panel = QWidget()
        panel.setObjectName(object_name)
        return panel

    def _build_catalog_panel(self) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        section = QLabel("Shelves")
        section.setObjectName("librarySection")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search title or path")
        self.item_list = QListWidget()
        self.open_button = QPushButton("Open")
        self.refresh_button = QPushButton("Refresh")
        layout.addWidget(section)
        layout.addWidget(self.search_box)
        layout.addWidget(self.item_list, 1)
        layout.addWidget(self.open_button)
        layout.addWidget(self.refresh_button)
        return panel

    def _build_reader_panel(self) -> QWidget:
        panel = self._panel("libraryViewport")
        layout = QVBoxLayout(panel)
        row = QHBoxLayout()
        self.reader_title = QLabel("Select an item")
        self.reader_title.setObjectName("librarySection")
        self.reader_mode = QLabel("READY")
        self.reader_mode.setObjectName("libraryStatus")
        row.addWidget(self.reader_title)
        row.addStretch(1)
        row.addWidget(self.reader_mode)
        self.reader = QTextBrowser()
        self.reader.setOpenExternalLinks(False)
        self.reader.setOpenLinks(False)
        self.reader.setHtml(
            "<h2>Velour's Library</h2>"
            "<p>Select a catalogued item from the shelf.</p>"
            "<p>The white page is intentional for downloaded websites so their own "
            "layout remains visually separate from the Velvet scroll frame.</p>"
        )
        layout.addLayout(row)
        layout.addWidget(self.reader, 1)
        return panel

    def _build_metadata_panel(self) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        section = QLabel("Source")
        section.setObjectName("librarySection")
        self.path_label = QLabel("No item selected")
        self.path_label.setWordWrap(True)
        self.format_label = QLabel("Format: —")
        self.size_label = QLabel("Size: —")
        boundary = QLabel(
            "READ ONLY\n"
            "No scripts executed\n"
            "No external links opened\n"
            "No library files modified\n"
            "No authority granted"
        )
        boundary.setWordWrap(True)
        layout.addWidget(section)
        layout.addWidget(self.path_label)
        layout.addWidget(self.format_label)
        layout.addWidget(self.size_label)
        layout.addSpacing(12)
        layout.addWidget(boundary)
        layout.addStretch(1)
        return panel

    def refresh_items(self) -> None:
        query = self.search_box.text().strip()
        try:
            items = self.provider.list_items(query=query)
        except (OSError, RuntimeError, ValueError) as exc:
            self._status("Library unavailable: %s" % exc)
            return
        self._items.clear()
        self.item_list.clear()
        for item in items:
            display = "%s  [%s]" % (item.title, item.suffix.lstrip(".").upper())
            row = QListWidgetItem(display)
            row.setData(Qt.UserRole, item.relative_path)
            self.item_list.addItem(row)
            self._items[item.relative_path] = item
        if self.provider.root.is_dir():
            self._status("%d item%s visible" % (len(items), "" if len(items) == 1 else "s"))
        else:
            self._status("Library root not mounted: %s" % self.provider.root)

    def open_selected(self) -> None:
        row = self.item_list.currentItem()
        if row is None:
            self._status("Select an item first")
            return
        relative = str(row.data(Qt.UserRole))
        item = self._items.get(relative)
        if item is None:
            self._status("Selected item is no longer in the local catalog")
            return
        self._show_metadata(item)
        self.reader_title.setText(item.title)
        self.reader_mode.setText(item.preview_kind.upper())
        try:
            if item.preview_kind == "text":
                self.reader.document().setBaseUrl(QUrl())
                self.reader.setPlainText(self.provider.read_text(item))
            elif item.preview_kind == "html":
                path = self.provider.path_for(item)
                self.reader.document().setBaseUrl(QUrl.fromLocalFile(str(path.parent) + "/"))
                self.reader.setHtml(self.provider.read_text(item))
            else:
                self._show_adapter_placeholder(item)
        except (FileNotFoundError, OSError, UnicodeError, ValueError) as exc:
            self.reader.setPlainText("Preview unavailable: %s" % exc)
            self._status("Preview unavailable")
            return
        self._status("Opened read-only: %s" % item.relative_path)

    def _show_adapter_placeholder(self, item: LibraryPreviewItem) -> None:
        labels = {
            "pdf": "PDF renderer adapter is not connected yet.",
            "epub": "EPUB renderer adapter is not connected yet.",
            "zim": "ZIM/Kiwix reader adapter is not connected yet.",
        }
        message = labels.get(item.preview_kind, "No preview adapter is connected for this format.")
        self.reader.setHtml(
            "<h2>%s</h2><p>%s</p>"
            "<p>The original remains catalogued and untouched. This surface will use the "
            "dedicated adapter when that backend contract is implemented.</p>"
            % (item.title, message)
        )

    def _show_metadata(self, item: LibraryPreviewItem) -> None:
        self.path_label.setText(item.relative_path)
        self.format_label.setText("Format: %s" % (item.suffix.lstrip(".").upper() or "unknown"))
        self.size_label.setText("Size: %s" % self._format_bytes(item.size_bytes))

    @staticmethod
    def _format_bytes(size: int) -> str:
        value = float(size)
        units = ("B", "KB", "MB", "GB", "TB")
        for unit in units:
            if value < 1024.0 or unit == units[-1]:
                return "%.1f %s" % (value, unit)
            value /= 1024.0
        return "%d B" % size

    def _status(self, text: str) -> None:
        self.status_label.setText(text)

    def _go_back(self) -> None:
        if self.on_back is not None:
            self.on_back()
