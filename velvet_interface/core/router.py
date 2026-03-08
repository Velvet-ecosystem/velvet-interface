# velvet_interface/core/router.py
"""
Scene routing and navigation management.

The Router manages scene transitions, navigation history,
and scene lifecycle coordination.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
import logging

from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface

logger = logging.getLogger(__name__)


class Router:
    """
    Scene navigation router.
    
    Manages scene registration, navigation, and lifecycle.
    Maintains navigation history for back/forward navigation.
    """
    
    def __init__(self, surface: Surface):
        """
        Initialize the router.
        
        Args:
            surface: The surface to render scenes on
        """
        self.surface = surface
        self._scenes: Dict[str, Scene] = {}
        self._current_scene: Optional[Scene] = None
        self._history: List[str] = []
        self._max_history = 50
    
    def register_scene(self, scene: Scene) -> None:
        """
        Register a scene with the router.
        
        Args:
            scene: Scene to register
        """
        if scene.scene_id in self._scenes:
            logger.warning(f"Scene {scene.scene_id} already registered, replacing")
        
        self._scenes[scene.scene_id] = scene
        logger.info(f"Registered scene: {scene.scene_id}")
    
    def unregister_scene(self, scene_id: str) -> None:
        """
        Unregister a scene from the router.
        
        Args:
            scene_id: ID of scene to unregister
        """
        if scene_id in self._scenes:
            del self._scenes[scene_id]
            logger.info(f"Unregistered scene: {scene_id}")
    
    def navigate(
        self, 
        scene_id: str, 
        context: Optional[Dict[str, Any]] = None,
        add_to_history: bool = True
    ) -> bool:
        """
        Navigate to a scene.
        
        Args:
            scene_id: ID of scene to navigate to
            context: Optional context data to pass to new scene
            add_to_history: Whether to add current scene to history
            
        Returns:
            True if navigation succeeded, False otherwise
        """
        if scene_id not in self._scenes:
            logger.error(f"Scene not found: {scene_id}")
            return False
        
        new_scene = self._scenes[scene_id]
        
        # Exit current scene
        if self._current_scene:
            logger.debug(f"Exiting scene: {self._current_scene.scene_id}")
            self._current_scene.on_exit()
            self.surface.hide_scene(self._current_scene)
            
            # Add to history
            if add_to_history:
                self._history.append(self._current_scene.scene_id)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
        
        # Enter new scene
        logger.info(f"Navigating to scene: {scene_id}")
        new_scene.on_enter(context)
        self.surface.show_scene(new_scene)
        self._current_scene = new_scene
        
        return True
    
    def back(self) -> bool:
        """
        Navigate back to previous scene in history.
        
        Returns:
            True if navigation succeeded, False if no history
        """
        if not self._history:
            logger.debug("No navigation history")
            return False
        
        previous_scene_id = self._history.pop()
        return self.navigate(previous_scene_id, add_to_history=False)
    
    def get_current_scene(self) -> Optional[Scene]:
        """
        Get the currently active scene.
        
        Returns:
            Current scene or None
        """
        return self._current_scene
    
    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """
        Get a registered scene by ID.
        
        Args:
            scene_id: Scene ID to retrieve
            
        Returns:
            Scene or None if not found
        """
        return self._scenes.get(scene_id)
    
    def list_scenes(self) -> List[str]:
        """
        List all registered scene IDs.
        
        Returns:
            List of scene IDs
        """
        return list(self._scenes.keys())
    
    def clear_history(self) -> None:
        """Clear navigation history."""
        self._history.clear()
        logger.debug("Navigation history cleared")
