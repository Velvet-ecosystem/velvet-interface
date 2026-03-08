# examples/desktop_demo/demo.py
"""
Desktop Demo - Image-based scenes with polygon regions.

Demonstrates:
- YAML scene loading
- Polygon interaction regions
- Scene navigation
- Transitions
"""

import sys
from pathlib import Path

try:
    from PyQt5.QtWidgets import QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("PyQt5 not installed. Install with: pip install PyQt5")
    sys.exit(1)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from velvet_interface.core import Router
from velvet_interface.surfaces.pyqt import QtSurface
from velvet_interface.scene_system import YAMLSceneLoader, ImageScene
from velvet_interface.surfaces.pyqt.image_scene_adapter import QtImageSceneWidget


def create_placeholder_background(path: Path, width: int, height: int, color: str, text: str):
    """Create a simple placeholder background image."""
    try:
        from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
        from PyQt5.QtCore import Qt
        
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(color))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 48))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        
        path.parent.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(path))
        
    except Exception as e:
        print(f"Warning: Could not create placeholder: {e}")


def main():
    """Run desktop demo."""
    print("Desktop Demo - Image-based Scenes")
    print("=" * 50)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create Qt surface
    surface = QtSurface(1280, 720)
    surface.initialize()
    
    # Create router
    router = Router(surface)
    
    # Create placeholder backgrounds
    demo_dir = Path(__file__).parent
    assets_dir = demo_dir / "assets"
    
    create_placeholder_background(
        assets_dir / "desktop_bg.png",
        1280, 720,
        "#2C3E50",
        "Desktop Demo\nMain Menu"
    )
    
    create_placeholder_background(
        assets_dir / "settings_bg.png",
        1280, 720,
        "#34495E",
        "Settings"
    )
    
    create_placeholder_background(
        assets_dir / "about_bg.png",
        1280, 720,
        "#16A085",
        "About"
    )
    
    # Load scenes from YAML
    loader = YAMLSceneLoader()
    scenes_dir = demo_dir / "scenes"
    
    try:
        scene_data = loader.load(str(scenes_dir / "main.yaml"))
        
        # Create ImageScene
        main_scene = ImageScene(scene_data)
        
        # Modify render method to use Qt adapter
        def render_with_adapter(s):
            return lambda surface: QtImageSceneWidget(main_scene, surface, router)
        
        main_scene.render = render_with_adapter(main_scene)
        
        # Register scene
        router.register_scene(main_scene)
        
        print(f"✓ Loaded scene: {scene_data['name']}")
        print(f"  - Background: {scene_data.get('background', 'none')}")
        print(f"  - Regions: {len(scene_data.get('regions', []))}")
        print(f"  - Enter transition: {scene_data.get('transitions', {}).get('enter', 'none')}")
        
    except FileNotFoundError:
        print("✗ Scene YAML not found")
        print(f"  Expected: {scenes_dir / 'main.yaml'}")
        print("\nNote: This is a demo framework. Create scene YAML files to see it in action.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error loading scenes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Navigate to main scene
    router.navigate("desktop_main")
    
    # Show window
    container = surface.get_container()
    container.setWindowTitle("Velvet Interface - Desktop Demo")
    container.show()
    
    print("\n" + "=" * 50)
    print("Demo running. Click regions to navigate.")
    print("Close window to exit.")
    print("=" * 50)
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
