# SPDX-License-Identifier: GPL-3.0-only
"""Strict runtime binding for selecting a Velvet interface surface set.

A surface set tells the interface where an approved collection of presentation
manifests lives and which scene should be preferred first. It is presentation
selection only. It cannot grant authority, select executors, or carry secrets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - package dependency guard
    yaml = None


SURFACE_SET_SCHEMA = "velvet.interface.surface-set.v1"
_FORBIDDEN_KEYS = {
    "actuate",
    "actuation",
    "capability",
    "capability_token",
    "command",
    "credential",
    "executor",
    "executor_name",
    "hardware_target",
    "password",
    "route_id",
    "secret",
    "shell",
    "token",
}


class SurfaceSetError(ValueError):
    """Raised when a runtime surface-set binding is malformed or unsafe."""


@dataclass(frozen=True)
class SurfaceSetBinding:
    name: str
    surface_directory: str
    initial_scene: str
    source_path: Optional[str] = None
    schema: str = SURFACE_SET_SCHEMA

    def __post_init__(self) -> None:
        _require_text("name", self.name)
        _require_text("surface_directory", self.surface_directory)
        _require_text("initial_scene", self.initial_scene)
        if self.schema != SURFACE_SET_SCHEMA:
            raise SurfaceSetError("unsupported surface-set schema")

    @property
    def surface_path(self) -> Path:
        return Path(self.surface_directory)


class SurfaceSetLoader:
    """Load one safe runtime surface-set binding from YAML."""

    def load(self, binding_path: str, require_directory: bool = True) -> SurfaceSetBinding:
        if yaml is None:
            raise ImportError("PyYAML not installed. Install with: pip install PyYAML")

        path = Path(binding_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError("Surface-set binding not found: %s" % binding_path)

        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError:
            raise
        except Exception as exc:
            raise SurfaceSetError("surface-set YAML is invalid: %s" % exc)

        if not isinstance(document, Mapping):
            raise SurfaceSetError("surface-set root must be a mapping")
        return self.from_mapping(document, source_path=path, require_directory=require_directory)

    def from_mapping(
        self,
        document: Mapping[str, Any],
        source_path: Optional[Path] = None,
        require_directory: bool = False,
    ) -> SurfaceSetBinding:
        _reject_forbidden(document)

        schema = str(document.get("schema", SURFACE_SET_SCHEMA)).strip()
        if schema != SURFACE_SET_SCHEMA:
            raise SurfaceSetError("unsupported surface-set schema")

        name = _required_mapping_text(document, "name")
        initial_scene = _required_mapping_text(document, "initial_scene")
        raw_directory = _required_mapping_text(document, "surface_directory")

        directory = Path(raw_directory).expanduser()
        if not directory.is_absolute() and source_path is not None:
            directory = source_path.parent / directory
        directory = directory.resolve()

        if require_directory and not directory.is_dir():
            raise FileNotFoundError("Surface directory not found: %s" % directory)

        return SurfaceSetBinding(
            name=name,
            surface_directory=str(directory),
            initial_scene=initial_scene,
            source_path=str(source_path) if source_path is not None else None,
            schema=schema,
        )


def _required_mapping_text(document: Mapping[str, Any], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SurfaceSetError("%s must be a non-empty string" % key)
    return value.strip()


def _require_text(label: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SurfaceSetError("%s must be a non-empty string" % label)


def _reject_forbidden(document: Mapping[str, Any]) -> None:
    for key in document:
        key_text = str(key).strip().lower()
        if key_text in _FORBIDDEN_KEYS:
            raise SurfaceSetError("surface-set binding cannot contain %s" % key_text)
