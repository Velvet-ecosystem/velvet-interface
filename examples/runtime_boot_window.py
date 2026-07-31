#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Visible Founder window backed by Runtime boot and body snapshots."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable, List, Optional

from velvet_interface.boot_status import BootStatusViewModel
from velvet_interface.founder_live_status import (
    FounderLiveStatus,
    load_founder_live_status,
)


def _refresh_interval(value: str) -> int:
    interval = int(value)
    if not 250 <= interval <= 60000:
        raise argparse.ArgumentTypeError(
            "refresh interval must be between 250 and 60000 milliseconds"
        )
    return interval


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Display live Velvet Founder status"
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_BOOT_SNAPSHOT_PATH",
                ".velvet-dev/first-boot-snapshot.json",
            )
        ),
        help="path to the bounded Runtime boot snapshot JSON",
    )
    parser.add_argument(
        "--body-snapshot",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_BODY_SNAPSHOT_PATH",
                ".velvet-dev/body-state.json",
            )
        ),
        help="path to the bounded Runtime body-state snapshot JSON",
    )
    parser.add_argument(
        "--refresh-ms",
        type=_refresh_interval,
        default=1000,
        help="snapshot refresh interval in milliseconds",
    )
    return parser


def _static_status(model: BootStatusViewModel) -> FounderLiveStatus:
    return FounderLiveStatus(
        boot=model,
        body_available=False,
        body_presence="unavailable",
        body_summary="",
        sensor_count=0,
        health_event_count=0,
        receipt_count=0,
        body_error="Body state not connected",
    )


def run_window(model: BootStatusViewModel) -> int:
    """Preserve the original one-shot BootStatusViewModel entry point."""

    return _run_qt(lambda: _static_status(model), refresh_ms=0)


def run_live_window(
    boot_path: Path,
    body_path: Path,
    refresh_ms: int = 1000,
) -> int:
    """Reload trusted local snapshots without giving Interface a Runtime handle."""

    return _run_qt(
        lambda: load_founder_live_status(boot_path, body_path),
        refresh_ms=refresh_ms,
    )


def _run_qt(
    loader: Callable[[], FounderLiveStatus],
    refresh_ms: int,
) -> int:
    try:
        from PyQt5.QtCore import QTimer, Qt
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import (
            QApplication,
            QFrame,
            QGridLayout,
            QLabel,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        print(
            "PyQt5 is required: pip install velvet-interface[qt]",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 2

    initial = loader()
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Velvet Founder Runtime")
    window.resize(800, 560)
    window.setStyleSheet(
        "QWidget { background: #07080c; color: #e8e3db; }"
        "QLabel#title { color: #d8b56a; letter-spacing: 8px; }"
        "QFrame { background: #11131a; border: 1px solid #2b2e39; "
        "border-radius: 12px; }"
        "QLabel#label { color: #8d93a3; }"
        "QLabel#value { color: #f2ede4; }"
        "QLabel#message { color: #bfc5d2; }"
    )

    root = QVBoxLayout(window)
    root.setContentsMargins(42, 28, 42, 28)
    root.setSpacing(10)

    title = QLabel(initial.boot.title)
    title.setObjectName("title")
    title.setAlignment(Qt.AlignCenter)
    title.setFont(QFont("Sans Serif", 28, QFont.Light))
    root.addWidget(title)

    subtitle = QLabel(initial.boot.subtitle)
    subtitle.setAlignment(Qt.AlignCenter)
    subtitle.setFont(QFont("Sans Serif", 11))
    root.addWidget(subtitle)

    panel = QFrame()
    panel_layout = QGridLayout(panel)
    panel_layout.setContentsMargins(28, 20, 28, 20)
    panel_layout.setHorizontalSpacing(28)
    panel_layout.setVerticalSpacing(7)

    value_labels = {}
    for row_index, (label_text, value_text) in enumerate(initial.rows()):
        label = QLabel(label_text)
        label.setObjectName("label")
        label.setTextFormat(Qt.PlainText)
        label.setFont(QFont("Monospace", 12))

        value = QLabel(value_text)
        value.setObjectName("value")
        value.setTextFormat(Qt.PlainText)
        value.setFont(QFont("Monospace", 12))
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        value_labels[label_text] = value
        panel_layout.addWidget(label, row_index, 0)
        panel_layout.addWidget(value, row_index, 1)

    panel_layout.setColumnStretch(0, 1)
    panel_layout.setColumnStretch(1, 1)
    root.addWidget(panel)

    message = QLabel(initial.message)
    message.setObjectName("message")
    message.setTextFormat(Qt.PlainText)
    message.setAlignment(Qt.AlignCenter)
    message.setWordWrap(True)
    message.setFont(QFont("Sans Serif", 11))
    root.addWidget(message)

    def refresh() -> None:
        frame = loader()
        title.setText(frame.boot.title)
        subtitle.setText(frame.boot.subtitle)
        for label_text, value_text in frame.rows():
            value_labels[label_text].setText(value_text)
        message.setText(frame.message)

    timer = None
    if refresh_ms > 0:
        timer = QTimer(window)
        timer.timeout.connect(refresh)
        timer.start(refresh_ms)
        window._velvet_refresh_timer = timer

    window.show()
    return app.exec_()


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return run_live_window(
        args.snapshot,
        args.body_snapshot,
        args.refresh_ms,
    )


if __name__ == "__main__":
    raise SystemExit(main())
