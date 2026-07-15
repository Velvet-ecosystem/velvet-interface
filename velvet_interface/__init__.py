# velvet_interface/__init__.py
"""Velvet Interface Framework."""

__version__ = "0.2.0"

from velvet_interface.core import Scene, Surface, Widget, Router
from velvet_interface.route_request import SceneRouteRequest, build_scene_route_request
from velvet_interface.core.ghost_can_panel import render_ghost_can_text, view_model_from_ghost_can_event

__all__ = [
    "Scene", "Surface", "Widget", "Router", "SceneRouteRequest",
    "build_scene_route_request", "render_ghost_can_text", "view_model_from_ghost_can_event",
]
