# SPDX-License-Identifier: GPL-3.0-only
"""Allow-listed built-in widgets for image-first Founder surfaces."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional


def _env_true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _development_mode() -> bool:
    runtime_mode = os.environ.get("VELVET_RUNTIME_MODE", "").strip().lower()
    return _env_true("VELVET_INTERFACE_DEVELOPMENT") or runtime_mode.startswith("development")


def resolve_builtin_widget(
    widget_id: str,
    *,
    eleanor_executable: Optional[Path] = None,
    eleanor_project: Optional[Path] = None,
    modules_root: Optional[Path] = None,
    development_mode: Optional[bool] = None,
) -> Optional[Any]:
    """Return one trusted built-in QWidget for an exact allow-listed ID.

    Surface manifests cannot name Python modules or commands. They may only
    request IDs in this registry. Founder widgets are backed by read-only
    evidence seams; manifests never acquire hardware handles or authority.
    """

    allowed = {
        "climate_environment_status",
        "lighting_context_status",
        "forge_engineering_design",
        "forge_module_lab",
        "forge_test_bench",
    }
    if widget_id not in allowed:
        return None

    if widget_id in {"climate_environment_status", "lighting_context_status"}:
        body_snapshot = Path(
            os.environ.get("VELVET_BODY_SNAPSHOT_PATH", "/run/velvet/body-state.json")
        ).expanduser()
        if widget_id == "climate_environment_status":
            from velvet_interface.surfaces.pyqt.climate_status_widget import (
                QtClimateStatusWidget,
            )

            return QtClimateStatusWidget(body_snapshot)

        from velvet_interface.surfaces.pyqt.lighting_context_widget import (
            QtLightingContextWidget,
        )

        return QtLightingContextWidget(body_snapshot)

    from velvet_interface.eleanor_bridge import EleanorBridge
    from velvet_interface.forge_workspace_bridges import (
        EngineeringDesignBridge,
        ModuleLabBridge,
        TestBenchBridge,
    )
    from velvet_interface.surfaces.pyqt.forge_workspace_widget import (
        QtForgeWorkspaceWidget,
    )

    development = _development_mode() if development_mode is None else bool(development_mode)
    if widget_id == "forge_module_lab":
        resolved_modules_root = Path(
            modules_root
            if modules_root is not None
            else os.environ.get(
                "VELVET_MODULES_ROOT",
                str(Path.home() / "velvet/Modules"),
            )
        ).expanduser()
        bridge = ModuleLabBridge(resolved_modules_root)
        return QtForgeWorkspaceWidget(
            "module_lab",
            bridge.snapshot,
            development_mode=development,
        )

    executable = Path(
        eleanor_executable
        if eleanor_executable is not None
        else os.environ.get(
            "VELVET_ELEANOR_EXECUTABLE",
            str(Path.home() / "velvet/.venvs/eleanor/bin/eleanor-engineering"),
        )
    ).expanduser()
    project = Path(
        eleanor_project
        if eleanor_project is not None
        else os.environ.get(
            "VELVET_ELEANOR_PROJECT",
            str(
                Path.home()
                / "velvet/velvet-eleanor-engineering/projects/automotive-interface-io-v0/engineering-project.yaml"
            ),
        )
    ).expanduser()
    eleanor = EleanorBridge(executable, project)
    if widget_id == "forge_engineering_design":
        bridge = EngineeringDesignBridge(eleanor)
        workspace_id = "engineering_design"
    else:
        bridge = TestBenchBridge(eleanor)
        workspace_id = "test_bench"
    return QtForgeWorkspaceWidget(
        workspace_id,
        bridge.snapshot,
        development_mode=development,
    )
