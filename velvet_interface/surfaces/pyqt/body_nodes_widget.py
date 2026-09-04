# SPDX-License-Identifier: GPL-3.0-only
"""Touch-first read-only body/node list for the Maintenance workshop."""

from __future__ import annotations

from typing import Callable, Dict, Optional

try:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    PYQT_AVAILABLE = False
    QDialog = object  # type: ignore[misc,assignment]

from velvet_interface.body_nodes_live_status import (
    BodyNodeStatus,
    BodyNodesStatus,
)


class QtBodyNodesTouchList(QDialog):
    """Modal maintenance widget for observing the current Velvet body.

    The only interactive actions are selecting a node and closing the widget.
    There is deliberately no restart, quarantine, wake, work-placement, or hardware
    control surface here.
    """

    def __init__(
        self,
        *,
        status_provider: Callable[[], BodyNodesStatus],
        parent: Optional[QWidget] = None,
        refresh_ms: int = 1000,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for body nodes widget")
        if not callable(status_provider):
            raise TypeError("status_provider must be callable")
        if not 250 <= int(refresh_ms) <= 60000:
            raise ValueError("refresh_ms must be between 250 and 60000")
        super().__init__(parent)
        self.status_provider = status_provider
        self._nodes = {}  # type: Dict[str, BodyNodeStatus]
        self._selected_node_id = None  # type: Optional[str]

        self.setWindowTitle("Velvet Body Nodes")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setStyleSheet(
            "QDialog { background: rgba(7, 8, 12, 246); color: #eee8df; "
            "border: 2px solid rgba(216, 181, 106, 170); border-radius: 14px; }"
            "QLabel { background: transparent; border: none; color: #e8e3db; }"
            "QLabel#muted { color: #aeb4c1; }"
            "QLabel#detail { background: rgba(16, 18, 25, 220); "
            "border: 1px solid rgba(216, 181, 106, 90); border-radius: 10px; "
            "padding: 12px; }"
            "QListWidget { background: rgba(12, 14, 20, 220); color: #eee8df; "
            "border: 1px solid rgba(216, 181, 106, 90); border-radius: 10px; "
            "padding: 4px; outline: none; }"
            "QListWidget::item { min-height: 58px; border-bottom: 1px solid rgba(255,255,255,25); "
            "padding: 8px; }"
            "QListWidget::item:selected { background: rgba(111, 35, 46, 210); "
            "border: 1px solid rgba(233, 190, 119, 150); border-radius: 7px; }"
            "QPushButton { background: rgba(111, 35, 46, 220); color: #f4eee5; "
            "border: 1px solid rgba(233, 190, 119, 130); border-radius: 8px; "
            "padding: 8px 14px; font-weight: bold; }"
            "QPushButton:pressed { background: rgba(82, 25, 34, 240); }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("NODES / BODY SYSTEMS")
        title.setFont(QFont("Sans Serif", 14, QFont.Bold))
        header.addWidget(title, 1)
        close_button = QPushButton("CLOSE")
        close_button.setMinimumSize(92, 42)
        close_button.clicked.connect(self.hide)
        header.addWidget(close_button, 0)
        root.addLayout(header)

        self.summary = QLabel("Awaiting Runtime evidence")
        self.summary.setObjectName("muted")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        content = QHBoxLayout()
        content.setSpacing(12)
        self.node_list = QListWidget()
        self.node_list.setMinimumWidth(310)
        self.node_list.itemClicked.connect(self._node_clicked)
        content.addWidget(self.node_list, 2)

        self.details = QLabel("Touch a node for details.")
        self.details.setObjectName("detail")
        self.details.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details.setTextFormat(Qt.PlainText)
        self.details.setWordWrap(True)
        content.addWidget(self.details, 3)
        root.addLayout(content, 1)

        self.resources = QLabel("Body resources: unavailable")
        self.resources.setObjectName("muted")
        self.resources.setTextFormat(Qt.PlainText)
        self.resources.setWordWrap(True)
        root.addWidget(self.resources)

        boundary = QLabel("OBSERVATIONAL ONLY  •  NO CONTROL AUTHORITY")
        boundary.setObjectName("muted")
        boundary.setAlignment(Qt.AlignCenter)
        boundary.setFont(QFont("Sans Serif", 8, QFont.Bold))
        root.addWidget(boundary)

        self.timer = QTimer(self)
        self.timer.setInterval(int(refresh_ms))
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def present(self, *, surface_width: int, surface_height: int) -> None:
        """Size the touch list for the Founder display and show it modally."""

        width = max(620, int(surface_width * 0.84))
        height = max(420, int(surface_height * 0.82))
        self.resize(width, height)
        parent = self.parentWidget()
        if parent is not None:
            parent_rect = parent.frameGeometry()
            geometry = self.frameGeometry()
            geometry.moveCenter(parent_rect.center())
            self.move(geometry.topLeft())
        self.refresh()
        self.show()
        self.raise_()
        self.activateWindow()

    def refresh(self) -> None:
        try:
            status = self.status_provider()
        except Exception as exc:
            self.summary.setText("Node evidence unavailable: %s" % str(exc)[:160])
            self.resources.setText("Body resources: unavailable")
            return
        if not isinstance(status, BodyNodesStatus):
            self.summary.setText("Node evidence provider returned an invalid snapshot")
            return

        self._nodes = {item.node_id: item for item in status.nodes}
        previous = self._selected_node_id
        self.node_list.blockSignals(True)
        self.node_list.clear()
        selected_row = None
        for row, node in enumerate(status.nodes):
            item = QListWidgetItem(_node_row_text(node))
            item.setData(Qt.UserRole, node.node_id)
            item.setToolTip("Touch to inspect %s" % node.node_id)
            self.node_list.addItem(item)
            if node.node_id == previous:
                selected_row = row
        self.node_list.blockSignals(False)

        if selected_row is not None:
            self.node_list.setCurrentRow(selected_row)
        elif status.nodes:
            self.node_list.setCurrentRow(0)
            self._selected_node_id = status.nodes[0].node_id
        else:
            self._selected_node_id = None

        self.summary.setText(status.message)
        self.resources.setText(_resource_summary(status))
        self._refresh_details()

    def _node_clicked(self, item: QListWidgetItem) -> None:
        node_id = item.data(Qt.UserRole)
        if isinstance(node_id, str) and node_id in self._nodes:
            self._selected_node_id = node_id
            self._refresh_details()

    def _refresh_details(self) -> None:
        if self._selected_node_id is None:
            self.details.setText("Touch a node for details.")
            return
        node = self._nodes.get(self._selected_node_id)
        if node is None:
            self.details.setText("Selected node is no longer present in current evidence.")
            return
        self.details.setText(_node_detail_text(node))


def _node_row_text(node: BodyNodeStatus) -> str:
    role = node.organ.upper() if node.organ else "UNKNOWN"
    return "%s    %s\n%s" % (node.node_id.upper(), node.state, role)


def _node_detail_text(node: BodyNodeStatus) -> str:
    lines = [
        node.node_id.upper(),
        node.organ,
        "",
        "Status       %s" % node.state,
        "Availability %s" % node.availability,
        "Heartbeat    %s" % _heartbeat_text(node.heartbeat_age_seconds),
        "Health       %s" % _percent_text(node.health),
        "Load         %s" % _percent_text(node.current_load),
        "Tasks        %s" % _task_text(node.current_tasks, node.max_concurrent_tasks),
        "Resources    %s" % ("VISIBLE" if node.resource_visible else "NOT REPORTED"),
        "Body verify  %s" % ("YES" if node.body_verified else "NO"),
        "Continuity   %s" % ("YES" if node.continuity_verified else "NO"),
    ]
    if node.capabilities:
        lines.extend(("", "Capabilities", "  " + "\n  ".join(node.capabilities)))
    return "\n".join(lines)


def _resource_summary(status: BodyNodesStatus) -> str:
    if not status.resource_snapshot_available:
        return "Body resources: snapshot unavailable"
    if not status.resource_totals:
        return "Body resources: no online resources reported"
    parts = []
    for total in status.resource_totals:
        if total.unit == "bytes":
            parts.append(
                "%s %s free / %s"
                % (
                    total.kind.upper(),
                    _human_bytes(total.available),
                    _human_bytes(total.capacity),
                )
            )
        else:
            parts.append(
                "%s %.1f free / %.1f %s"
                % (total.kind.upper(), total.available, total.capacity, total.unit)
            )
    prefix = "Body %s" % status.body_id if status.body_id else "Body resources"
    return prefix + ":  " + "   •   ".join(parts)


def _heartbeat_text(age: Optional[float]) -> str:
    if age is None:
        return "not reported"
    if age < 1.0:
        return "<1 s ago"
    return "%.1f s ago" % age


def _percent_text(value: Optional[float]) -> str:
    return "not reported" if value is None else "%d%%" % int(round(value * 100.0))


def _task_text(current: Optional[int], maximum: Optional[int]) -> str:
    if current is None or maximum is None:
        return "not reported"
    return "%d / %d" % (current, maximum)


def _human_bytes(value: float) -> str:
    amount = float(value)
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    index = 0
    while amount >= 1024.0 and index < len(units) - 1:
        amount /= 1024.0
        index += 1
    return "%.1f %s" % (amount, units[index])
