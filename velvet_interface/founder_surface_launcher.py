# SPDX-License-Identifier: GPL-3.0-only
"""Reusable full image-first Founder interface launcher."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from velvet_interface.core.router import Router
from velvet_interface.scene_system.camera_capture import FileCameraFrameProvider
from velvet_interface.scene_system.image_scene import ImageScene
from velvet_interface.scene_system.surface_workspace import (
    SurfacePromotionContext,
    SurfaceWorkspace,
)
from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader
from velvet_interface.scenes.surface_studio_scene import SurfaceStudioScene


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch Velvet Founder surfaces")
    parser.add_argument(
        "--surfaces",
        type=Path,
        default=Path("examples/surfaces"),
        help="active directory containing .yaml or .yml surface manifests",
    )
    parser.add_argument("--initial", default="founder_home")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument(
        "--surface-workspace",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_SURFACE_STUDIO_WORKSPACE",
                ".velvet-dev/surface-studio",
            )
        ),
        help="private draft workspace used by the on-device Surface Studio",
    )
    parser.add_argument(
        "--camera-frame-path",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_CAMERA_FRAME_PATH",
                "/run/velvet/camera/latest-frame.jpg",
            )
        ),
        help="atomically published current PNG/JPEG still for Surface Studio capture",
    )
    parser.add_argument(
        "--camera-source-id",
        default=os.environ.get("VELVET_CAMERA_SOURCE_ID", "camera.current_frame"),
    )
    parser.add_argument(
        "--camera-frame-max-age",
        type=float,
        default=float(os.environ.get("VELVET_CAMERA_FRAME_MAX_AGE", "3.0")),
        help="maximum age in seconds for a frame to count as current",
    )
    parser.add_argument(
        "--disable-surface-studio",
        action="store_true",
        help="do not register the trusted built-in Surface Studio scene",
    )
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


def _env_true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.width < 320 or args.height < 240:
        print("Founder surface dimensions are too small", file=sys.stderr)
        return 2
    if args.camera_frame_max_age <= 0:
        print("camera-frame-max-age must be positive", file=sys.stderr)
        return 2

    try:
        from PyQt5.QtGui import QKeySequence
        from PyQt5.QtWidgets import QApplication, QShortcut
    except ImportError as exc:
        print("PyQt5 is required: pip install 'velvet-interface[qt]'", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    from velvet_interface.surfaces.pyqt.founder_body_widget import (
        QtFounderBodyStatusWidget,
    )
    from velvet_interface.surfaces.pyqt.gnss_status_widget import QtGnssStatusWidget
    from velvet_interface.surfaces.pyqt.microphone_input_status_widget import (
        QtMicrophoneInputStatusWidget,
    )
    from velvet_interface.surfaces.pyqt.nfc_status_widget import QtNfcStatusWidget
    from velvet_interface.surfaces.pyqt.qt_surface import QtSurface
    from velvet_interface.surfaces.pyqt.vehicle_power_status_widget import (
        QtVehiclePowerStatusWidget,
    )

    surfaces_path = args.surfaces.expanduser().resolve()
    surfaces_path.mkdir(parents=True, exist_ok=True)
    scene_loader = YAMLSceneLoader()
    scene_documents = scene_loader.load_multiple(
        str(surfaces_path),
        require_background=True,
    )
    if not scene_documents and args.disable_surface_studio:
        print("No valid surface manifests found in %s" % surfaces_path, file=sys.stderr)
        return 2

    app = QApplication(sys.argv)

    def widget_provider(widget_id: str):
        if widget_id == "founder_body_status":
            return QtFounderBodyStatusWidget(
                boot_snapshot=args.boot_snapshot,
                body_snapshot=args.body_snapshot,
            )
        if widget_id == "gnss_status":
            return QtGnssStatusWidget(body_snapshot=args.body_snapshot)
        if widget_id == "vehicle_power_status":
            return QtVehiclePowerStatusWidget(body_snapshot=args.body_snapshot)
        if widget_id == "nfc_status":
            return QtNfcStatusWidget(body_snapshot=args.body_snapshot)
        if widget_id == "microphone_input_status":
            return QtMicrophoneInputStatusWidget(body_snapshot=args.body_snapshot)
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

    studio_scene = None
    if not args.disable_surface_studio:
        workspace = SurfaceWorkspace(
            workspace_root=args.surface_workspace,
            active_surface_dir=surfaces_path,
        )
        camera_frame_provider = FileCameraFrameProvider(
            frame_path=args.camera_frame_path,
            source_id=args.camera_source_id,
            max_age_seconds=args.camera_frame_max_age,
            max_bytes=workspace.max_asset_bytes,
        )

        def maintenance_access_provider() -> bool:
            return _env_true("VELVET_MAINTENANCE_UNLOCKED")

        def promotion_context_provider() -> SurfacePromotionContext:
            return SurfacePromotionContext(
                maintenance_unlocked=maintenance_access_provider(),
                owner_present=_env_true("VELVET_OWNER_PRESENT"),
                vehicle_stationary=_env_true("VELVET_VEHICLE_STATIONARY"),
                physical_control_disabled=_env_true(
                    "VELVET_PHYSICAL_CONTROL_DISABLED"
                ),
                receipt_id=str(uuid4()),
            )

        def reload_promoted_surface(result) -> None:
            document = scene_loader.load(
                str(result.manifest_path),
                require_background=True,
            )
            surface.invalidate_scene(result.surface_name)
            router.register_scene(ImageScene(document))
            router.navigate(result.surface_name)

        studio_scene = SurfaceStudioScene(
            workspace=workspace,
            maintenance_access_provider=maintenance_access_provider,
            promotion_context_provider=promotion_context_provider,
            camera_frame_provider=camera_frame_provider,
            on_promoted=reload_promoted_surface,
        )
        studio_scene.bind_router(router)
        router.register_scene(studio_scene)

    initial = args.initial
    if initial not in router.list_scenes():
        non_studio = [name for name in sorted(router.list_scenes()) if name != "surface_studio"]
        initial = non_studio[0] if non_studio else "surface_studio"
    if not router.navigate(initial):
        print("Unable to open initial surface: %s" % initial, file=sys.stderr)
        return 2

    window = surface.get_container()
    window.setWindowTitle("Velvet Founder Interface")

    if studio_scene is not None:
        studio_shortcut = QShortcut(QKeySequence("Ctrl+Alt+S"), window)

        def open_studio() -> None:
            if _env_true("VELVET_MAINTENANCE_UNLOCKED"):
                router.navigate("surface_studio")

        studio_shortcut.activated.connect(open_studio)
        window._velvet_surface_studio_shortcut = studio_shortcut  # type: ignore[attr-defined]

    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()
    return app.exec_()
