# SPDX-License-Identifier: GPL-3.0-only
"""Federated Archive search desk rendered inside the reusable Scroll artwork."""
from __future__ import annotations

import html
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
except ImportError:  # pragma: no cover
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]

from velvet_interface.archive_search import ArchiveSearchResult, ArchiveSearchSnapshot


SearchProvider = Callable[[str], ArchiveSearchSnapshot]


class QtArchiveSearchWidget(QWidget):
    """Touch-friendly, reference-only view over Velour federated search."""

    def __init__(self, search_provider: Optional[SearchProvider] = None) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is required for Velour Archive Search")
        super().__init__()
        self.search_provider = search_provider
        self._results = {}  # type: Dict[str, ArchiveSearchResult]

        self.setObjectName("velourArchiveSearch")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(
            "QWidget#velourArchiveSearch { background: transparent; color: #24180f; }"
            "QWidget#archiveSearchPanel { background: rgba(246, 235, 211, 225); border: 1px solid rgba(78, 51, 28, 150); border-radius: 8px; }"
            "QWidget#archiveSearchViewport { background: rgba(255, 255, 255, 246); border: 1px solid rgba(70, 60, 48, 150); border-radius: 8px; }"
            "QLabel#archiveSearchTitle { background: transparent; font-size: 23px; font-weight: 700; color: #3a2415; }"
            "QLabel#archiveSearchSection { background: transparent; font-size: 15px; font-weight: 700; color: #4e321c; }"
            "QLabel#archiveSearchStatus { background: transparent; color: #67451f; font-size: 11px; padding: 2px; }"
            "QPushButton { min-height: 30px; padding: 3px 8px; }"
            "QLineEdit, QListWidget { background: rgba(255, 252, 244, 240); color: #21170f; }"
            "QTextBrowser { background: white; color: #171717; border: none; padding: 8px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("VELOUR ARCHIVE SEARCH")
        title.setObjectName("archiveSearchTitle")
        self.status_label = QLabel("REFERENCE ONLY · LIBRARY FIRST")
        self.status_label.setObjectName("archiveSearchStatus")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(title)
        header.addWidget(self.status_label, 1)
        root.addLayout(header)

        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search Library, ZIM shelves, and live Web...")
        self.search_button = QPushButton("Search")
        search_row.addWidget(self.search_box, 1)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        self.source_status = QLabel("Library: ready when vault is present · ZIM/Web: optional")
        self.source_status.setObjectName("archiveSearchStatus")
        root.addWidget(self.source_status)

        body = QHBoxLayout()
        body.setSpacing(8)
        body.addWidget(self._build_results_panel(), 3)
        body.addWidget(self._build_detail_panel(), 8)
        root.addLayout(body, 1)

        self.search_button.clicked.connect(self.search)
        self.search_box.returnPressed.connect(self.search)
        self.result_list.currentItemChanged.connect(lambda _current, _previous: self.show_selected())
        self.result_list.itemDoubleClicked.connect(lambda _item: self.show_selected())

    def _panel(self, object_name: str = "archiveSearchPanel") -> QWidget:
        panel = QWidget()
        panel.setObjectName(object_name)
        return panel

    def _build_results_panel(self) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(7, 7, 7, 7)
        section = QLabel("Results")
        section.setObjectName("archiveSearchSection")
        self.result_list = QListWidget()
        layout.addWidget(section)
        layout.addWidget(self.result_list, 1)
        return panel

    def _build_detail_panel(self) -> QWidget:
        panel = self._panel("archiveSearchViewport")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(7, 7, 7, 7)
        row = QHBoxLayout()
        self.detail_title = QLabel("Search across Velour's shelves")
        self.detail_title.setObjectName("archiveSearchSection")
        self.detail_mode = QLabel("FEDERATED")
        self.detail_mode.setObjectName("archiveSearchStatus")
        row.addWidget(self.detail_title)
        row.addStretch(1)
        row.addWidget(self.detail_mode)

        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(False)
        self.detail.setOpenLinks(False)
        self.detail.document().setBaseUrl(QUrl())
        self.detail.setHtml(
            "<h2>Velour Archive Search</h2>"
            "<p>One query can search the protected local Library, optional offline Kiwix/ZIM shelves, and the configured live Web provider.</p>"
            "<p>Sources stay visibly separate. A missing optional source does not suppress the others, and search results remain reference-only with no Velvet authority.</p>"
        )
        layout.addLayout(row)
        layout.addWidget(self.detail, 1)
        return panel

    def search(self) -> None:
        query = self.search_box.text().strip()
        if not query:
            self._status("Enter a search query")
            return
        if self.search_provider is None:
            self._status("Velour federated search adapter is not connected")
            return
        try:
            snapshot = self.search_provider(query)
        except (OSError, RuntimeError, ValueError) as exc:
            self._status("Search unavailable: %s" % exc)
            return

        self._results.clear()
        self.result_list.clear()
        for result in snapshot.results:
            row = QListWidgetItem("[%s] %s" % (self._provider_mark(result.provider), result.title))
            row.setData(Qt.UserRole, result.result_id)
            row.setToolTip(result.summary or result.source)
            self.result_list.addItem(row)
            self._results[result.result_id] = result

        self.source_status.setText(self._source_line(snapshot))
        count = len(snapshot.results)
        self._status("%d result%s · authority none" % (count, "" if count == 1 else "s"))
        if count:
            self.result_list.setCurrentRow(0)
        else:
            self.detail_title.setText("No matching references")
            self.detail.setHtml("<p>No configured source returned a matching reference.</p>")

    def show_selected(self) -> None:
        row = self.result_list.currentItem()
        if row is None:
            return
        result = self._results.get(str(row.data(Qt.UserRole)))
        if result is None:
            return
        self.detail_title.setText(result.title)
        self.detail_mode.setText(result.provider.upper())

        metadata = dict(result.metadata)
        details = []
        if result.provider == "library":
            for key, label in (
                ("trust_class", "Trust"),
                ("lifecycle_state", "Lifecycle"),
                ("retrieval_method", "Match"),
            ):
                value = metadata.get(key)
                if value:
                    details.append("<b>%s:</b> %s" % (label, html.escape(str(value))))
        elif result.provider == "zim":
            if metadata.get("book"):
                details.append("<b>ZIM:</b> %s" % html.escape(str(metadata["book"])))
        details.append("<b>Source:</b> %s" % html.escape(result.source))
        details.append("<b>Reference:</b> %s" % html.escape(result.uri))

        summary = html.escape(result.summary or "No preview text was supplied for this result.")
        self.detail.setHtml(
            "<h2>%s</h2><p>%s</p><p>%s</p><hr><p><i>Reference only. Selecting this result grants no authority and performs no persistence.</i></p>"
            % (html.escape(result.title), "<br>".join(details), summary)
        )

    @staticmethod
    def _provider_mark(provider: str) -> str:
        return {"library": "LIB", "zim": "ZIM", "web": "WEB"}.get(provider, "?")

    @staticmethod
    def _source_line(snapshot: ArchiveSearchSnapshot) -> str:
        parts = []
        for provider, label in (("library", "Library"), ("zim", "ZIM"), ("web", "Web")):
            state = snapshot.sources.get(provider, {})
            status = str(state.get("status") or "unknown")
            count = state.get("count", 0)
            if status == "ok":
                parts.append("%s: %s" % (label, count))
            else:
                parts.append("%s: %s" % (label, status))
        return " · ".join(parts)

    def _status(self, text: str) -> None:
        self.status_label.setText(text)
