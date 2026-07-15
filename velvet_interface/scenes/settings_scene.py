# velvet_interface/scenes/settings_scene.py
from __future__ import annotations
"""
Generic settings scene example.

Demonstrates a simple settings interface with configurable options.
"""

from typing import Dict, Any, Optional
import logging

try:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface

logger = logging.getLogger(__name__)


class SettingsScene(Scene):
    """
    Generic settings scene.
    
    Displays configurable application settings.
    Can be extended with custom setting controls.
    """
    
    def __init__(self):
        super().__init__("settings")
        self.settings: Dict[str, Any] = {}
    
    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Load settings when scene becomes active."""
        super().on_enter(context)
        logger.info("Settings scene entered")
        
        # Load default settings
        self.settings = {
            "volume": 50,
            "brightness": 75,
            "dark_mode": False,
        }
    
    def on_exit(self) -> None:
        """Save settings when leaving scene."""
        super().on_exit()
        logger.info(f"Settings scene exited, settings: {self.settings}")
    
    def render(self, surface: Surface) -> Any:
        """
        Render settings scene.
        
        For Qt surface: returns QWidget
        For other surfaces: would return appropriate container
        """
        if surface.surface_id == "qt" and PYQT_AVAILABLE:
            return self._render_qt(surface)
        else:
            raise NotImplementedError(f"Surface {surface.surface_id} not supported")
    
    def _render_qt(self, surface: Surface) -> QWidget:
        """Render settings scene for Qt surface."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 24))
        layout.addWidget(title)
        
        # Settings info (placeholder)
        info = QLabel(f"Volume: {self.settings['volume']}%")
        info.setFont(QFont("Arial", 14))
        layout.addWidget(info)
        
        brightness_info = QLabel(f"Brightness: {self.settings['brightness']}%")
        brightness_info.setFont(QFont("Arial", 14))
        layout.addWidget(brightness_info)
        
        mode_info = QLabel(f"Dark Mode: {'On' if self.settings['dark_mode'] else 'Off'}")
        mode_info.setFont(QFont("Arial", 14))
        layout.addWidget(mode_info)
        
        # Back button (example)
        back_button = QPushButton("Back")
        back_button.clicked.connect(lambda: self.handle_event("back.clicked", {}))
        layout.addWidget(back_button)
        
        return widget
    
    def update_setting(self, key: str, value: Any) -> None:
        """Update a setting value."""
        self.settings[key] = value
        logger.debug(f"Setting updated: {key} = {value}")
