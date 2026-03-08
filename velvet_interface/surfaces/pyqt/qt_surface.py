# velvet_interface/surfaces/pyqt/qt_surface.py
"""
PyQt5 surface implementation.

Renders scenes and widgets using Qt widgets.
"""

from __future__ import annotations
from typing import Any, Optional, Tuple
import logging

try:
    from PyQt5.QtWidgets import (
        QWidget, QLabel, QPushButton, QStackedWidget, QVBoxLayout
    )
    from PyQt5.QtGui import QPixmap, QFont
    from PyQt5.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from velvet_interface.core.surface import Surface
from velvet_interface.core.scene import Scene

logger = logging.getLogger(__name__)


class QtSurface(Surface):
    """
    Qt-based surface implementation.
    
    Renders scenes as QWidget instances within a QStackedWidget.
    """
    
    def __init__(self, width: int = 800, height: int = 600):
        """
        Initialize Qt surface.
        
        Args:
            width: Surface width in pixels
            height: Surface height in pixels
        """
        super().__init__("qt")
        
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is not installed. Install with: pip install PyQt5")
        
        self.width = width
        self.height = height
        self.container: Optional[QStackedWidget] = None
        self._scene_widgets: dict[str, QWidget] = {}
    
    def initialize(self) -> None:
        """Initialize Qt surface with main container widget."""
        self.container = QStackedWidget()
        self.container.setFixedSize(self.width, self.height)
        logger.info(f"Qt surface initialized ({self.width}x{self.height})")
    
    def show_scene(self, scene: Scene) -> QWidget:
        """
        Display a scene as a Qt widget.
        
        Args:
            scene: Scene to display
            
        Returns:
            QWidget containing the rendered scene
        """
        if not self.container:
            raise RuntimeError("Surface not initialized. Call initialize() first.")
        
        # Check if scene already rendered
        if scene.scene_id in self._scene_widgets:
            widget = self._scene_widgets[scene.scene_id]
        else:
            # Render scene to Qt widget
            widget = scene.render(self)
            self._scene_widgets[scene.scene_id] = widget
            self.container.addWidget(widget)
        
        # Show the widget
        self.container.setCurrentWidget(widget)
        logger.debug(f"Showing scene: {scene.scene_id}")
        
        return widget
    
    def hide_scene(self, scene: Scene) -> None:
        """
        Hide a scene (switch away from it).
        
        Args:
            scene: Scene to hide
        """
        # Qt handles hiding via setCurrentWidget
        logger.debug(f"Hiding scene: {scene.scene_id}")
    
    def show_text(
        self,
        text: str,
        x: int,
        y: int,
        font_size: int = 14,
        color: Optional[str] = None
    ) -> QLabel:
        """
        Display text as a QLabel.
        
        Args:
            text: Text content
            x: Horizontal position
            y: Vertical position
            font_size: Font size in points
            color: CSS color string (e.g., "#FFFFFF")
            
        Returns:
            QLabel widget
        """
        label = QLabel(text)
        label.setFont(QFont("Arial", font_size))
        label.move(x, y)
        
        if color:
            label.setStyleSheet(f"color: {color};")
        
        return label
    
    def show_button(
        self,
        label: str,
        x: int,
        y: int,
        width: int,
        height: int,
        on_click: Optional[callable] = None
    ) -> QPushButton:
        """
        Display a button as a QPushButton.
        
        Args:
            label: Button text
            x: Horizontal position
            y: Vertical position
            width: Button width
            height: Button height
            on_click: Click handler
            
        Returns:
            QPushButton widget
        """
        button = QPushButton(label)
        button.setGeometry(x, y, width, height)
        
        if on_click:
            button.clicked.connect(on_click)
        
        return button
    
    def show_image(
        self,
        image_path: str,
        x: int,
        y: int,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> QLabel:
        """
        Display an image as a QLabel with QPixmap.
        
        Args:
            image_path: Path to image file
            x: Horizontal position
            y: Vertical position
            width: Image width (None = original)
            height: Image height (None = original)
            
        Returns:
            QLabel with pixmap
        """
        label = QLabel()
        pixmap = QPixmap(image_path)
        
        if not pixmap.isNull():
            if width and height:
                pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
        else:
            logger.warning(f"Failed to load image: {image_path}")
        
        label.move(x, y)
        return label
    
    def clear(self) -> None:
        """Clear all scenes from the container."""
        if self.container:
            while self.container.count() > 0:
                widget = self.container.widget(0)
                self.container.removeWidget(widget)
                widget.deleteLater()
            
            self._scene_widgets.clear()
            logger.debug("Surface cleared")
    
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get surface dimensions.
        
        Returns:
            (width, height) tuple
        """
        return (self.width, self.height)
    
    def get_container(self) -> QStackedWidget:
        """
        Get the Qt container widget.
        
        Returns:
            QStackedWidget containing scenes
        """
        if not self.container:
            raise RuntimeError("Surface not initialized")
        return self.container
