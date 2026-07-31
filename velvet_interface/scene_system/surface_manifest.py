# SPDX-License-Identifier: GPL-3.0-only
"""Strict data contracts for image-first Velvet interface surfaces.

A surface manifest binds one background image to resolution-independent press
points and widget placements. It describes presentation only. It cannot import
code, select executors, carry capability tokens, or grant physical authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - package dependency guard
    yaml = None


SURFACE_MANIFEST_SCHEMA = "velvet.interface.surface.v1"
_ALLOWED_FIT_MODES = {"stretch", "contain", "cover"}
_ALLOWED_COORDINATE_SPACES = {"normalized", "pixels"}
_ALLOWED_ACTION_PREFIXES = {"navigate", "emit"}
_FORBIDDEN_KEYS = {
    "actuate",
    "actuation",
    "capability",
    "capability_token",
    "command",
    "executor",
    "executor_name",
    "hardware_target",
    "route_id",
    "shell",
    "target",
    "token",
}


class SurfaceManifestError(ValueError):
    """Raised when a surface manifest is unsafe or malformed."""


@dataclass(frozen=True)
class BackgroundAsset:
    image_path: str
    fit: str = "cover"
    alt_text: str = "Velvet interface background"

    def __post_init__(self) -> None:
        _require_text("background.image", self.image_path)
        _require_text("background.alt_text", self.alt_text)
        if self.fit not in _ALLOWED_FIT_MODES:
            raise SurfaceManifestError("background.fit must be stretch, contain, or cover")


@dataclass(frozen=True)
class PressPoint:
    point_id: str
    polygon: Tuple[Tuple[float, float], ...]
    action: str
    coordinate_space: str = "normalized"
    label: str = ""
    accessibility_label: str = ""
    z_index: int = 10
    enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text("press_point.id", self.point_id)
        _validate_action(self.action)
        _validate_coordinate_space(self.coordinate_space)
        _validate_polygon(self.polygon, self.coordinate_space)
        _validate_z_index(self.z_index)
        if not isinstance(self.enabled, bool):
            raise SurfaceManifestError("press_point.enabled must be boolean")
        if self.label:
            _require_text("press_point.label", self.label)
        if self.accessibility_label:
            _require_text("press_point.accessibility_label", self.accessibility_label)
        _reject_forbidden(self.metadata, "press_point.metadata")

    def base_polygon(self, base_resolution: Tuple[int, int]) -> Tuple[Tuple[float, float], ...]:
        if self.coordinate_space == "pixels":
            return self.polygon
        width, height = base_resolution
        return tuple((x * width, y * height) for x, y in self.polygon)


@dataclass(frozen=True)
class WidgetPlacement:
    widget_id: str
    rect: Tuple[float, float, float, float]
    coordinate_space: str = "normalized"
    z_index: int = 20
    visible_in: Tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text("widget.id", self.widget_id)
        _validate_coordinate_space(self.coordinate_space)
        _validate_rect(self.rect, self.coordinate_space)
        _validate_z_index(self.z_index)
        for mode in self.visible_in:
            _require_text("widget.visible_in item", mode)
        _reject_forbidden(self.metadata, "widget.metadata")

    def base_rect(self, base_resolution: Tuple[int, int]) -> Tuple[float, float, float, float]:
        if self.coordinate_space == "pixels":
            return self.rect
        width, height = base_resolution
        x, y, rect_width, rect_height = self.rect
        return (x * width, y * height, rect_width * width, rect_height * height)


@dataclass(frozen=True)
class SurfaceManifest:
    name: str
    base_resolution: Tuple[int, int]
    background: BackgroundAsset
    press_points: Tuple[PressPoint, ...] = ()
    widgets: Tuple[WidgetPlacement, ...] = ()
    enter_transition: str = "none"
    exit_transition: str = "none"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source_path: Optional[str] = None
    schema: str = SURFACE_MANIFEST_SCHEMA

    def __post_init__(self) -> None:
        _require_text("name", self.name)
        if self.schema != SURFACE_MANIFEST_SCHEMA:
            raise SurfaceManifestError("unsupported surface manifest schema")
        _validate_resolution(self.base_resolution)
        _require_unique([item.point_id for item in self.press_points], "press point")
        _require_unique([item.widget_id for item in self.widgets], "widget")
        _reject_forbidden(self.metadata, "surface.metadata")

    def to_scene_data(self) -> Dict[str, Any]:
        """Project the manifest into the existing ImageScene mapping contract."""

        return {
            "schema": self.schema,
            "name": self.name,
            "base_resolution": list(self.base_resolution),
            "background": self.background.image_path,
            "background_fit": self.background.fit,
            "background_alt_text": self.background.alt_text,
            "regions": [
                {
                    "name": point.point_id,
                    "polygon": [list(pair) for pair in point.base_polygon(self.base_resolution)],
                    "action": point.action,
                    "enabled": point.enabled,
                    "z_index": point.z_index,
                    "metadata": dict(point.metadata, label=point.label, accessibility_label=point.accessibility_label),
                }
                for point in self.press_points
            ],
            "widgets": [
                {
                    "widget_id": widget.widget_id,
                    "rect": list(widget.base_rect(self.base_resolution)),
                    "z_index": widget.z_index,
                    "visible_in": list(widget.visible_in),
                    "metadata": dict(widget.metadata),
                }
                for widget in self.widgets
            ],
            "transitions": {
                "enter": self.enter_transition,
                "exit": self.exit_transition,
            },
            "metadata": dict(self.metadata),
            "source_path": self.source_path,
        }


class SurfaceManifestLoader:
    """Load one safe image-surface manifest from YAML."""

    def load(self, manifest_path: str, require_background: bool = True) -> SurfaceManifest:
        if yaml is None:
            raise ImportError("PyYAML not installed. Install with: pip install PyYAML")
        path = Path(manifest_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError("Surface manifest not found: %s" % manifest_path)
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError:
            raise
        except Exception as exc:
            raise SurfaceManifestError("surface manifest YAML is invalid: %s" % exc)
        if not isinstance(document, Mapping):
            raise SurfaceManifestError("surface manifest root must be a mapping")
        return self.from_mapping(
            document,
            source_path=path,
            require_background=require_background,
        )

    def from_mapping(
        self,
        document: Mapping[str, Any],
        source_path: Optional[Path] = None,
        require_background: bool = False,
    ) -> SurfaceManifest:
        _reject_forbidden(document, "surface")
        schema = str(document.get("schema", SURFACE_MANIFEST_SCHEMA)).strip()
        if schema != SURFACE_MANIFEST_SCHEMA:
            raise SurfaceManifestError("unsupported surface manifest schema")

        base_resolution = _parse_resolution(document.get("base_resolution", (1280, 720)))
        background = self._parse_background(
            document.get("background"), source_path, require_background
        )
        press_raw = document.get("press_points", document.get("regions", ()))
        widgets_raw = document.get("widgets", ())
        press_points = tuple(self._parse_press_point(item) for item in _require_sequence("press_points", press_raw))
        widgets = tuple(self._parse_widget(item) for item in _require_sequence("widgets", widgets_raw))
        transitions = document.get("transitions", {})
        if not isinstance(transitions, Mapping):
            raise SurfaceManifestError("transitions must be a mapping")
        metadata = document.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise SurfaceManifestError("metadata must be a mapping")

        return SurfaceManifest(
            name=_required_mapping_text(document, "name"),
            base_resolution=base_resolution,
            background=background,
            press_points=press_points,
            widgets=widgets,
            enter_transition=str(transitions.get("enter", "none")),
            exit_transition=str(transitions.get("exit", "none")),
            metadata=dict(metadata),
            source_path=str(source_path) if source_path is not None else None,
            schema=schema,
        )

    def _parse_background(
        self,
        value: Any,
        source_path: Optional[Path],
        require_background: bool,
    ) -> BackgroundAsset:
        if isinstance(value, str):
            raw_path = value
            fit = "cover"
            alt_text = "Velvet interface background"
        elif isinstance(value, Mapping):
            raw_path = _required_mapping_text(value, "image")
            fit = str(value.get("fit", "cover")).strip().lower()
            alt_text = str(value.get("alt_text", "Velvet interface background")).strip()
        else:
            raise SurfaceManifestError("background must be a path or mapping")

        path = Path(raw_path).expanduser()
        if not path.is_absolute() and source_path is not None:
            path = source_path.parent / path
        resolved = path.resolve()
        if require_background and not resolved.is_file():
            raise FileNotFoundError("Surface background not found: %s" % resolved)
        return BackgroundAsset(str(resolved), fit, alt_text)

    def _parse_press_point(self, item: Any) -> PressPoint:
        if not isinstance(item, Mapping):
            raise SurfaceManifestError("each press point must be a mapping")
        polygon_raw = item.get("polygon")
        polygon = _parse_polygon(polygon_raw)
        coordinate_space = str(item.get("coordinate_space", "pixels" if "regions" in item else "normalized")).lower()
        metadata = item.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise SurfaceManifestError("press point metadata must be a mapping")
        point_id = item.get("id", item.get("name"))
        if not isinstance(point_id, str) or not point_id.strip():
            raise SurfaceManifestError("press point id must be a non-empty string")
        return PressPoint(
            point_id=point_id.strip(),
            polygon=polygon,
            action=_required_mapping_text(item, "action"),
            coordinate_space=coordinate_space,
            label=str(item.get("label", metadata.get("label", ""))).strip(),
            accessibility_label=str(item.get("accessibility_label", metadata.get("accessibility_label", ""))).strip(),
            z_index=_parse_int(item.get("z_index", 10), "press point z_index"),
            enabled=item.get("enabled", True),
            metadata=dict(metadata),
        )

    def _parse_widget(self, item: Any) -> WidgetPlacement:
        if not isinstance(item, Mapping):
            raise SurfaceManifestError("each widget placement must be a mapping")
        metadata = item.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise SurfaceManifestError("widget metadata must be a mapping")
        visible_raw = item.get("visible_in", ())
        visible_in = tuple(str(value).strip() for value in _require_sequence("visible_in", visible_raw))
        return WidgetPlacement(
            widget_id=_required_mapping_text(item, "widget_id"),
            rect=_parse_rect(item.get("rect")),
            coordinate_space=str(item.get("coordinate_space", "normalized")).lower(),
            z_index=_parse_int(item.get("z_index", 20), "widget z_index"),
            visible_in=visible_in,
            metadata=dict(metadata),
        )


def _parse_resolution(value: Any) -> Tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise SurfaceManifestError("base_resolution must be [width, height]")
    result = (_parse_int(value[0], "base width"), _parse_int(value[1], "base height"))
    _validate_resolution(result)
    return result


def _parse_polygon(value: Any) -> Tuple[Tuple[float, float], ...]:
    if not isinstance(value, (list, tuple)):
        raise SurfaceManifestError("press point polygon must be a sequence")
    points = []
    for item in value:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise SurfaceManifestError("polygon point must be [x, y]")
        points.append((_parse_number(item[0], "polygon x"), _parse_number(item[1], "polygon y")))
    return tuple(points)


def _parse_rect(value: Any) -> Tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise SurfaceManifestError("widget rect must be [x, y, width, height]")
    return tuple(_parse_number(item, "widget rect") for item in value)  # type: ignore[return-value]


def _validate_polygon(points: Sequence[Tuple[float, float]], coordinate_space: str) -> None:
    if len(points) < 3:
        raise SurfaceManifestError("press point polygon requires at least three points")
    for x, y in points:
        _validate_coordinate(x, coordinate_space, "polygon x")
        _validate_coordinate(y, coordinate_space, "polygon y")


def _validate_rect(rect: Sequence[float], coordinate_space: str) -> None:
    if len(rect) != 4:
        raise SurfaceManifestError("widget rect requires four values")
    x, y, width, height = rect
    _validate_coordinate(x, coordinate_space, "widget x")
    _validate_coordinate(y, coordinate_space, "widget y")
    if width <= 0 or height <= 0:
        raise SurfaceManifestError("widget width and height must be positive")
    if coordinate_space == "normalized" and (x + width > 1.0 or y + height > 1.0):
        raise SurfaceManifestError("normalized widget rect must remain inside the surface")


def _validate_coordinate(value: float, coordinate_space: str, label: str) -> None:
    if coordinate_space == "normalized":
        if not 0.0 <= value <= 1.0:
            raise SurfaceManifestError("%s must be between 0 and 1" % label)
    elif value < 0:
        raise SurfaceManifestError("%s cannot be negative" % label)


def _validate_coordinate_space(value: str) -> None:
    if value not in _ALLOWED_COORDINATE_SPACES:
        raise SurfaceManifestError("coordinate_space must be normalized or pixels")


def _validate_resolution(value: Tuple[int, int]) -> None:
    width, height = value
    if width < 1 or height < 1 or width > 16384 or height > 16384:
        raise SurfaceManifestError("base_resolution is outside supported bounds")


def _validate_action(action: str) -> None:
    _require_text("press_point.action", action)
    if ":" not in action:
        raise SurfaceManifestError("press point action must use prefix:value")
    prefix, value = action.split(":", 1)
    if prefix not in _ALLOWED_ACTION_PREFIXES or not value.strip():
        raise SurfaceManifestError("press point action must be navigate:<scene> or emit:<event>")


def _validate_z_index(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not -1000 <= value <= 1000:
        raise SurfaceManifestError("z_index must be an integer between -1000 and 1000")


def _require_unique(values: Sequence[str], label: str) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise SurfaceManifestError("duplicate %s id: %s" % (label, value))
        seen.add(value)


def _reject_forbidden(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key)
            if name in _FORBIDDEN_KEYS:
                raise SurfaceManifestError("surface contains forbidden authority field: %s.%s" % (path, name))
            _reject_forbidden(item, "%s.%s" % (path, name))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_forbidden(item, "%s[%d]" % (path, index))


def _required_mapping_text(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise SurfaceManifestError("%s must be a non-empty string" % key)
    return item.strip()


def _require_text(label: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SurfaceManifestError("%s must be a non-empty string" % label)


def _require_sequence(label: str, value: Any) -> Sequence[Any]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SurfaceManifestError("%s must be a sequence" % label)
    return value


def _parse_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SurfaceManifestError("%s must be numeric" % label)
    return float(value)


def _parse_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SurfaceManifestError("%s must be an integer" % label)
    return value
