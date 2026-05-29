# Velvet Interface Framework

**Multi-surface interface framework for building UIs across desktop, car dashboard, mobile, and web platforms.**

## Overview

Velvet Interface provides a clean abstraction for building user interfaces that work across multiple rendering backends (surfaces). Write your UI logic once, render it anywhere.

## Scene-Based Interface

Velvet Interface implements the public scene and room-body interface model.

Scenes may be expressive, contextual, hidden, and body-aware, but they only route intent. They do not directly actuate hardware.

See:

- [Scene Interface Contract](docs/scene_interface_contract.md)

## Features

- **Surface-Agnostic Scenes:** Write UI logic once, render on Qt, web, mobile, or custom surfaces
- **Scene Navigation:** Built-in router with history and lifecycle management
- **Image-Based Scenes:** YAML-defined scenes with background images and polygon regions
- **Polygon Regions:** Point-in-polygon hit testing for interactive areas
- **Automatic Scaling:** Scenes adapt from base resolution to any target display
- **Scene Transitions:** Built-in fade, slide effects
- **Reusable Widgets:** Composable UI components that work across surfaces
- **Minimal Dependencies:** Core framework requires only PyYAML
- **Type-Safe:** Full type hints for modern Python development

## Installation

### Core Framework
```bash
pip install velvet-interface
# Includes PyYAML for scene loading
```

### With Qt Support (desktop/embedded)
```bash
pip install velvet-interface[qt]
# Includes PyQt5 for Qt surface
```

### Development
```bash
pip install velvet-interface[dev]
```

## Quick Start

### Basic Example (Qt Surface)

```python
from PyQt5.QtWidgets import QApplication
from velvet_interface.core import Scene, Router
from velvet_interface.surfaces.pyqt import QtSurface
from velvet_interface.scenes import SettingsScene
import sys

# Create Qt application
app = QApplication(sys.argv)

# Create surface
surface = QtSurface(800, 600)
surface.initialize()

# Create router
router = Router(surface)

# Register scenes
router.register_scene(SettingsScene())

# Navigate to settings
router.navigate("settings")

# Show window and run
surface.get_container().show()
sys.exit(app.exec_())
```

### Scene System Example (YAML + Polygon Regions)

Create a scene definition in YAML:

```yaml
# scenes/main.yaml
name: "main_menu"
base_resolution: [1280, 720]
background: "assets/main_bg.png"

regions:
  - name: "start_button"
    polygon: [[100, 300], [400, 300], [400, 400], [100, 400]]
    action: "navigate:game_start"
    metadata:
      tooltip: "Start Game"
  
  - name: "settings_button"
    polygon: [[100, 450], [400, 450], [400, 550], [100, 550]]
    action: "navigate:settings"
    metadata:
      tooltip: "Settings"

transitions:
  enter: "fade"
  exit: "slide_left"
```

Load and use the scene:

```python
from velvet_interface.scene_system import YAMLSceneLoader, ImageScene
from velvet_interface.surfaces.pyqt.image_scene_adapter import QtImageSceneWidget

# Load scene from YAML
loader = YAMLSceneLoader()
scene_data = loader.load("scenes/main.yaml")

# Create ImageScene
scene = ImageScene(scene_data)

# Adapt for Qt rendering
def render_qt(surface):
    return QtImageSceneWidget(scene, surface, router)

scene.render = lambda s: render_qt(s)

# Register and navigate
router.register_scene(scene)
router.navigate("main_menu")
```

Click regions in the background image trigger navigation!

### Creating a Custom Scene

```python
from velvet_interface.core import Scene, Surface
from typing import Any, Optional, Dict

class MyScene(Scene):
    def __init__(self):
        super().__init__("my_scene")
        self.counter = 0
    
    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        super().on_enter(context)
        print("My scene activated!")
    
    def on_exit(self) -> None:
        super().on_exit()
        print("My scene deactivated!")
    
    def render(self, surface: Surface) -> Any:
        # For Qt surface
        if surface.surface_id == "qt":
            from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
            
            widget = QWidget()
            layout = QVBoxLayout()
            
            title = surface.show_text("My Custom Scene", 50, 50, font_size=24)
            layout.addWidget(title)
            
            widget.setLayout(layout)
            return widget
        
        raise NotImplementedError(f"Surface {surface.surface_id} not supported")

# Use the scene
router.register_scene(MyScene())
router.navigate("my_scene")
```

## Architecture

### Core Concepts

#### Scene
A logical view or screen in your application. Scenes are surface-agnostic and contain your UI logic.

```python
class Scene(ABC):
    def on_enter(self, context) -> None: ...
    def on_exit(self) -> None: ...
    def render(self, surface) -> Any: ...
```

#### Surface
A rendering backend (Qt, web, mobile, etc.). Surfaces implement platform-specific rendering.

```python
class Surface(ABC):
    def show_scene(self, scene) -> Any: ...
    def show_text(self, text, x, y, ...) -> Any: ...
    def show_button(self, label, x, y, ...) -> Any: ...
```

#### Router
Manages scene navigation and lifecycle.

```python
router = Router(surface)
router.register_scene(my_scene)
router.navigate("my_scene")
router.back()  # Navigate to previous scene
```

#### Widget
Reusable UI components that can be embedded in scenes.

```python
class Widget(ABC):
    def render(self, surface, x, y) -> Any: ...
```

### Multi-Surface Design

```
┌─────────────────────────────────────────┐
│ Scene Logic (your code)                 │
│  - State management                     │
│  - Business logic                       │
│  - Event handling                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Surface Interface (framework)           │
│  - show_scene(), show_text(), etc.      │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┬─────────┐
       ▼               ▼         ▼
   ┌───────┐      ┌──────┐  ┌────────┐
   │  Qt   │      │ Web  │  │ Mobile │
   │Surface│      │Surface  │Surface │
   └───────┘      └──────┘  └────────┘
```

## Supported Surfaces

### Qt (Desktop/Embedded)
- Status: ✓ Implemented
- Use case: Desktop apps, car dashboards, embedded systems
- Requires: `PyQt5`

### Web (Browser)
- Status: 🚧 Planned
- Use case: Web applications
- Requires: Backend framework (Flask, FastAPI, etc.)

### Mobile (iOS/Android)
- Status: 🚧 Planned
- Use case: Mobile apps
- Requires: React Native or Flutter bridge

### Custom Surfaces
You can implement your own surface by subclassing `Surface` and implementing the abstract methods.

## Examples

See the `examples/` directory for complete examples:

- `minimal_app.py` — Minimal Qt application with settings scene
- `desktop_demo/` — Desktop application with YAML scenes
- `automotive_demo/` — Car dashboard with three-zone layout
- `mobile_demo/` — Mobile app interface (portrait)
- `industrial_demo/` — Industrial HMI control panel
- `robotics_demo/` — Robot control interface

Run an example:

```bash
cd examples/desktop_demo
python demo.py
```

## Documentation

- [Architecture Guide](docs/architecture.md)
- [Creating Scenes](docs/creating-scenes.md)
- [Surface Development](docs/surfaces/)

## Requirements

- Python 3.8 or higher
- PyYAML 5.4+ (for scene loading)
- Optional: PyQt5 5.15+ (for Qt surface)

## License

**GNU General Public License v3.0 (GPLv3)**

See [LICENSE](LICENSE) for full terms.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Project Status

**Version:** 0.2.0 (Alpha)  
**Stability:** Experimental — API may change

**New in 0.2.0:**
- YAML scene loading
- Polygon region support
- Automatic scene scaling
- Built-in transitions
- Image-based scenes
- Multiple demo applications

This is an early release. Production use is not recommended until 1.0.0.

## Links

- **GitHub:** [github.com/velvet-ai/velvet-interface](https://github.com/velvet-ai/velvet-interface)
- **Issues:** [GitHub Issues](https://github.com/velvet-ai/velvet-interface/issues)
- **Documentation:** [docs.velvet.ai/interface](https://docs.velvet.ai/interface)

---

Built for multi-platform interface development.
