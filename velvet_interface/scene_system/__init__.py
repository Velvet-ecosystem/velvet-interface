# SPDX-License-Identifier: GPL-3.0-only
"""Image-first scene, layout, scaling, and authoring contracts."""

from velvet_interface.scene_system.authoring import SurfaceLayoutAuthoringSession
from velvet_interface.scene_system.image_scene import ImageScene
from velvet_interface.scene_system.regions import PolygonRegion, RegionManager
from velvet_interface.scene_system.scaling import SceneScaler
from velvet_interface.scene_system.surface_manifest import (
    SURFACE_MANIFEST_SCHEMA,
    BackgroundAsset,
    PressPoint,
    SurfaceManifest,
    SurfaceManifestError,
    SurfaceManifestLoader,
    WidgetPlacement,
)
from velvet_interface.scene_system.transitions import (
    Transition,
    TransitionManager,
    TransitionType,
)
from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader

__all__ = [
    "YAMLSceneLoader",
    "SurfaceManifestLoader",
    "SurfaceManifest",
    "SurfaceManifestError",
    "SURFACE_MANIFEST_SCHEMA",
    "BackgroundAsset",
    "PressPoint",
    "WidgetPlacement",
    "SurfaceLayoutAuthoringSession",
    "PolygonRegion",
    "RegionManager",
    "SceneScaler",
    "Transition",
    "TransitionType",
    "TransitionManager",
    "ImageScene",
]
