# velvet_interface/core/surface.py
"""
Abstract surface interface for multi-backend rendering.

A Surface represents a rendering backend (Qt, web, mobile, etc.)
and provides primitive operations for displaying scenes.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class Surface(ABC):
    """
    Abstract base class for rendering surfaces.
    
    Surfaces implement the actual rendering logic for a specific platform
    (Qt, web, mobile, etc.) and provide primitive operations for displaying
    content.
    
    Scenes call Surface methods to render their content in a platform-agnostic way.
    """
    
    def __init__(self, surface_id: str):
        """
        Initialize the surface.
        
        Args:
            surface_id: Unique identifier for this surface (e.g., "qt", "web")
        """
        self.surface_id = surface_id
        self._properties: Dict[str, Any] = {}
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the surface backend.
        
        Called once before the surface is used for rendering.
        Use this to set up windowing systems, contexts, etc.
        """
        pass
    
    @abstractmethod
    def show_scene(self, scene: 'Scene') -> Any:
        """
        Display a scene on this surface.
        
        Args:
            scene: The scene to display
            
        Returns:
            Surface-specific display handle
        """
        pass
    
    @abstractmethod
    def hide_scene(self, scene: 'Scene') -> None:
        """
        Hide a scene from this surface.
        
        Args:
            scene: The scene to hide
        """
        pass
    
    @abstractmethod
    def show_text(
        self, 
        text: str, 
        x: int, 
        y: int, 
        font_size: int = 14,
        color: Optional[str] = None
    ) -> Any:
        """
        Display text at a specific position.
        
        Args:
            text: Text content to display
            x: Horizontal position
            y: Vertical position
            font_size: Text size in points
            color: Text color (platform-specific format)
            
        Returns:
            Surface-specific text widget/element
        """
        pass
    
    @abstractmethod
    def show_button(
        self,
        label: str,
        x: int,
        y: int,
        width: int,
        height: int,
        on_click: Optional[callable] = None
    ) -> Any:
        """
        Display a button at a specific position.
        
        Args:
            label: Button text
            x: Horizontal position
            y: Vertical position
            width: Button width
            height: Button height
            on_click: Callback when button is clicked
            
        Returns:
            Surface-specific button widget/element
        """
        pass
    
    @abstractmethod
    def show_image(
        self,
        image_path: str,
        x: int,
        y: int,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Any:
        """
        Display an image at a specific position.
        
        Args:
            image_path: Path to image file
            x: Horizontal position
            y: Vertical position
            width: Image width (None = original)
            height: Image height (None = original)
            
        Returns:
            Surface-specific image widget/element
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all content from the surface."""
        pass
    
    @abstractmethod
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get surface dimensions.
        
        Returns:
            (width, height) tuple
        """
        pass
    
    def set_property(self, key: str, value: Any) -> None:
        """Store surface-specific property."""
        self._properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Retrieve surface-specific property."""
        return self._properties.get(key, default)
