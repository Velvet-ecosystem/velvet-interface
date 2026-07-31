#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Launch full image-first Founder interface surfaces.

This is the bridge from the rectangular Founder proof window to authored Velvet
screens. It loads all surface manifests in a directory, registers them with the
normal Router, places only explicitly registered widgets, and keeps physical
control disabled unless the separate Runtime authority path says otherwise.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from velvet_interface.core.router import Router
from velvet_interface.scene_system.image_scene import ImageScene
from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch Velvet Founder surfaces")
    parser.add_argument(
        "--surfaces",
        type=Path,
        default=Path("examples/surfaces"),
        help="directory containing .yaml or .yml surface manifests",
    )
    parser.add_argument("--initial", default="founder_home")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument(
        "--boot-snapshot",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_BOOT_SNAPSHOT_PATH",
                ".velvet-dev/first-boot-snapshot.json",
            )
        ),
    )
    parser.add_argument(
        "--body-snapshot",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_BODY_SNAPSHOT_PATH",
                "/run/velvet/body-state.json",
            )
        ),
    )
    parser.add_argument(
        "--presentation-mode",
        choices=("owner", "guest", "service", "silent", "emergency"),
        default="owner",
    )
    parser.add_argument("--placement-debug", action="store_true")
    parser.add_argument("--fullscreen", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.width < 320 or args.height < 240:
        print("Founder surface dimensions are too small", file=sys.stderr)
        return 2

    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError as exc:
        print("PyQt5 is required: pip install 'velvet-interface[qt]'", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    from velvet_interface.surfaces.pyqt.founder_body_widget import (
        QtFounderBodyStatusWidget,
    )
    from velvet_interface.surfaces.pyqt.qt_surface import QtSurface

    surfaces_path = args.surfaces.expanduser().resolve()
    scene_documents = YAMLSceneLoader().load_multiple(
        str(surfaces_path),
        require_background=True,
    )
    if not scene_documents:
        print("No valid surface manifests found in %s" % surfaces_path, file=sys.stderr)
        return 2

    app = QApplication(sys.argv)

    def widget_provider(widget_id: str):
        if widget_id == "founder_body_status":
            return QtFounderBodyStatusWidget(
                boot_snapshot=args.boot_snapshot,
                body_snapshot=args.body_snapshot,
            )
        # Unknown IDs remain absent. Surface YAML never dynamically imports code.
        return None

    def coordinate_sink(scene_id: str, point) -> None:
        if args.placement_debug:
            print("%s point: [%.6f, %.6f]" % (scene_id, point[0], point[1]))

    surface = QtSurface(
        width=args.width,
        height=args.height,
        widget_provider=widget_provider,
        presentation_mode=args.presentation_mode,
        placement_debug=args.placement_debug,
        coordinate_sink=coordinate_sink,
    )
    surface.initialize()
    router = Router(surface)
    for name in sorted(scene_documents):
        router.register_scene(ImageScene(scene_documents[name]))

    initial = args.initial
    if initial not in router.list_scenes():
        initial = sorted(router.list_scenes())[0]
    if not router.navigate(initial):
        print("Unable to open initial surface: %s" % initial, file=sys.stderr)
        return 2

    window = surface.get_container()
    window.setWindowTitle("Velvet Founder Interface")
    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
