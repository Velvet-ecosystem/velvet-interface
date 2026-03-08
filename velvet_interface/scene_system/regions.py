# velvet_interface/scene_system/regions.py
"""
Polygon-based interaction regions.

Point-in-polygon detection and region metadata management.
"""

from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PolygonRegion:
    """
    A polygon-based interaction region.
    
    Supports point-in-polygon hit testing and action binding.
    """
    
    def __init__(
        self,
        name: str,
        polygon: List[Tuple[float, float]],
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize polygon region.
        
        Args:
            name: Region identifier
            polygon: List of (x, y) coordinates defining the polygon
            action: Action to trigger (e.g., "navigate:scene_name")
            metadata: Optional metadata (tooltip, sound, etc.)
        """
        self.name = name
        self.polygon = polygon
        self.action = action
        self.metadata = metadata or {}
        
        if len(polygon) < 3:
            raise ValueError(f"Polygon must have at least 3 points, got {len(polygon)}")
    
    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if point (x, y) is inside the polygon using ray casting.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if point is inside polygon
        """
        n = len(self.polygon)
        inside = False
        
        p1x, p1y = self.polygon[0]
        
        for i in range(1, n + 1):
            p2x, p2y = self.polygon[i % n]
            
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            
            p1x, p1y = p2x, p2y
        
        return inside
    
    def scale(self, scale_x: float, scale_y: float) -> 'PolygonRegion':
        """
        Create a scaled copy of this region.
        
        Args:
            scale_x: X scale factor
            scale_y: Y scale factor
            
        Returns:
            New PolygonRegion with scaled coordinates
        """
        scaled_polygon = [
            (x * scale_x, y * scale_y)
            for x, y in self.polygon
        ]
        
        return PolygonRegion(
            name=self.name,
            polygon=scaled_polygon,
            action=self.action,
            metadata=self.metadata.copy()
        )


class RegionManager:
    """
    Manage multiple polygon regions for hit testing.
    """
    
    def __init__(self):
        self.regions: List[PolygonRegion] = []
    
    def add_region(self, region: PolygonRegion) -> None:
        """Add a region to the manager."""
        self.regions.append(region)
        logger.debug(f"Added region: {region.name}")
    
    def remove_region(self, name: str) -> None:
        """Remove a region by name."""
        self.regions = [r for r in self.regions if r.name != name]
        logger.debug(f"Removed region: {name}")
    
    def find_region_at(self, x: float, y: float) -> Optional[PolygonRegion]:
        """
        Find the first region containing the point (x, y).
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            First region containing the point, or None
        """
        for region in self.regions:
            if region.contains_point(x, y):
                logger.debug(f"Hit region: {region.name} at ({x}, {y})")
                return region
        
        return None
    
    def find_all_regions_at(self, x: float, y: float) -> List[PolygonRegion]:
        """
        Find all regions containing the point (x, y).
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            List of regions containing the point
        """
        return [r for r in self.regions if r.contains_point(x, y)]
    
    def scale_all(self, scale_x: float, scale_y: float) -> None:
        """
        Scale all regions by the given factors.
        
        Args:
            scale_x: X scale factor
            scale_y: Y scale factor
        """
        self.regions = [r.scale(scale_x, scale_y) for r in self.regions]
        logger.debug(f"Scaled all regions by ({scale_x}, {scale_y})")
    
    def clear(self) -> None:
        """Remove all regions."""
        self.regions.clear()
        logger.debug("Cleared all regions")
