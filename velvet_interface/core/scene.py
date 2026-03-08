# velvet_interface/core/scene.py
"""
Abstract scene interface for multi-surface rendering.

A Scene represents a logical view or screen in the application.
Scenes are surface-agnostic and delegate rendering to Surface implementations.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable


class Scene(ABC):
    """
    Abstract base class for all scenes.
    
    Scenes manage application state and logic but do not directly render.
    Rendering is delegated to Surface implementations via the render() method.
    
    Lifecycle:
        1. __init__() - Scene is created
        2. on_enter() - Scene becomes active
        3. render() - Scene is rendered on a surface (may be called multiple times)
        4. on_exit() - Scene is deactivated
    """
    
    def __init__(self, scene_id: str):
        """
        Initialize the scene.
        
        Args:
            scene_id: Unique identifier for this scene
        """
        self.scene_id = scene_id
        self._active = False
        self._data: Dict[str, Any] = {}
        self._event_handlers: Dict[str, Callable] = {}
    
    @abstractmethod
    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Called when the scene becomes active.
        
        Use this to initialize scene state, load data, or subscribe to events.
        
        Args:
            context: Optional context data passed from the previous scene
        """
        self._active = True
    
    @abstractmethod
    def on_exit(self) -> None:
        """
        Called when the scene is deactivated.
        
        Use this to save state, unsubscribe from events, or perform cleanup.
        """
        self._active = False
    
    @abstractmethod
    def render(self, surface: 'Surface') -> Any:
        """
        Render the scene on the given surface.
        
        This method should use the Surface API to display scene content.
        The return type depends on the surface implementation.
        
        Args:
            surface: The surface to render on
            
        Returns:
            Surface-specific render result (e.g., QWidget for Qt, HTML for web)
        """
        pass
    
    def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Handle an event for this scene.
        
        Args:
            event_type: Type of event (e.g., "button.clicked", "data.updated")
            data: Event payload
        """
        handler = self._event_handlers.get(event_type)
        if handler:
            handler(data)
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Callback function (data: Dict[str, Any]) -> None
        """
        self._event_handlers[event_type] = handler
    
    def set_data(self, key: str, value: Any) -> None:
        """Store scene-specific data."""
        self._data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Retrieve scene-specific data."""
        return self._data.get(key, default)
    
    @property
    def is_active(self) -> bool:
        """Check if scene is currently active."""
        return self._active
