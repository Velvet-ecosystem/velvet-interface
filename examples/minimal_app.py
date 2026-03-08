# examples/minimal_app.py
"""
Minimal Velvet Interface application using Qt surface.

Demonstrates basic setup with one scene.
"""

import sys
from PyQt5.QtWidgets import QApplication

from velvet_interface.core import Router
from velvet_interface.surfaces.pyqt import QtSurface
from velvet_interface.scenes import SettingsScene


def main():
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create Qt surface (800x600 window)
    surface = QtSurface(800, 600)
    surface.initialize()
    
    # Create router
    router = Router(surface)
    
    # Register scenes
    settings_scene = SettingsScene()
    router.register_scene(settings_scene)
    
    # Navigate to settings scene
    router.navigate("settings")
    
    # Show window
    container = surface.get_container()
    container.setWindowTitle("Velvet Interface - Minimal Example")
    container.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
