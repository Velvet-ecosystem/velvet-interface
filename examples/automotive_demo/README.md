# Automotive Demo

Demonstrates image-based scenes for automotive dashboards.

## Features

- Wide display format (1920x720)
- Three-zone layout (left, center, right)
- Touch-friendly polygon regions
- Scene transitions

## Running

```bash
cd examples/automotive_demo
python demo.py
```

## Scene Structure

```
dashboard (main)
  ├─ climate → Climate controls
  ├─ navigation → Map/routing
  └─ media → Audio/video player
```

## Notes

This is a framework demonstration. Production automotive UIs would include:
- Real-time vehicle data integration
- CAN bus communication
- Safety constraints
- OEM customization

For production automotive use, consider integrating with `velvet-vehicle-can`.
