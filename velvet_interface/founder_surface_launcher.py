# SPDX-License-Identifier: GPL-3.0-only
"""Reusable full image-first Founder interface launcher."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from velvet_interface.core.router import Router
from velvet_interface.scene_system.camera_capture import FileCameraFrameProvider
from velvet_interface.scene_system.image_scene import ImageScene
from velvet_interface.scene_system.surface_set import SurfaceSetLoader
from velvet_interface.scene_system.surface_workspace import (
    SurfacePromotionContext,
    SurfaceWorkspace,
)
from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader
from velvet_interface.scenes.surface_studio_scene import SurfaceStudioScene


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch Velvet Founder surfaces")
    surface_set_env = os.environ.get("VELVET_SURFACE_SET_PATH", "").strip()
    parser.add_argument(
        "--surface-set",
        type=Path,
        default=Path(surface_set_env) if surface_set_env else None,
        help=(
            "runtime surface-set binding; may also be supplied with "
            "VELVET_SURFACE_SET_PATH"
        ),
    )
    parser.add_argument(
        "--surfaces",
        type=Path,
        default=None,
        help=(
            "override active directory containing .yaml or .yml surface manifests; "
            "defaults to the selected surface set or examples/surfaces"
        ),
    )
    parser.add_argument(
        "--initial",
        default=None,
        help=(
            "override initial scene; defaults to the selected surface set or "
            "founder_home"
        ),
    )
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
        "--conversation-socket",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_CONVERSATION_SOCKET_PATH",
                "/run/velvet/conversation.sock",
            )
        ),
        help="local Runtime Unix socket used by the written conversation scene",
    )
    parser.add_argument(
        "--disable-written-conversation",
        action="store_true",
        help="do not register the trusted built-in written conversation scene",
    )
    parser.add_argument(
        "--distributed-lifecycle-journal",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_DISTRIBUTED_LIFECYCLE_JOURNAL",
                "/var/lib/velvet-runtime/distributed-lifecycle.jsonl",
            )
        ),
        help="read-only Runtime node heartbeat journal used by Maintenance body status",
    )
    parser.add_argument(
        "--body-resource-socket",
        type=Path,
        default=Path(
            os.environ.get(
                "VELVET_BODY_RESOURCE_SOCKET_PATH",
                "/run/velvet/body-resources.sock",
            )
        ),
        help="read-only local Runtime body-resource socket",
    )
    parser.add_argument(
        "--node-heartbeat-max-age",
        type=float,
        default=float(os.environ.get("VELVET_NODE_HEARTBEAT_MAX_AGE", "20.0")),
        help="seconds before a Maintenance node heartbeat is shown as stale",
    )
    parser.add_argument(
        "--local-node-id",
        default=os.environ.get("VELVET_LOCAL_NODE_ID", "founder"),
        help="local body host ID displayed first in the Maintenance node list",
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


def _resolve_surface_selection(args: argparse.Namespace) -> Tuple[Path, str]:
    """Resolve presentation content without coupling the launcher to a body type."""

    bound_directory = None
    bound_initial = None
    if args.surface_set is not None:
        binding = SurfaceSetLoader().load(
            str(args.surface_set),
            require_directory=True,
        )
        bound_directory = binding.surface_path
        bound_initial = binding.initial_scene

    surfaces_path = (
        args.surfaces.expanduser().resolve()
        if args.surfaces is not None
        else (
            bound_directory
            if bound_directory is not None
            else Path("examples/surfaces").expanduser().resolve()
        )
    )
    initial = args.initial or bound_initial or "founder_home"
    return surfaces_path, initial


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.width < 320 or args.height < 240:
        print("Founder surface dimensions are too small", file=sys.stderr)
        return 2
    if args.camera_frame_max_age <= 0:
        print("camera-frame-max-age must be positive", file=sys.stderr)
        return 2
    if args.node_heartbeat_max_age <= 0:
        print("node-heartbeat-max-age must be positive", file=sys.stderr)
        return 2
    if not str(args.local_node_id).strip():
        print("local-node-id must be non-empty", file=sys.stderr)
        return 2

    try:
        surfaces_path, requested_initial = _resolve_surface_selection(args)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print("Unable to resolve surface set: %s" % exc, file=sys.stderr)
        return 2

    try:
        from PyQt5.QtGui import QKeySequence
        from PyQt5.QtWidgets import QApplication, QShortcut
    except ImportError as exc:
        print("PyQt5 is required: pip install 'velvet-interface[qt]'", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    from velvet_interface.body_nodes_live_status import load_body_nodes_status
    from velvet_interface.surfaces.pyqt.body_nodes_widget import QtBodyNodesTouchList
    from velvet_interface.surfaces.pyqt.founder_body_widget import (
        QtFounderBodyStatusWidget,
    )
    from velvet_interface.surfaces.pyqt.gnss_status_widget import QtGnssStatusWidget
    from velvet_interface.surfaces.pyqt.microphone_input_status_widget import (
        QtMicrophoneInputStatusWidget,
    )
    from velvet_interface.surfaces.pyqt.nfc_status_widget import QtNfcStatusWidget
    from velvet_interface.surfaces.pyqt.qt_surface import QtSurface
    from velvet_interface.surfaces.pyqt.seat_presence_status_widget import (
        QtSeatPresenceStatusWidget,
    )
    from velvet_interface.surfaces.pyqt.vehicle_power_status_widget import (
        QtVehiclePowerStatusWidget,
    )

    surfaces_path.mkdir(parents=True, exist_ok=True)
    scene_loader = YAMLSceneLoader()
    scene_documents = scene_loader.load_multiple(
        str(surfaces_path),
        require_background=True,
    )
    if (
        not scene_documents
        and args.disable_surface_studio
        and args.disable_written_conversation
    ):
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
        if widget_id == "seat_presence_status":
            return QtSeatPresenceStatusWidget(body_snapshot=args.body_snapshot)
        return None

    def coordinate_sink(scene_id: str, point) -> None:
        if args.placement_debug:
            print("%s point: [%.6f, %.6f]" % (scene_id, point[0], point[1]))

    resource_client = None
    try:
        from services.body_resource_transport import UnixBodyResourceClient

        resource_client = UnixBodyResourceClient(
            args.body_resource_socket,
            timeout_seconds=0.5,
            retries=0,
        )
    except (ImportError, ValueError):
        resource_client = None

    def body_nodes_status_provider():
        snapshot_provider = None
        if resource_client is not None:

            def snapshot_provider(now: float):
                return resource_client.capacity_snapshot(now=now)

        return load_body_nodes_status(
            args.distributed_lifecycle_journal,
            resource_snapshot_provider=snapshot_provider,
            max_heartbeat_age_seconds=args.node_heartbeat_max_age,
            local_node_id=str(args.local_node_id).strip(),
        )

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

    body_nodes_touch_list = None

    def open_body_nodes_touch_list(_event_data) -> None:
        nonlocal body_nodes_touch_list
        if body_nodes_touch_list is None:
            body_nodes_touch_list = QtBodyNodesTouchList(
                status_provider=body_nodes_status_provider,
                parent=surface.get_container(),
            )
        body_nodes_touch_list.present(
            surface_width=args.width,
            surface_height=args.height,
        )

    for name in sorted(scene_documents):
        scene = ImageScene(scene_documents[name])
        if name == "vehicle":
            scene.register_event_handler(
                "vehicle.electronics.selected",
                open_body_nodes_touch_list,
            )
        router.register_scene(scene)

    conversation_scene = None
    conversation_access_provider = None
    if not args.disable_written_conversation:
        try:
            from services.conversation_unix_transport import UnixConversationClient
            from velvet_interface.scenes.written_conversation_scene import (
                WrittenConversationScene,
            )

            conversation_client = UnixConversationClient(
                args.conversation_socket,
                timeout_seconds=2.0,
                retries=0,
            )

            def conversation_access_provider() -> bool:
                return _env_true("VELVET_OWNER_PRESENT") or _env_true(
                    "VELVET_MAINTENANCE_UNLOCKED"
                )

            def submit_written_turn(text: str):
                return conversation_client.submit(text, modality="text")

            conversation_scene = WrittenConversationScene(
                submit_turn=submit_written_turn,
                access_provider=conversation_access_provider,
            )
            conversation_scene.bind_router(router)
            router.register_scene(conversation_scene)
        except (ImportError, ValueError) as exc:
            print(
                "Written conversation surface unavailable: %s" % exc,
                file=sys.stderr,
            )

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
            promoted_scene = ImageScene(document)
            if result.surface_name == "vehicle":
                promoted_scene.register_event_handler(
                    "vehicle.electronics.selected",
                    open_body_nodes_touch_list,
                )
            router.register_scene(promoted_scene)
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

    initial = requested_initial
    if initial not in router.list_scenes():
        built_in_tools = {"surface_studio", "written_conversation"}
        ordinary = [
            name for name in sorted(router.list_scenes()) if name not in built_in_tools
        ]
        if ordinary:
            initial = ordinary[0]
        elif studio_scene is not None:
            initial = "surface_studio"
        else:
            initial = "written_conversation"
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

    if conversation_scene is not None:
        conversation_shortcut = QShortcut(QKeySequence("Ctrl+Alt+C"), window)

        def open_written_conversation() -> None:
            router.navigate("written_conversation")

        conversation_shortcut.activated.connect(open_written_conversation)
        window._velvet_written_conversation_shortcut = conversation_shortcut  # type: ignore[attr-defined]

    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()
    return app.exec_()
