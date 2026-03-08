# velvet_interface/core/__init__.py
"""
Core interface framework primitives.

Provides abstract base classes for building multi-surface interfaces.
"""

from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface
from velvet_interface.core.widget import Widget
from velvet_interface.core.router import Router

__all__ = [
    "Scene",
    "Surface",
    "Widget",
    "Router",
]
