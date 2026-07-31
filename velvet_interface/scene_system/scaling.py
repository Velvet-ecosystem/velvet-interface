# SPDX-License-Identifier: GPL-3.0-only
"""Resolution transforms for image-first Velvet surfaces."""

from __future__ import annotations

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SceneScaler:
    """Transform base-scene coordinates into a concrete display surface.

    ``stretch`` fills the target independently on each axis. ``contain`` keeps
    the whole background visible with letterboxing. ``cover`` fills the target
    while allowing symmetric cropping. The same transform is used for the image,
    press points, widget anchors, and reverse hit testing.
    """

    DEFAULT_BASE_RESOLUTION = (1280, 720)
    FIT_MODES = {"stretch", "contain", "cover"}

    def __init__(
        self,
        base_resolution: Tuple[int, int] = DEFAULT_BASE_RESOLUTION,
        target_resolution: Tuple[int, int] = DEFAULT_BASE_RESOLUTION,
        maintain_aspect_ratio: bool = False,
        fit_mode: str = "",
    ) -> None:
        self.base_width, self.base_height = _validate_resolution(
            "base_resolution", base_resolution
        )
        self.target_width, self.target_height = _validate_resolution(
            "target_resolution", target_resolution
        )

        if fit_mode:
            selected_fit = str(fit_mode).strip().lower()
        else:
            selected_fit = "contain" if maintain_aspect_ratio else "stretch"
        if selected_fit not in self.FIT_MODES:
            raise ValueError("fit_mode must be stretch, contain, or cover")

        self.fit_mode = selected_fit
        self.maintain_aspect_ratio = selected_fit != "stretch"
        self._calculate_scale_factors()

    def _calculate_scale_factors(self) -> None:
        width_scale = self.target_width / self.base_width
        height_scale = self.target_height / self.base_height

        if self.fit_mode == "stretch":
            self.scale_x = width_scale
            self.scale_y = height_scale
        else:
            scale = min(width_scale, height_scale)
            if self.fit_mode == "cover":
                scale = max(width_scale, height_scale)
            self.scale_x = scale
            self.scale_y = scale

        scaled_width = self.base_width * self.scale_x
        scaled_height = self.base_height * self.scale_y
        self.offset_x = (self.target_width - scaled_width) / 2.0
        self.offset_y = (self.target_height - scaled_height) / 2.0

        logger.debug(
            "Scene transform fit=%s scale=(%.4f, %.4f) offset=(%.2f, %.2f)",
            self.fit_mode,
            self.scale_x,
            self.scale_y,
            self.offset_x,
            self.offset_y,
        )

    def scale_point(self, x: float, y: float) -> Tuple[float, float]:
        return (
            float(x) * self.scale_x + self.offset_x,
            float(y) * self.scale_y + self.offset_y,
        )

    def unscale_point(self, x: float, y: float) -> Tuple[float, float]:
        return (
            (float(x) - self.offset_x) / self.scale_x,
            (float(y) - self.offset_y) / self.scale_y,
        )

    def scale_size(self, width: float, height: float) -> Tuple[float, float]:
        return (float(width) * self.scale_x, float(height) * self.scale_y)

    def scale_rect(
        self, x: float, y: float, width: float, height: float
    ) -> Tuple[int, int, int, int]:
        left, top = self.scale_point(x, y)
        scaled_width, scaled_height = self.scale_size(width, height)
        return (
            int(round(left)),
            int(round(top)),
            max(1, int(round(scaled_width))),
            max(1, int(round(scaled_height))),
        )

    def get_scaled_dimensions(self) -> Tuple[int, int]:
        return (
            max(1, int(round(self.base_width * self.scale_x))),
            max(1, int(round(self.base_height * self.scale_y))),
        )

    def get_letterbox_rect(self) -> Tuple[int, int, int, int]:
        width, height = self.get_scaled_dimensions()
        return (
            int(round(self.offset_x)),
            int(round(self.offset_y)),
            width,
            height,
        )

    def contains_target_point(self, x: float, y: float) -> bool:
        base_x, base_y = self.unscale_point(x, y)
        return 0.0 <= base_x <= self.base_width and 0.0 <= base_y <= self.base_height

    def normalized_target_point(self, x: float, y: float) -> Tuple[float, float]:
        base_x, base_y = self.unscale_point(x, y)
        return (base_x / self.base_width, base_y / self.base_height)


def _validate_resolution(
    label: str, resolution: Tuple[int, int]
) -> Tuple[int, int]:
    if not isinstance(resolution, (tuple, list)) or len(resolution) != 2:
        raise ValueError("%s must be a width-height pair" % label)
    width, height = resolution
    if (
        isinstance(width, bool)
        or isinstance(height, bool)
        or not isinstance(width, int)
        or not isinstance(height, int)
        or width < 1
        or height < 1
    ):
        raise ValueError("%s values must be positive integers" % label)
    return int(width), int(height)
