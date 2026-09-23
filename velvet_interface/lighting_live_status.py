# SPDX-License-Identifier: GPL-3.0-only
"""Read-only lighting context projected from canonical environmental evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from velvet_interface.climate_live_status import load_climate_live_status


@dataclass(frozen=True)
class LightingLiveStatus:
    available: bool
    state: str
    freshness: str
    ambient_light_lux: Optional[float] = None
    observer: Optional[str] = None
    lighting_observer_state: str = "UNBOUND"
    physical_control_state: str = "DISABLED"
    message: str = ""


def load_lighting_live_status(
    body_path: Path,
    now_monotonic: Optional[float] = None,
) -> LightingLiveStatus:
    """Project actual ambient-light context without inventing fixture state."""

    climate = load_climate_live_status(body_path, now_monotonic=now_monotonic)
    if not climate.available:
        return LightingLiveStatus(
            available=False,
            state="UNAVAILABLE",
            freshness=climate.freshness,
            message=(
                "Lighting context awaiting genuine ambient-light evidence; "
                "fixture observation remains unbound"
            ),
        )

    return LightingLiveStatus(
        available=True,
        state=climate.state,
        freshness=climate.freshness,
        ambient_light_lux=climate.ambient_light_lux,
        observer=climate.owning_handmaiden,
        message=_message(climate.state, climate.freshness),
    )


def _message(state: str, freshness: str) -> str:
    if state == "FAILED":
        return "Ambient-light sensing failed; lighting fixture state remains unknown"
    if state == "DEGRADED":
        return "Ambient-light sensing is degraded; lighting fixture state remains unknown"
    if state == "STALE" or freshness == "stale":
        return "Last ambient-light observation is stale; lighting fixture state remains unknown"
    return (
        "Live ambient-light context only; starlight, cabin accents, scenes, and "
        "brightness remain unbound until a reviewed lighting observer exists"
    )
