# SPDX-License-Identifier: GPL-3.0-only
"""Trusted PyQt written-conversation surface for the Founder interface."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Tuple

MAX_WRITTEN_TURN_CHARACTERS = 4096
MAX_TRANSCRIPT_ENTRIES = 80

# Use the same physically measured parchment writing frame as the three Forge
# scroll workspaces so Velvet's written conversation belongs to the same room
# family on the Founder display.
_SCROLL_CONTENT_RECT = (0.175347, 0.180000, 0.647570, 0.590062)


def normalize_conversation_reply(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate the narrow local conversation reply before showing it in UI."""

    if not isinstance(result, Mapping):
        raise TypeError("conversation reply must be a mapping")
    text = result.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("conversation reply text is invalid")
    if result.get("authority_granted") is not False:
        raise ValueError("conversation reply cannot grant authority")
    if result.get("grants_execution") is not False:
        raise ValueError("conversation reply cannot grant execution")
    if result.get("grants_actuation") is not False:
        raise ValueError("conversation reply cannot grant actuation")
    if not isinstance(result.get("requires_authority_check"), bool):
        raise ValueError("conversation authority-check flag is invalid")
    generator = result.get("generator")
    if not isinstance(generator, str) or not generator.strip():
        raise ValueError("conversation reply generator is invalid")
    return dict(result)


try:
    from PyQt5.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
    from PyQt5.QtGui import QPainter, QPixmap
    from PyQt5.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]


if PYQT_AVAILABLE:
    class _ConversationSignals(QObject):
        success = pyqtSignal(object)
        failure = pyqtSignal(str)


    class _ConversationTask(QRunnable):
        def __init__(self, submit_turn: Callable[[str], Mapping[str, Any]], text: str) -> None:
            super().__init__()
            self.submit_turn = submit_turn
            self.text = text
            self.signals = _ConversationSignals()

        def run(self) -> None:
            try:
                result = normalize_conversation_reply(self.submit_turn(self.text))
            except Exception as exc:
                self.signals.failure.emit(str(exc) or type(exc).__name__)
                return
            self.signals.success.emit(result)


class QtWrittenConversationWidget(QWidget):
    """Parchment-framed text surface delegating every turn to a trusted submitter."""

    def __init__(
        self,
        *,
        submit_turn: Callable[[str], Mapping[str, Any]],
        target_size: Tuple[int, int],
        on_back: Callable[[], Any],
        background_path: Path = Path("examples/assets/workspace_scroll.png"),
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is required for written conversation surface")
        if not callable(submit_turn):
            raise TypeError("submit_turn must be callable")
        if not callable(on_back):
            raise TypeError("on_back must be callable")
        super().__init__()
        self.submit_turn = submit_turn
        self.on_back = on_back
        self.background_path = Path(background_path)
        self._background = QPixmap(str(self.background_path))
        self._pending = False
        self._history = []  # type: list[str]
        self._pool = QThreadPool.globalInstance()

        width, height = target_size
        self.setObjectName("writtenConversation")
        self.setFixedSize(int(width), int(height))
        self.setStyleSheet(
            "QWidget#writtenConversation { background: transparent; color: #2d1c11; }"
            "QWidget#conversationFrame { background: transparent; }"
            "QLabel#conversationTitle { color: #3a2214; font-size: 22px; font-weight: 700; }"
            "QLabel#conversationStatus { color: #704b32; font-size: 11px; font-weight: 600; }"
            "QTextBrowser { background: rgba(8, 8, 12, 220); border: 1px solid rgba(78, 51, 28, 180); "
            "border-radius: 7px; padding: 9px; color: #eee8df; font-size: 15px; }"
            "QLineEdit { background: rgba(17, 17, 24, 235); border: 1px solid #6a4f45; border-radius: 6px; "
            "padding: 7px; color: #f3ede5; font-size: 15px; }"
            "QPushButton { background: rgba(33, 27, 36, 235); color: #eee8df; border: 1px solid #6a4f45; "
            "border-radius: 6px; min-height: 30px; padding: 3px 12px; }"
            "QPushButton:disabled { color: #66646a; border-color: #2b2930; }"
        )

        self.content_frame = QWidget(self)
        self.content_frame.setObjectName("conversationFrame")
        root = QVBoxLayout(self.content_frame)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(7)

        header = QHBoxLayout()
        back = QPushButton("Back")
        back.clicked.connect(self.on_back)
        title = QLabel("VELVET  •  WRITTEN CONVERSATION")
        title.setObjectName("conversationTitle")
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(back)
        header.addStretch(1)
        header.addWidget(title)
        header.addStretch(1)
        header.addSpacing(back.sizeHint().width())
        root.addLayout(header)

        self.transcript = QTextBrowser()
        self.transcript.setReadOnly(True)
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setPlainText(
            "Velvet> Written conversation ready. I will answer from verified local context when it is available."
        )
        root.addWidget(self.transcript, stretch=1)

        self.status = QLabel("Local conversation surface • no execution authority")
        self.status.setObjectName("conversationStatus")
        self.status.setAlignment(Qt.AlignLeft)
        root.addWidget(self.status)

        entry_row = QHBoxLayout()
        entry_row.setSpacing(7)
        self.entry = QLineEdit()
        self.entry.setMaxLength(MAX_WRITTEN_TURN_CHARACTERS)
        self.entry.setPlaceholderText("Type to Velvet…")
        self.entry.returnPressed.connect(self._submit)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._submit)
        entry_row.addWidget(self.entry, stretch=1)
        entry_row.addWidget(self.send_button)
        root.addLayout(entry_row)

        self._position_content_frame()

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

    def _position_content_frame(self) -> None:
        x, y, width, height = _SCROLL_CONTENT_RECT
        self.content_frame.setGeometry(
            int(round(self.width() * x)),
            int(round(self.height() * y)),
            max(1, int(round(self.width() * width))),
            max(1, int(round(self.height() * height))),
        )
        self.content_frame.raise_()

    def resizeEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        if hasattr(self, "content_frame"):
            self._position_content_frame()

    def focus_input(self) -> None:
        if PYQT_AVAILABLE:
            self.entry.setFocus(Qt.OtherFocusReason)

    def _submit(self) -> None:
        if self._pending:
            return
        text = self.entry.text().strip()
        if not text:
            return
        self.entry.clear()
        self._append("Mister> %s" % text)
        self._set_pending(True)
        task = _ConversationTask(self.submit_turn, text)
        task.signals.success.connect(self._on_success)
        task.signals.failure.connect(self._on_failure)
        self._pool.start(task)

    def _on_success(self, result: Mapping[str, Any]) -> None:
        self._append("Velvet> %s" % str(result["text"]).strip())
        if result.get("requires_authority_check") is True:
            self.status.setText("Runtime authorization required for the requested action")
        else:
            self.status.setText("Verified local conversation • %s" % result["generator"])
        self._set_pending(False)

    def _on_failure(self, message: str) -> None:
        self._append("Velvet> I couldn't verify that turn through the local conversation service.")
        self.status.setText("Conversation service unavailable: %s" % message)
        self._set_pending(False)

    def _set_pending(self, pending: bool) -> None:
        self._pending = bool(pending)
        self.entry.setEnabled(not self._pending)
        self.send_button.setEnabled(not self._pending)
        if self._pending:
            self.status.setText("Checking local verified context…")
        else:
            self.entry.setFocus(Qt.OtherFocusReason)

    def _append(self, text: str) -> None:
        self._history.append(text)
        self._history = self._history[-MAX_TRANSCRIPT_ENTRIES:]
        initial = (
            "Velvet> Written conversation ready. I will answer from verified local context when it is available."
        )
        self.transcript.setPlainText("\n\n".join([initial] + self._history))
        scrollbar = self.transcript.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
