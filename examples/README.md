# Velvet Interface - Example Demos

Example demonstrations of the scene system framework.

## Available Demos

### Desktop Demo
**Directory:** `desktop_demo/`  
**Resolution:** 1280x720  
**Features:** Traditional desktop application with menu navigation

```bash
cd desktop_demo
python demo.py
```

### Automotive Demo
**Directory:** `automotive_demo/`  
**Resolution:** 1920x720 (wide)  
**Features:** Car dashboard with three-zone layout

```bash
cd automotive_demo
python demo.py
```

### Mobile Demo
**Directory:** `mobile_demo/`  
**Resolution:** 390x844 (portrait)  
**Features:** Mobile app home screen

```bash
cd mobile_demo
python demo.py
```

### Industrial Demo
**Directory:** `industrial_demo/`  
**Resolution:** 1024x768  
**Features:** Industrial machine control panel (HMI)

```bash
cd industrial_demo
python demo.py
```

### Robotics Demo
**Directory:** `robotics_demo/`  
**Resolution:** 1280x800  
**Features:** Robot control interface with multiple zones

```bash
cd robotics_demo
python demo.py
```

## Demo Architecture

All demos use the same framework components:

1. **YAML Scene Definitions** - Declarative scene layout
2. **Polygon Regions** - Click/touch interaction areas
3. **Automatic Scaling** - Adapts to different screen sizes
4. **Scene Transitions** - Smooth navigation between scenes
5. **Router Integration** - Navigation management

## Creating Custom Scenes

### 1. Define Scene in YAML

```yaml
name: "my_scene"
base_resolution: [1280, 720]
background: "assets/my_bg.png"

regions:
  - name: "button_1"
    polygon: [[100, 100], [300, 100], [300, 200], [100, 200]]
    action: "navigate:next_scene"
    metadata:
      tooltip: "Click me"

transitions:
  enter: "fade"
  exit: "slide_left"
```

### 2. Load and Register Scene

```python
from velvet_interface.scene_system import YAMLSceneLoader, ImageScene

loader = YAMLSceneLoader()
scene_data = loader.load("scenes/my_scene.yaml")
scene = ImageScene(scene_data)

router.register_scene(scene)
```

### 3. Navigate

```python
router.navigate("my_scene")
```

## Framework Features Demonstrated

### YAML Scene Loading
- Declarative scene definitions
- Metadata support
- Validation

### Polygon Regions
- Point-in-polygon hit testing
- Action binding
- Metadata (tooltips, sounds, etc.)

### Automatic Scaling
- Base resolution → target resolution
- Maintains aspect ratio or stretches
- Scales all regions automatically

### Scene Transitions
- Fade, slide (left/right/up/down)
- Configurable duration
- Per-scene enter/exit transitions

### Router Integration
- Scene lifecycle (on_enter, on_exit)
- Navigation history
- Action parsing (navigate:, emit:)

## Requirements

- Python 3.8+
- PyQt5 (for Qt demos)
- PyYAML (for scene loading)

```bash
pip install PyQt5 PyYAML
```

## Notes

These are framework demonstrations, not production applications.

For production use:
- Add proper asset management
- Implement error handling
- Add accessibility features
- Optimize for target platform
- Add telemetry/analytics

## Integration

These demos can be integrated with:
- **velvet-ai-core** - For event bus, command routing
- **velvet-vehicle-can** - For automotive CAN integration
- Custom backends - Database, IoT, etc.

The framework is designed to be standalone but integrates easily with other systems.
