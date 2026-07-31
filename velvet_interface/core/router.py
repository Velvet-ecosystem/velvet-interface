# SPDX-License-Identifier: GPL-3.0-only
"""Scene routing and navigation management."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface

logger = logging.getLogger(__name__)


class Router:
    """Manage scene registration, lifecycle, rendering, and history."""

    def __init__(self, surface: Surface) -> None:
        self.surface = surface
        self._scenes = {}  # type: Dict[str, Scene]
        self._current_scene = None  # type: Optional[Scene]
        self._history = []  # type: List[str]
        self._max_history = 50

        bind_router = getattr(surface, "bind_router", None)
        if callable(bind_router):
            bind_router(self)

    def register_scene(self, scene: Scene) -> None:
        if scene.scene_id in self._scenes:
            logger.warning("Scene %s already registered, replacing", scene.scene_id)
        self._scenes[scene.scene_id] = scene
        logger.info("Registered scene: %s", scene.scene_id)

    def unregister_scene(self, scene_id: str) -> None:
        if scene_id in self._scenes:
            del self._scenes[scene_id]
            logger.info("Unregistered scene: %s", scene_id)

    def navigate(
        self,
        scene_id: str,
        context: Optional[Dict[str, Any]] = None,
        add_to_history: bool = True,
    ) -> bool:
        if scene_id not in self._scenes:
            logger.error("Scene not found: %s", scene_id)
            return False

        new_scene = self._scenes[scene_id]
        if self._current_scene is not None:
            logger.debug("Exiting scene: %s", self._current_scene.scene_id)
            self._current_scene.on_exit()
            self.surface.hide_scene(self._current_scene)
            if add_to_history:
                self._history.append(self._current_scene.scene_id)
                if len(self._history) > self._max_history:
                    self._history.pop(0)

        logger.info("Navigating to scene: %s", scene_id)
        new_scene.on_enter(context)
        self.surface.show_scene(new_scene)
        self._current_scene = new_scene
        return True

    def back(self) -> bool:
        if not self._history:
            logger.debug("No navigation history")
            return False
        previous_scene_id = self._history.pop()
        return self.navigate(previous_scene_id, add_to_history=False)

    def get_current_scene(self) -> Optional[Scene]:
        return self._current_scene

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        return self._scenes.get(scene_id)

    def list_scenes(self) -> List[str]:
        return list(self._scenes.keys())

    def clear_history(self) -> None:
        self._history.clear()
        logger.debug("Navigation history cleared")
