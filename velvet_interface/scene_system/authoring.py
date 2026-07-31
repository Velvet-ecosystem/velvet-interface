# SPDX-License-Identifier: GPL-3.0-only
"""Pure authoring model for image-first Velvet surface layouts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from velvet_interface.scene_system.scaling import SceneScaler
from velvet_interface.scene_system.surface_manifest import (
    BackgroundAsset,
    PressPoint,
    SurfaceManifest,
    SurfaceManifestLoader,
    WidgetPlacement,
)


@dataclass
class SurfaceLayoutAuthoringSession:
    """Build a surface manifest using coordinates captured on a target screen."""

    name: str
    background_path: str
    base_resolution: Tuple[int, int]
    fit_mode: str = "cover"
    press_points: List[PressPoint] = field(default_factory=list)
    widgets: List[WidgetPlacement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    enter_transition: str = "none"
    exit_transition: str = "none"

    def __post_init__(self) -> None:
        # Constructing the asset and an empty manifest applies all base checks.
        BackgroundAsset(self.background_path, self.fit_mode)
        SurfaceManifest(
            name=self.name,
            base_resolution=self.base_resolution,
            background=BackgroundAsset(self.background_path, self.fit_mode),
        )

    @classmethod
    def from_manifest(cls, manifest: SurfaceManifest) -> "SurfaceLayoutAuthoringSession":
        return cls(
            name=manifest.name,
            background_path=manifest.background.image_path,
            base_resolution=manifest.base_resolution,
            fit_mode=manifest.background.fit,
            press_points=list(manifest.press_points),
            widgets=list(manifest.widgets),
            metadata=dict(manifest.metadata),
            enter_transition=manifest.enter_transition,
            exit_transition=manifest.exit_transition,
        )

    @classmethod
    def load(cls, path: str) -> "SurfaceLayoutAuthoringSession":
        manifest = SurfaceManifestLoader().load(path, require_background=True)
        return cls.from_manifest(manifest)

    def scaler(self, target_resolution: Tuple[int, int]) -> SceneScaler:
        return SceneScaler(
            base_resolution=self.base_resolution,
            target_resolution=target_resolution,
            fit_mode=self.fit_mode,
        )

    def normalized_point(
        self,
        x: float,
        y: float,
        target_resolution: Tuple[int, int],
    ) -> Optional[Tuple[float, float]]:
        transform = self.scaler(target_resolution)
        if not transform.contains_target_point(x, y):
            return None
        nx, ny = transform.normalized_target_point(x, y)
        return (round(nx, 6), round(ny, 6))

    def add_press_point_from_target(
        self,
        point_id: str,
        action: str,
        target_points: Sequence[Tuple[float, float]],
        target_resolution: Tuple[int, int],
        label: str = "",
        accessibility_label: str = "",
        z_index: int = 10,
    ) -> PressPoint:
        normalized = []
        for x, y in target_points:
            point = self.normalized_point(x, y, target_resolution)
            if point is None:
                raise ValueError("press point vertex is outside the background content")
            normalized.append(point)
        press_point = PressPoint(
            point_id=point_id,
            polygon=tuple(normalized),
            action=action,
            coordinate_space="normalized",
            label=label,
            accessibility_label=accessibility_label,
            z_index=z_index,
        )
        self._replace_press_point(press_point)
        return press_point

    def add_widget_from_target(
        self,
        widget_id: str,
        target_rect: Tuple[float, float, float, float],
        target_resolution: Tuple[int, int],
        z_index: int = 20,
        visible_in: Sequence[str] = (),
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> WidgetPlacement:
        x, y, width, height = target_rect
        if width <= 0 or height <= 0:
            raise ValueError("widget target rectangle must have positive size")
        first = self.normalized_point(x, y, target_resolution)
        second = self.normalized_point(x + width, y + height, target_resolution)
        if first is None or second is None:
            raise ValueError("widget rectangle is outside the background content")
        nx, ny = first
        right, bottom = second
        widget = WidgetPlacement(
            widget_id=widget_id,
            rect=(nx, ny, round(right - nx, 6), round(bottom - ny, 6)),
            coordinate_space="normalized",
            z_index=z_index,
            visible_in=tuple(visible_in),
            metadata=dict(metadata or {}),
        )
        self._replace_widget(widget)
        return widget

    def remove_press_point(self, point_id: str) -> None:
        self.press_points = [item for item in self.press_points if item.point_id != point_id]

    def remove_widget(self, widget_id: str) -> None:
        self.widgets = [item for item in self.widgets if item.widget_id != widget_id]

    def manifest(self) -> SurfaceManifest:
        return SurfaceManifest(
            name=self.name,
            base_resolution=self.base_resolution,
            background=BackgroundAsset(self.background_path, self.fit_mode),
            press_points=tuple(self.press_points),
            widgets=tuple(self.widgets),
            enter_transition=self.enter_transition,
            exit_transition=self.exit_transition,
            metadata=dict(self.metadata),
        )

    def to_mapping(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        manifest = self.manifest()
        image_path = Path(manifest.background.image_path)
        image_value = str(image_path)
        if output_path is not None:
            try:
                image_value = str(image_path.relative_to(output_path.parent))
            except ValueError:
                image_value = str(image_path)

        return {
            "schema": manifest.schema,
            "name": manifest.name,
            "base_resolution": list(manifest.base_resolution),
            "background": {
                "image": image_value,
                "fit": manifest.background.fit,
                "alt_text": manifest.background.alt_text,
            },
            "press_points": [
                {
                    "id": item.point_id,
                    "coordinate_space": "normalized",
                    "polygon": [list(point) for point in item.polygon],
                    "action": item.action,
                    "label": item.label,
                    "accessibility_label": item.accessibility_label,
                    "z_index": item.z_index,
                    "enabled": item.enabled,
                    "metadata": dict(item.metadata),
                }
                for item in manifest.press_points
            ],
            "widgets": [
                {
                    "widget_id": item.widget_id,
                    "coordinate_space": "normalized",
                    "rect": list(item.rect),
                    "z_index": item.z_index,
                    "visible_in": list(item.visible_in),
                    "metadata": dict(item.metadata),
                }
                for item in manifest.widgets
            ],
            "transitions": {
                "enter": manifest.enter_transition,
                "exit": manifest.exit_transition,
            },
            "metadata": dict(manifest.metadata),
        }

    def save(self, path: str) -> Path:
        if yaml is None:
            raise ImportError("PyYAML not installed. Install with: pip install PyYAML")
        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        document = self.to_mapping(output)
        temporary = output.with_name(".%s.tmp" % output.name)
        temporary.write_text(
            yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        temporary.replace(output)
        return output

    def _replace_press_point(self, press_point: PressPoint) -> None:
        self.remove_press_point(press_point.point_id)
        self.press_points.append(press_point)

    def _replace_widget(self, widget: WidgetPlacement) -> None:
        self.remove_widget(widget.widget_id)
        self.widgets.append(widget)
