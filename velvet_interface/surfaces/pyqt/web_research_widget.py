# SPDX-License-Identifier: GPL-3.0-only
"""Interactive research desk rendered inside the reusable Scroll artwork."""

from __future__ import annotations

from typing import Callable, Dict, Optional

try:
    from PyQt5.QtCore import Qt, QUrl
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
    QWidget = object  # type: ignore[misc,assignment]

from velvet_interface.web_research import (
    DocumentProvider,
    SearchProvider,
    WebResearchDocument,
    WebResearchResult,
)


ItemCallback = Callable[[WebResearchDocument], object]


class QtWebResearchWidget(QWidget):
    """Touch-friendly web research pane with no implicit network authority.

    The image-surface manifest owns the Scroll artwork, Return hotspot, and
    Emergency hotspot. This widget is deliberately placed only inside the
    measured writing area so those outer surface controls remain independent.
    """

    def __init__(
        self,
        search_provider: Optional[SearchProvider] = None,
        document_provider: Optional[DocumentProvider] = None,
        on_ask_velour: Optional[ItemCallback] = None,
        on_save_library: Optional[ItemCallback] = None,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is required for Velour Web Research")
        super().__init__()
        self.search_provider = search_provider
        self.document_provider = document_provider
        self.on_ask_velour = on_ask_velour
        self.on_save_library = on_save_library
        self._results = {}  # type: Dict[str, WebResearchResult]
        self._current_document = None  # type: Optional[WebResearchDocument]

        self.setObjectName("velourWebResearch")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(
            "QWidget#velourWebResearch { background: transparent; color: #24180f; }"
            "QWidget#researchPanel { background: rgba(246, 235, 211, 225); border: 1px solid rgba(78, 51, 28, 150); border-radius: 8px; }"
            "QWidget#researchViewport { background: rgba(255, 255, 255, 246); border: 1px solid rgba(70, 60, 48, 150); border-radius: 8px; }"
            "QLabel#researchTitle { background: transparent; font-size: 23px; font-weight: 700; color: #3a2415; }"
            "QLabel#researchSection { background: transparent; font-size: 15px; font-weight: 700; color: #4e321c; }"
            "QLabel#researchStatus { background: transparent; color: #67451f; font-size: 11px; padding: 2px; }"
            "QPushButton { min-height: 30px; padding: 3px 8px; }"
            "QLineEdit, QListWidget { background: rgba(255, 252, 244, 240); color: #21170f; }"
            "QTextBrowser { background: white; color: #171717; border: none; padding: 8px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("VELOUR RESEARCH")
        title.setObjectName("researchTitle")
        self.status_label = QLabel("REFERENCE ONLY · NETWORK ADAPTER NOT CONNECTED")
        self.status_label.setObjectName("researchStatus")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(title)
        header.addWidget(self.status_label, 1)
        root.addLayout(header)

        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search the web through Velour...")
        self.search_button = QPushButton("Search")
        search_row.addWidget(self.search_box, 1)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        body = QHBoxLayout()
        body.setSpacing(8)
        body.addWidget(self._build_results_panel(), 3)
        body.addWidget(self._build_reader_panel(), 8)
        root.addLayout(body, 1)

        footer = QHBoxLayout()
        self.source_label = QLabel("Source: none")
        self.source_label.setObjectName("researchStatus")
        self.source_label.setWordWrap(True)
        self.ask_button = QPushButton("Ask Velour")
        self.save_button = QPushButton("Save to Library")
        self.ask_button.setEnabled(False)
        self.save_button.setEnabled(False)
        footer.addWidget(self.source_label, 1)
        footer.addWidget(self.ask_button)
        footer.addWidget(self.save_button)
        root.addLayout(footer)

        self.search_button.clicked.connect(self.search)
        self.search_box.returnPressed.connect(self.search)
        self.open_button.clicked.connect(self.open_selected)
        self.result_list.itemDoubleClicked.connect(lambda _item: self.open_selected())
        self.ask_button.clicked.connect(self._ask_current)
        self.save_button.clicked.connect(self._save_current)

    def _panel(self, object_name: str = "researchPanel") -> QWidget:
        panel = QWidget()
        panel.setObjectName(object_name)
        return panel

    def _build_results_panel(self) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(7, 7, 7, 7)
        section = QLabel("Results")
        section.setObjectName("researchSection")
        self.result_list = QListWidget()
        self.open_button = QPushButton("Open")
        layout.addWidget(section)
        layout.addWidget(self.result_list, 1)
        layout.addWidget(self.open_button)
        return panel

    def _build_reader_panel(self) -> QWidget:
        panel = self._panel("researchViewport")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(7, 7, 7, 7)
        row = QHBoxLayout()
        self.reader_title = QLabel("Research desk ready")
        self.reader_title.setObjectName("researchSection")
        self.reader_mode = QLabel("OFFLINE SHELL")
        self.reader_mode.setObjectName("researchStatus")
        row.addWidget(self.reader_title)
        row.addStretch(1)
        row.addWidget(self.reader_mode)

        self.reader = QTextBrowser()
        self.reader.setOpenExternalLinks(False)
        self.reader.setOpenLinks(False)
        self.reader.document().setBaseUrl(QUrl())
        self.reader.setHtml(
            "<h2>Velour Research</h2>"
            "<p>The Scroll stays fixed while this reading pane scrolls vertically.</p>"
            "<p><b>No live web adapter is connected in this build.</b> Search and fetched "
            "pages will arrive through an explicit provider boundary in the next phase.</p>"
            "<p>Web material remains external reference input: no scripts, no Court "
            "authority, no vehicle control, and no automatic Library persistence.</p>"
        )
        layout.addLayout(row)
        layout.addWidget(self.reader, 1)
        return panel

    def search(self) -> None:
        query = self.search_box.text().strip()
        if not query:
            self._status("Enter a research query")
            return
        if self.search_provider is None:
            self._status("Live web search adapter is not connected yet")
            return
        try:
            results = list(self.search_provider(query))
        except (OSError, RuntimeError, ValueError) as exc:
            self._status("Search unavailable: %s" % exc)
            return

        self._results.clear()
        self.result_list.clear()
        for result in results:
            row = QListWidgetItem(result.title)
            row.setData(Qt.UserRole, result.result_id)
            if result.summary:
                row.setToolTip(result.summary)
            self.result_list.addItem(row)
            self._results[result.result_id] = result
        self._status(
            "%d result%s · reference only"
            % (len(results), "" if len(results) == 1 else "s")
        )

    def open_selected(self) -> None:
        row = self.result_list.currentItem()
        if row is None:
            self._status("Select a result first")
            return
        result_id = str(row.data(Qt.UserRole))
        result = self._results.get(result_id)
        if result is None:
            self._status("Selected result is no longer available")
            return
        if self.document_provider is None:
            self._status("Document fetch adapter is not connected yet")
            return
        try:
            document = self.document_provider(result)
        except (OSError, RuntimeError, ValueError) as exc:
            self._status("Document unavailable: %s" % exc)
            return

        self._current_document = document
        self.reader_title.setText(document.title)
        self.reader_mode.setText("WEB REFERENCE")
        self.source_label.setText("Source: %s · %s" % (document.source, document.url))
        self.reader.document().setBaseUrl(QUrl())
        if document.html:
            self.reader.setHtml(document.html)
        else:
            self.reader.setPlainText(document.text)
        self.ask_button.setEnabled(self.on_ask_velour is not None)
        self.save_button.setEnabled(self.on_save_library is not None)
        self._status("Opened external reference · no authority granted")

    def _ask_current(self) -> None:
        if self._current_document is not None and self.on_ask_velour is not None:
            self.on_ask_velour(self._current_document)

    def _save_current(self) -> None:
        if self._current_document is not None and self.on_save_library is not None:
            self.on_save_library(self._current_document)

    def _status(self, text: str) -> None:
        self.status_label.setText(text)
