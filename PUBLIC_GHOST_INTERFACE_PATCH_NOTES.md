# Public Ghost Interface Patch Notes

This patch adds the public-safe Ghost CAN panel for the Velvet ghost system.

## Added

- `velvet_interface/core/ghost_can_panel.py`
- `examples/ghost_can_panel.py`
- `examples/fixtures/ghost_can_panel_event.json`
- `docs/ghost_can_panel.md`
- `tests/test_ghost_can_panel.py`

## Updated

- `velvet_interface/core/__init__.py`
- `velvet_interface/__init__.py`
- `velvet_interface/scenes/settings_scene.py`
- `velvet_interface/scenes/diagnostics_scene.py`
- `README.md`

The panel is display-only. It blocks command, executor, target, hardware, shell, token, transmit, and actuation-shaped fields. It does not open `can0`, decode raw CAN, request Runtime routes, grant authority, or imply physical vehicle control.
