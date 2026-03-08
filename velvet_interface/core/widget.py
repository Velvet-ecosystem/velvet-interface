# velvet_interface/core/widget.py
"""
Abstract widget interface for reusable UI components.

Widgets are reusable UI elements that can be embedded in scenes.
Like scenes, widgets are surface-agnostic and delegate rendering.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Widget(ABC):
    """
    Abstract base class for reusable UI widgets.
    
    Widgets are smaller, composable UI elements that can be embedded
    within scenes. Examples: status indicators, buttons, sliders, etc.
    
    Widgets follow the same surface-agnostic design as scenes.
    """
    
    def __init__(self, widget_id: str):
        """
        Initialize the widget.
        
        Args:
            widget_id: Unique identifier for this widget instance
        """
        self.widget_id = widget_id
        self._visible = True
        self._enabled = True
        self._state: Dict[str, Any] = {}
    
    @abstractmethod
    def render(self, surface: 'Surface', x: int, y: int) -> Any:
        """
        Render the widget on the given surface at a specific position.
        
        Args:
            surface: The surface to render on
            x: Horizontal position
            y: Vertical position
            
        Returns:
            Surface-specific render result
        """
        pass
    
    def on_update(self, data: Dict[str, Any]) -> None:
        """
        Called when widget state should be updated.
        
        Args:
            data: New state data
        """
        self._state.update(data)
    
    def show(self) -> None:
        """Make widget visible."""
        self._visible = True
    
    def hide(self) -> None:
        """Make widget invisible."""
        self._visible = False
    
    def enable(self) -> None:
        """Enable widget interactions."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable widget interactions."""
        self._enabled = False
    
    @property
    def is_visible(self) -> bool:
        """Check if widget is visible."""
        return self._visible
    
    @property
    def is_enabled(self) -> bool:
        """Check if widget is enabled."""
        return self._enabled
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve widget state value."""
        return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """Update widget state value."""
        self._state[key] = value
