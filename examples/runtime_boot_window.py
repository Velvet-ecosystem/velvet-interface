#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Minimal visible boot window for a Runtime snapshot."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from velvet_interface.boot_status import BootStatusViewModel, load_boot_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Display Velvet Runtime boot status")
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path(os.environ.get("VELVET_BOOT_SNAPSHOT_PATH", ".velvet-dev/first-boot-snapshot.json")),
        help="path to the bounded Runtime boot snapshot JSON",
    )
    return parser


def run_window(model: BootStatusViewModel) -> int:
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import QApplication, QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget
    except ImportError as exc:
        print("PyQt5 is required: pip install velvet-interface[qt]", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Velvet Founder Runtime")
    window.resize(800, 480)
    window.setStyleSheet(
        "QWidget { background: #07080c; color: #e8e3db; }"
        "QLabel#title { color: #d8b56a; letter-spacing: 8px; }"
        "QFrame { background: #11131a; border: 1px solid #2b2e39; border-radius: 12px; }"
        "QLabel#label { color: #8d93a3; }"
        "QLabel#value { color: #f2ede4; }"
        "QLabel#message { color: #bfc5d2; }"
    )

    root = QVBoxLayout(window)
    root.setContentsMargins(42, 32, 42, 32)
    root.setSpacing(12)

    title = QLabel(model.title)
    title.setObjectName("title")
    title.setAlignment(Qt.AlignCenter)
    title.setFont(QFont("Sans Serif", 28, QFont.Light))
    root.addWidget(title)

    subtitle = QLabel(model.subtitle)
    subtitle.setAlignment(Qt.AlignCenter)
    subtitle.setFont(QFont("Sans Serif", 11))
    root.addWidget(subtitle)

    panel = QFrame()
    panel_layout = QGridLayout(panel)
    panel_layout.setContentsMargins(28, 22, 28, 22)
    panel_layout.setHorizontalSpacing(28)
    panel_layout.setVerticalSpacing(8)

    rows = (
        ("Continuity", model.continuity),
        ("Court", model.court),
        ("Runtime", model.runtime),
        ("Routes", model.routes),
        ("Physical Control", model.physical_control),
    )
    for row_index, (label_text, value_text) in enumerate(rows):
        label = QLabel(label_text)
        label.setObjectName("label")
        label.setTextFormat(Qt.PlainText)
        label.setFont(QFont("Monospace", 13))

        value = QLabel(value_text)
        value.setObjectName("value")
        value.setTextFormat(Qt.PlainText)
        value.setFont(QFont("Monospace", 13))
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        panel_layout.addWidget(label, row_index, 0)
        panel_layout.addWidget(value, row_index, 1)

    panel_layout.setColumnStretch(0, 1)
    panel_layout.setColumnStretch(1, 1)
    root.addWidget(panel)

    message = QLabel(model.message)
    message.setObjectName("message")
    message.setTextFormat(Qt.PlainText)
    message.setAlignment(Qt.AlignCenter)
    message.setWordWrap(True)
    message.setFont(QFont("Sans Serif", 12))
    root.addWidget(message)

    window.show()
    return app.exec_()


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    model = load_boot_snapshot(args.snapshot)
    return run_window(model)


if __name__ == "__main__":
    raise SystemExit(main())
