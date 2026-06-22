# SPDX-License-Identifier: GPL-3.0-only
"""Display-only observation widget contracts.

The interface layer receives sanitized observations from Runtime or the event
protocol. It does not decode CAN frames, select executors, or actuate hardware.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from velvet_interface.core.widget import Widget

_FORBIDDEN_FIELDS = {
    "action",
    "actuate",
    "actuation",
    "capability",
    "command",
    "executor",
    "executor_name",
    "hardware",
    "hardware_target",
    "route_id",
    "shell",
    "target",
    "token",
}


@dataclass(frozen=True)
class ObservationValue:
    """One sanitized value suitable for display on any Velvet surface."""

    name: str
    value: Any
    confidence: float
    observed_at: float
    source_profile: str
    unit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        _validate_value(self)
        document: Dict[str, Any] = {
            "name": self.name,
            "value": self.value,
            "confidence": float(self.confidence),
            "observed_at": float(self.observed_at),
            "source_profile": self.source_profile,
            "status": "observation-only",
            "read_only": True,
            "actuation_granted": False,
            "actuation_performed": False,
        }
        if self.unit is not None:
            document["unit"] = self.unit
        return document


class ObservationWidget(Widget):
    """Surface-agnostic base for bounded display-only observation panels."""

    def __init__(self, widget_id: str, max_values: int = 16) -> None:
        super().__init__(widget_id)
        if isinstance(max_values, bool) or not isinstance(max_values, int):
            raise TypeError("max_values must be an integer")
        if max_values < 1 or max_values > 64:
            raise ValueError("max_values must be between 1 and 64")
        self._max_values = max_values
        self._values: Tuple[ObservationValue, ...] = ()

    def update_observations(self, observations: Iterable[Mapping[str, Any]]) -> None:
        values: List[ObservationValue] = []
        for raw in observations:
            if not isinstance(raw, Mapping):
                raise ValueError("observation must be a mapping")
            forbidden = _FORBIDDEN_FIELDS.intersection(raw)
            if forbidden:
                raise ValueError(
                    "observation contains forbidden authority fields: %s"
                    % sorted(forbidden)
                )
            _require_safety_claims(raw)
            values.append(
                ObservationValue(
                    name=_required_text(raw, "name", alias="signal_name"),
                    value=raw.get("value"),
                    confidence=_required_number(raw, "confidence"),
                    observed_at=_required_number(raw, "observed_at", alias="timestamp"),
                    source_profile=_required_text(raw, "source_profile"),
                    unit=_optional_text(raw.get("unit"), "unit"),
                )
            )
            if len(values) >= self._max_values:
                break

        for value in values:
            _validate_value(value)
        self._values = tuple(values)

    @property
    def observations(self) -> Tuple[ObservationValue, ...]:
        return self._values

    def snapshot(self, now: Optional[float] = None, stale_after_s: float = 2.0) -> Dict[str, Any]:
        if isinstance(stale_after_s, bool) or not isinstance(stale_after_s, (int, float)):
            raise TypeError("stale_after_s must be numeric")
        if stale_after_s < 0:
            raise ValueError("stale_after_s cannot be negative")

        rendered: List[Dict[str, Any]] = []
        for value in self._values:
            item = value.to_dict()
            if now is None:
                item["freshness"] = "unknown"
            elif float(now) - value.observed_at > float(stale_after_s):
                item["freshness"] = "stale"
            else:
                item["freshness"] = "fresh"
            item["quality"] = "validated" if value.confidence >= 0.8 else "provisional"
            rendered.append(item)

        return {
            "widget_id": self.widget_id,
            "mode": "display-only",
            "status": "observation-only",
            "value_count": len(rendered),
            "values": rendered,
            "actuation_granted": False,
            "actuation_performed": False,
        }

    @abstractmethod
    def render(self, surface: "Surface", x: int, y: int) -> Any:
        """Render the current display-only snapshot on a concrete surface."""
        raise NotImplementedError


def _require_safety_claims(raw: Mapping[str, Any]) -> None:
    if raw.get("status") != "observation-only":
        raise ValueError("observation status must be observation-only")
    if raw.get("read_only") is not True:
        raise ValueError("observation must be read_only")
    if raw.get("actuation_granted") is not False:
        raise ValueError("observation cannot grant actuation")
    if raw.get("actuation_performed") is not False:
        raise ValueError("observation cannot claim actuation")


def _validate_value(value: ObservationValue) -> None:
    if not isinstance(value.name, str) or not value.name.strip():
        raise ValueError("observation name must be a non-empty string")
    if value.value is None or isinstance(value.value, (dict, list, tuple, set)):
        raise ValueError("observation value must be a scalar")
    if isinstance(value.confidence, bool) or not isinstance(value.confidence, (int, float)):
        raise ValueError("confidence must be numeric")
    if not 0.0 <= float(value.confidence) <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if isinstance(value.observed_at, bool) or not isinstance(value.observed_at, (int, float)):
        raise ValueError("observed_at must be numeric")
    if float(value.observed_at) < 0:
        raise ValueError("observed_at cannot be negative")
    if not isinstance(value.source_profile, str) or not value.source_profile.strip():
        raise ValueError("source_profile must be a non-empty string")
    if value.unit is not None and (not isinstance(value.unit, str) or not value.unit.strip()):
        raise ValueError("unit must be a non-empty string when provided")


def _required_text(raw: Mapping[str, Any], key: str, alias: Optional[str] = None) -> str:
    value = raw.get(key)
    if value is None and alias is not None:
        value = raw.get(alias)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % key)
    return value.strip()


def _required_number(raw: Mapping[str, Any], key: str, alias: Optional[str] = None) -> float:
    value = raw.get(key)
    if value is None and alias is not None:
        value = raw.get(alias)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % key)
    return float(value)


def _optional_text(value: Any, label: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % label)
    return value.strip()
