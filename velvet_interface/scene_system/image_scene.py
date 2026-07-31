# SPDX-License-Identifier: GPL-3.0-only
"""Image-first scene with press points and widget placements."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional, Tuple

from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface
from velvet_interface.scene_system.regions import PolygonRegion, RegionManager
from velvet_interface.scene_system.scaling import SceneScaler

logger = logging.getLogger(__name__)


class ImageScene(Scene):
    """One background image, bounded press points, and widget anchors.

    Coordinates remain in the declared base resolution. A single SceneScaler
    transforms the background, press points, widgets, and target clicks. This
    prevents a surface from drifting when the real display resolution differs
    from the image used to author the scene.
    """

    def __init__(self, scene_data: Dict[str, Any]) -> None:
        if not isinstance(scene_data, dict):
            raise TypeError("scene_data must be a dictionary")
        name = scene_data.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("image scene requires a non-empty name")
        super().__init__(name.strip())

        self.scene_data = dict(scene_data)
        self.background_path = scene_data.get("background")
        self.background_fit = str(scene_data.get("background_fit", "stretch")).lower()
        if self.background_fit not in SceneScaler.FIT_MODES:
            raise ValueError("background_fit must be stretch, contain, or cover")
        self.background_alt_text = str(
            scene_data.get("background_alt_text", "Velvet interface background")
        )

        base_res = scene_data.get("base_resolution", [1280, 720])
        if not isinstance(base_res, (list, tuple)) or len(base_res) != 2:
            raise ValueError("base_resolution must be [width, height]")
        self.base_resolution = (int(base_res[0]), int(base_res[1]))
        if self.base_resolution[0] < 1 or self.base_resolution[1] < 1:
            raise ValueError("base_resolution values must be positive")

        self.region_manager = RegionManager()
        self._load_regions()
        self.widget_placements = self._load_widget_placements()
        self.scaler = None  # type: Optional[SceneScaler]

        transitions = scene_data.get("transitions", {})
        if not isinstance(transitions, Mapping):
            raise ValueError("transitions must be a mapping")
        self.enter_transition = str(transitions.get("enter", "none"))
        self.exit_transition = str(transitions.get("exit", "none"))

    def _load_regions(self) -> None:
        raw_regions = self.scene_data.get("regions", [])
        if not isinstance(raw_regions, list):
            raise ValueError("regions must be a list")

        ordered = sorted(
            raw_regions,
            key=lambda item: int(item.get("z_index", 10)) if isinstance(item, Mapping) else 10,
            reverse=True,
        )
        for region_data in ordered:
            if not isinstance(region_data, Mapping):
                raise ValueError("each region must be a mapping")
            metadata = region_data.get("metadata", {})
            if not isinstance(metadata, Mapping):
                raise ValueError("region metadata must be a mapping")
            metadata_copy = dict(metadata)
            metadata_copy["enabled"] = region_data.get("enabled", True)
            metadata_copy["z_index"] = int(region_data.get("z_index", 10))
            region = PolygonRegion(
                name=str(region_data["name"]),
                polygon=[tuple(point) for point in region_data["polygon"]],
                action=str(region_data["action"]),
                metadata=metadata_copy,
            )
            self.region_manager.add_region(region)

    def _load_widget_placements(self) -> Tuple[Dict[str, Any], ...]:
        raw_widgets = self.scene_data.get("widgets", [])
        if not isinstance(raw_widgets, list):
            raise ValueError("widgets must be a list")
        placements = []  # type: List[Dict[str, Any]]
        seen = set()
        for item in raw_widgets:
            if not isinstance(item, Mapping):
                raise ValueError("each widget placement must be a mapping")
            widget_id = item.get("widget_id")
            rect = item.get("rect")
            if not isinstance(widget_id, str) or not widget_id.strip():
                raise ValueError("widget_id must be a non-empty string")
            if widget_id in seen:
                raise ValueError("duplicate widget placement: %s" % widget_id)
            if not isinstance(rect, (list, tuple)) or len(rect) != 4:
                raise ValueError("widget rect must be [x, y, width, height]")
            x, y, width, height = [float(value) for value in rect]
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                raise ValueError("widget rect values are invalid")
            visible_in = item.get("visible_in", [])
            if not isinstance(visible_in, (list, tuple)):
                raise ValueError("widget visible_in must be a list")
            metadata = item.get("metadata", {})
            if not isinstance(metadata, Mapping):
                raise ValueError("widget metadata must be a mapping")
            placements.append(
                {
                    "widget_id": widget_id.strip(),
                    "rect": (x, y, width, height),
                    "z_index": int(item.get("z_index", 20)),
                    "visible_in": tuple(str(value) for value in visible_in),
                    "metadata": dict(metadata),
                }
            )
            seen.add(widget_id)
        placements.sort(key=lambda item: item["z_index"])
        return tuple(placements)

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        super().on_enter(context)
        logger.info("Image scene entered: %s", self.scene_id)

    def on_exit(self) -> None:
        super().on_exit()
        logger.info("Image scene exited: %s", self.scene_id)

    def setup_scaling(self, target_resolution: Tuple[int, int]) -> None:
        """Create the one transform shared by every scene element."""

        self.scaler = SceneScaler(
            base_resolution=self.base_resolution,
            target_resolution=target_resolution,
            fit_mode=self.background_fit,
        )
        logger.debug(
            "Scene transform set: %s -> %s (%s)",
            self.base_resolution,
            target_resolution,
            self.background_fit,
        )

    def handle_click(self, x: float, y: float) -> Optional[str]:
        """Return a bounded presentation action for one target-space press."""

        if self.scaler is None:
            base_x, base_y = float(x), float(y)
        else:
            if not self.scaler.contains_target_point(x, y):
                return None
            base_x, base_y = self.scaler.unscale_point(x, y)

        region = self.region_manager.find_region_at(base_x, base_y)
        if region is None:
            return None
        if region.metadata.get("enabled") is not True:
            logger.info("Disabled region pressed: %s", region.name)
            return None
        logger.info("Region pressed: %s -> %s", region.name, region.action)
        return region.action

    def scaled_region_polygon(
        self, region: PolygonRegion
    ) -> Tuple[Tuple[float, float], ...]:
        if self.scaler is None:
            return tuple((float(x), float(y)) for x, y in region.polygon)
        return tuple(self.scaler.scale_point(x, y) for x, y in region.polygon)

    def widget_rect(self, placement: Mapping[str, Any]) -> Tuple[int, int, int, int]:
        rect = placement.get("rect")
        if not isinstance(rect, (list, tuple)) or len(rect) != 4:
            raise ValueError("widget placement has invalid rect")
        x, y, width, height = [float(value) for value in rect]
        if self.scaler is None:
            return (int(round(x)), int(round(y)), int(round(width)), int(round(height)))
        return self.scaler.scale_rect(x, y, width, height)

    def normalized_point(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        """Convert a target press into authoring coordinates between zero and one."""

        if self.scaler is None:
            width, height = self.base_resolution
            base_x, base_y = float(x), float(y)
            if not 0 <= base_x <= width or not 0 <= base_y <= height:
                return None
            return (base_x / width, base_y / height)
        if not self.scaler.contains_target_point(x, y):
            return None
        normalized_x, normalized_y = self.scaler.normalized_target_point(x, y)
        return (round(normalized_x, 6), round(normalized_y, 6))

    def placement_snapshot(self) -> Dict[str, Any]:
        """Return geometry-only state for previews and authoring tools."""

        return {
            "scene_id": self.scene_id,
            "background": self.background_path,
            "background_fit": self.background_fit,
            "base_resolution": self.base_resolution,
            "press_points": [
                {
                    "id": region.name,
                    "polygon": self.scaled_region_polygon(region),
                    "action": region.action,
                    "enabled": region.metadata.get("enabled") is True,
                    "z_index": region.metadata.get("z_index", 10),
                }
                for region in self.region_manager.regions
            ],
            "widgets": [
                dict(placement, target_rect=self.widget_rect(placement))
                for placement in self.widget_placements
            ],
            "read_only": True,
            "actuation_granted": False,
            "actuation_performed": False,
        }

    def render(self, surface: Surface) -> Any:
        raise NotImplementedError("ImageScene.render() must use a surface adapter")
