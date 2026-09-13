#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Launch the read-only Velour Library Reader without the full Founder router."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from velvet_interface.catalog_library_preview import CatalogLibraryPreviewProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview Velour's read-only library surface")
    parser.add_argument(
        "--library-root",
        type=Path,
        default=Path(os.environ.get("VELVET_LIBRARY_ROOT", "/srv/velvet")),
        help="configured local vault/library root; default: VELVET_LIBRARY_ROOT or /srv/velvet",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="optional catalog/items.jsonl override; defaults beneath the selected library root",
    )
    parser.add_argument(
        "--background",
        type=Path,
        default=Path("examples/assets/workspace_scroll.png"),
        help="workspace background image",
    )
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fullscreen", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        from PyQt5.QtWidgets import QApplication
        from velvet_interface.surfaces.pyqt.library_reader_widget import QtLibraryReaderWidget
    except ImportError as exc:
        print("PyQt5 is required: pip install 'velvet-interface[qt]'", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    app = QApplication(sys.argv)
    widget = QtLibraryReaderWidget(
        provider=CatalogLibraryPreviewProvider(
            args.library_root,
            catalog_path=args.catalog,
        ),
        target_size=(args.width, args.height),
        background_path=args.background,
    )
    widget.setWindowTitle("Velour Library Reader Preview")
    if args.fullscreen:
        widget.showFullScreen()
    else:
        widget.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
