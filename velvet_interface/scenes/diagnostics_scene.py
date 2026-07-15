# velvet_interface/scenes/diagnostics_scene.py
from __future__ import annotations
"""
Generic diagnostics scene example.

Displays system status and diagnostic information.
"""

from typing import Dict, Any, Optional
import logging

try:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface

logger = logging.getLogger(__name__)


class DiagnosticsScene(Scene):
    """
    Generic diagnostics scene.
    
    Displays system information and status.
    Can be extended with custom diagnostic checks.
    """
    
    def __init__(self):
        super().__init__("diagnostics")
        self.status_data: Dict[str, str] = {}
    
    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Gather diagnostic data when scene becomes active."""
        super().on_enter(context)
        logger.info("Diagnostics scene entered")
        
        # Gather diagnostic data
        self.status_data = {
            "System": "Online",
            "Modules": "4 loaded",
            "Memory": "128 MB used",
            "Uptime": "2h 34m",
        }
    
    def on_exit(self) -> None:
        """Clean up when leaving scene."""
        super().on_exit()
        logger.info("Diagnostics scene exited")
    
    def render(self, surface: Surface) -> Any:
        """
        Render diagnostics scene.
        
        For Qt surface: returns QWidget
        For other surfaces: would return appropriate container
        """
        if surface.surface_id == "qt" and PYQT_AVAILABLE:
            return self._render_qt(surface)
        else:
            raise NotImplementedError(f"Surface {surface.surface_id} not supported")
    
    def _render_qt(self, surface: Surface) -> QWidget:
        """Render diagnostics scene for Qt surface."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Title
        title = QLabel("System Diagnostics")
        title.setFont(QFont("Arial", 24))
        layout.addWidget(title)
        
        # Status items
        for key, value in self.status_data.items():
            status_label = QLabel(f"{key}: {value}")
            status_label.setFont(QFont("Arial", 14))
            layout.addWidget(status_label)
        
        return widget
    
    def update_status(self, key: str, value: str) -> None:
        """Update a status value."""
        self.status_data[key] = value
        logger.debug(f"Status updated: {key} = {value}")
