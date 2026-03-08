# velvet_interface/scene_system/scaling.py
"""
Scene scaling utilities.

Automatic scaling of scenes, images, and polygons across different screen sizes.
"""

from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class SceneScaler:
    """
    Handle automatic scaling of scene elements.
    
    Scales from a base resolution to a target resolution while
    maintaining aspect ratio or stretching as needed.
    """
    
    DEFAULT_BASE_RESOLUTION = (1280, 720)
    
    def __init__(
        self,
        base_resolution: Tuple[int, int] = DEFAULT_BASE_RESOLUTION,
        target_resolution: Tuple[int, int] = DEFAULT_BASE_RESOLUTION,
        maintain_aspect_ratio: bool = False
    ):
        """
        Initialize scene scaler.
        
        Args:
            base_resolution: Base scene resolution (width, height)
            target_resolution: Target display resolution
            maintain_aspect_ratio: If True, use letterboxing/pillarboxing
        """
        self.base_width, self.base_height = base_resolution
        self.target_width, self.target_height = target_resolution
        self.maintain_aspect_ratio = maintain_aspect_ratio
        
        self._calculate_scale_factors()
    
    def _calculate_scale_factors(self) -> None:
        """Calculate X and Y scale factors."""
        if self.maintain_aspect_ratio:
            # Use uniform scaling (smaller of the two factors)
            scale = min(
                self.target_width / self.base_width,
                self.target_height / self.base_height
            )
            self.scale_x = scale
            self.scale_y = scale
            
            # Calculate letterbox/pillarbox offsets
            scaled_width = self.base_width * scale
            scaled_height = self.base_height * scale
            
            self.offset_x = (self.target_width - scaled_width) / 2
            self.offset_y = (self.target_height - scaled_height) / 2
        else:
            # Independent X/Y scaling (stretch to fit)
            self.scale_x = self.target_width / self.base_width
            self.scale_y = self.target_height / self.base_height
            self.offset_x = 0
            self.offset_y = 0
        
        logger.debug(
            f"Scale factors: x={self.scale_x:.2f}, y={self.scale_y:.2f}, "
            f"offset=({self.offset_x}, {self.offset_y})"
        )
    
    def scale_point(self, x: float, y: float) -> Tuple[float, float]:
        """
        Scale a point from base to target resolution.
        
        Args:
            x: X coordinate in base resolution
            y: Y coordinate in base resolution
            
        Returns:
            (x, y) in target resolution
        """
        return (
            x * self.scale_x + self.offset_x,
            y * self.scale_y + self.offset_y
        )
    
    def unscale_point(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert a point from target back to base resolution.
        
        Useful for hit testing: convert click coordinates back to base space.
        
        Args:
            x: X coordinate in target resolution
            y: Y coordinate in target resolution
            
        Returns:
            (x, y) in base resolution
        """
        return (
            (x - self.offset_x) / self.scale_x,
            (y - self.offset_y) / self.scale_y
        )
    
    def scale_size(self, width: float, height: float) -> Tuple[float, float]:
        """
        Scale a size (width, height) from base to target resolution.
        
        Args:
            width: Width in base resolution
            height: Height in base resolution
            
        Returns:
            (width, height) in target resolution
        """
        return (
            width * self.scale_x,
            height * self.scale_y
        )
    
    def get_scaled_dimensions(self) -> Tuple[int, int]:
        """
        Get the scaled scene dimensions.
        
        Returns:
            (width, height) of scaled scene
        """
        if self.maintain_aspect_ratio:
            return (
                int(self.base_width * self.scale_x),
                int(self.base_height * self.scale_y)
            )
        else:
            return (self.target_width, self.target_height)
    
    def get_letterbox_rect(self) -> Tuple[int, int, int, int]:
        """
        Get the rectangle for the scaled scene within the target.
        
        Returns:
            (x, y, width, height) of the scene area
        """
        width, height = self.get_scaled_dimensions()
        return (
            int(self.offset_x),
            int(self.offset_y),
            width,
            height
        )
