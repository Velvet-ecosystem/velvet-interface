# velvet_interface/scene_system/image_scene.py
"""
Image-based scene with polygon regions.

A scene implementation that uses a background image with
clickable polygon regions.
"""

from typing import Dict, Any, Optional, Tuple
import logging

from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface
from velvet_interface.scene_system.regions import PolygonRegion, RegionManager
from velvet_interface.scene_system.scaling import SceneScaler
from velvet_interface.scene_system.transitions import Transition, TransitionManager

logger = logging.getLogger(__name__)


class ImageScene(Scene):
    """
    Image-based scene with polygon interaction regions.
    
    Supports:
    - Background image
    - Polygon regions for interactions
    - Automatic scaling
    - Transitions
    """
    
    def __init__(self, scene_data: Dict[str, Any]):
        """
        Initialize image scene from YAML data.
        
        Args:
            scene_data: Scene definition dict from YAML
        """
        super().__init__(scene_data['name'])
        
        self.scene_data = scene_data
        self.background_path = scene_data.get('background')
        
        # Base resolution for scaling
        base_res = scene_data.get('base_resolution', [1280, 720])
        self.base_resolution = tuple(base_res)
        
        # Region manager
        self.region_manager = RegionManager()
        self._load_regions()
        
        # Scaler (will be set when surface dimensions known)
        self.scaler: Optional[SceneScaler] = None
        
        # Transition config
        self.enter_transition = scene_data.get('transitions', {}).get('enter', 'none')
        self.exit_transition = scene_data.get('transitions', {}).get('exit', 'none')
    
    def _load_regions(self) -> None:
        """Load polygon regions from scene data."""
        for region_data in self.scene_data.get('regions', []):
            region = PolygonRegion(
                name=region_data['name'],
                polygon=[tuple(p) for p in region_data['polygon']],
                action=region_data['action'],
                metadata=region_data.get('metadata', {})
            )
            self.region_manager.add_region(region)
    
    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Called when scene becomes active."""
        super().on_enter(context)
        logger.info(f"Image scene entered: {self.scene_id}")
    
    def on_exit(self) -> None:
        """Called when scene is deactivated."""
        super().on_exit()
        logger.info(f"Image scene exited: {self.scene_id}")
    
    def setup_scaling(self, target_resolution: Tuple[int, int]) -> None:
        """
        Set up scaling for target resolution.
        
        Args:
            target_resolution: (width, height) of display
        """
        self.scaler = SceneScaler(
            base_resolution=self.base_resolution,
            target_resolution=target_resolution,
            maintain_aspect_ratio=False  # Stretch to fit by default
        )
        
        # Scale all regions
        self.region_manager.scale_all(
            self.scaler.scale_x,
            self.scaler.scale_y
        )
        
        logger.debug(
            f"Scene scaling set up: {self.base_resolution} -> {target_resolution}"
        )
    
    def handle_click(self, x: float, y: float) -> Optional[str]:
        """
        Handle click at (x, y) in target coordinates.
        
        Args:
            x: X coordinate (target resolution)
            y: Y coordinate (target resolution)
            
        Returns:
            Action string if region hit, None otherwise
        """
        if not self.scaler:
            logger.warning("Scaler not set up, using raw coordinates")
            base_x, base_y = x, y
        else:
            base_x, base_y = self.scaler.unscale_point(x, y)
        
        region = self.region_manager.find_region_at(base_x, base_y)
        
        if region:
            logger.info(f"Region clicked: {region.name} -> {region.action}")
            return region.action
        
        return None
    
    def render(self, surface: Surface) -> Any:
        """
        Render scene on surface.
        
        Surface implementations should:
        1. Call setup_scaling() with their dimensions
        2. Display background image (scaled)
        3. Set up click handling via handle_click()
        
        Args:
            surface: Surface to render on
            
        Returns:
            Surface-specific widget/container
        """
        # This is overridden by surface-specific scene adapters
        raise NotImplementedError(
            "ImageScene.render() should be called via surface adapter"
        )
