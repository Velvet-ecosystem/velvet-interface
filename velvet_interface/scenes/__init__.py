# velvet_interface/scenes/__init__.py
"""
Example scene implementations.

Generic, reusable scenes for common interface patterns.
"""

from velvet_interface.scenes.settings_scene import SettingsScene
from velvet_interface.scenes.diagnostics_scene import DiagnosticsScene

__all__ = [
    "SettingsScene",
    "DiagnosticsScene",
]
