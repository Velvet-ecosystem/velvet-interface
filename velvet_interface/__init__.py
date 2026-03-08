# velvet_interface/__init__.py
"""
Velvet Interface Framework

A multi-surface interface framework for building UIs that work across
desktop, car dashboard, mobile, and web platforms.

Core concepts:
- Scene: A logical view or screen (surface-agnostic)
- Surface: A rendering backend (Qt, web, mobile, etc.)
- Widget: A reusable UI component
- Router: Scene navigation manager

Scene System:
- ImageScene: Image-based scenes with polygon regions
- YAMLSceneLoader: Load scenes from YAML definitions
- PolygonRegion: Interactive clickable areas
- SceneScaler: Automatic resolution scaling
- Transitions: Scene transition effects

Example usage:

    from velvet_interface.core import Scene, Router
    from velvet_interface.surfaces.pyqt import QtSurface
    from velvet_interface.scene_system import YAMLSceneLoader, ImageScene
    
    # Create surface
    surface = QtSurface(800, 600)
    surface.initialize()
    
    # Create router
    router = Router(surface)
    
    # Load scene from YAML
    loader = YAMLSceneLoader()
    scene_data = loader.load("scenes/main.yaml")
    scene = ImageScene(scene_data)
    
    # Register and navigate
    router.register_scene(scene)
    router.navigate("main")
"""

__version__ = "0.2.0"

from velvet_interface.core import Scene, Surface, Widget, Router

__all__ = [
    "Scene",
    "Surface",
    "Widget",
    "Router",
]
