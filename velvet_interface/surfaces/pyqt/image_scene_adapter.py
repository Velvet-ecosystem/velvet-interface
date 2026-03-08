# velvet_interface/surfaces/pyqt/image_scene_adapter.py
"""
Qt adapter for ImageScene.

Renders image-based scenes with polygon regions in PyQt5.
"""

from typing import Any, Optional
import logging

try:
    from PyQt5.QtWidgets import QWidget, QLabel
    from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
    from PyQt5.QtCore import Qt, QRect
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from velvet_interface.scene_system.image_scene import ImageScene
from velvet_interface.core.surface import Surface

logger = logging.getLogger(__name__)


class QtImageSceneWidget(QWidget):
    """
    Qt widget for rendering ImageScene.
    
    Displays background image and handles click events on polygon regions.
    """
    
    def __init__(self, scene: ImageScene, surface: Surface, router=None):
        """
        Initialize Qt image scene widget.
        
        Args:
            scene: ImageScene to render
            surface: Qt surface
            router: Optional router for navigation
        """
        super().__init__()
        
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 required for Qt image scene adapter")
        
        self.scene = scene
        self.surface = surface
        self.router = router
        
        # Set up scaling for this surface
        target_width, target_height = surface.get_dimensions()
        scene.setup_scaling((target_width, target_height))
        
        # Set widget size
        self.setFixedSize(target_width, target_height)
        
        # Background label
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, target_width, target_height)
        
        # Load background image
        if scene.background_path:
            self._load_background()
        
        # Enable mouse tracking for potential hover effects
        self.setMouseTracking(True)
        
        logger.debug(f"Qt image scene widget created for: {scene.scene_id}")
    
    def _load_background(self) -> None:
        """Load and scale background image."""
        pixmap = QPixmap(self.scene.background_path)
        
        if pixmap.isNull():
            logger.warning(f"Failed to load background: {self.scene.background_path}")
            return
        
        # Scale to widget size
        scaled = pixmap.scaled(
            self.size(),
            Qt.IgnoreAspectRatio,  # Stretch to fit
            Qt.SmoothTransformation
        )
        
        self.background_label.setPixmap(scaled)
        logger.debug(f"Background loaded: {self.scene.background_path}")
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse click events."""
        x = event.x()
        y = event.y()
        
        action = self.scene.handle_click(x, y)
        
        if action:
            self._handle_action(action)
    
    def _handle_action(self, action: str) -> None:
        """
        Execute action from region click.
        
        Args:
            action: Action string (e.g., "navigate:scene_name")
        """
        if action.startswith("navigate:"):
            # Navigate to another scene
            target_scene = action.split(":", 1)[1]
            
            if self.router:
                logger.info(f"Navigating to: {target_scene}")
                self.router.navigate(target_scene)
            else:
                logger.warning(f"No router available for navigation: {target_scene}")
        
        elif action.startswith("emit:"):
            # Emit event (for custom handling)
            event_name = action.split(":", 1)[1]
            self.scene.handle_event(event_name, {"source": "region_click"})
        
        else:
            # Unknown action type
            logger.warning(f"Unknown action type: {action}")
    
    def paintEvent(self, event) -> None:
        """
        Paint event for custom drawing (optional region highlights).
        
        Override this to draw region outlines for debugging.
        """
        super().paintEvent(event)
        
        # Optionally draw region outlines for debugging
        # self._draw_region_outlines()
    
    def _draw_region_outlines(self) -> None:
        """Draw region outlines for debugging (optional)."""
        painter = QPainter(self)
        pen = QPen(QColor(255, 0, 0, 128))  # Semi-transparent red
        pen.setWidth(2)
        painter.setPen(pen)
        
        for region in self.scene.region_manager.regions:
            # Draw polygon outline
            points = [QPoint(int(x), int(y)) for x, y in region.polygon]
            if points:
                for i in range(len(points)):
                    p1 = points[i]
                    p2 = points[(i + 1) % len(points)]
                    painter.drawLine(p1, p2)
        
        painter.end()
