# velvet_interface/scene_system/__init__.py
"""
Scene system for image-based, polygon-interactive scenes.

Provides YAML loading, polygon regions, automatic scaling, and transitions.
"""

from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader
from velvet_interface.scene_system.regions import PolygonRegion, RegionManager
from velvet_interface.scene_system.scaling import SceneScaler
from velvet_interface.scene_system.transitions import (
    Transition,
    TransitionType,
    TransitionManager
)
from velvet_interface.scene_system.image_scene import ImageScene

__all__ = [
    "YAMLSceneLoader",
    "PolygonRegion",
    "RegionManager",
    "SceneScaler",
    "Transition",
    "TransitionType",
    "TransitionManager",
    "ImageScene",
]
