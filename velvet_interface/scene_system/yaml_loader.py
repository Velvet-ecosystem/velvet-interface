# SPDX-License-Identifier: GPL-3.0-only
"""YAML loading for image-first Velvet surface manifests."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from velvet_interface.scene_system.surface_manifest import (
    SurfaceManifest,
    SurfaceManifestLoader,
)

logger = logging.getLogger(__name__)


class YAMLSceneLoader:
    """Compatibility loader above the strict SurfaceManifest contract.

    New files should use ``velvet.interface.surface.v1`` with ``press_points``
    and normalized coordinates. The older ``regions`` form remains readable and
    is interpreted as base-resolution pixels.
    """

    def __init__(self) -> None:
        self._loader = SurfaceManifestLoader()

    def load_manifest(
        self, yaml_path: str, require_background: bool = False
    ) -> SurfaceManifest:
        path = Path(yaml_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError("Scene YAML not found: %s" % yaml_path)

        # SurfaceManifestLoader is deliberately strict. For the legacy regions
        # shape, insert the old pixel coordinate meaning before validation.
        import yaml

        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("Scene YAML root must be a mapping")
        if "press_points" not in document and isinstance(document.get("regions"), list):
            document = dict(document)
            legacy_regions = []
            for item in document["regions"]:
                if not isinstance(item, dict):
                    legacy_regions.append(item)
                    continue
                migrated = dict(item)
                migrated.setdefault("coordinate_space", "pixels")
                legacy_regions.append(migrated)
            document["regions"] = legacy_regions

        manifest = self._loader.from_mapping(
            document,
            source_path=path,
            require_background=require_background,
        )
        logger.info("Loaded surface manifest: %s from %s", manifest.name, path)
        return manifest

    def load(self, yaml_path: str, require_background: bool = False) -> Dict[str, Any]:
        """Load YAML and return the historical ImageScene mapping shape."""

        return self.load_manifest(
            yaml_path, require_background=require_background
        ).to_scene_data()

    def load_multiple(
        self, directory: str, require_background: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        path = Path(directory).expanduser().resolve()
        if not path.is_dir():
            raise ValueError("Not a directory: %s" % directory)

        scenes = {}  # type: Dict[str, Dict[str, Any]]
        for yaml_file in sorted(list(path.glob("*.yaml")) + list(path.glob("*.yml"))):
            try:
                scene_data = self.load(
                    str(yaml_file), require_background=require_background
                )
                scenes[scene_data["name"]] = scene_data
            except Exception as exc:
                logger.error("Failed to load %s: %s", yaml_file, exc)
        logger.info("Loaded %d scenes from %s", len(scenes), path)
        return scenes
