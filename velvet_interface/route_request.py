# SPDX-License-Identifier: GPL-3.0-only
"""Bounded route requests emitted by scenes and interface surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

_RESERVED_PARAMETER_NAMES = {
    "executor_name",
    "capability",
    "target",
    "profile_id",
    "session_id",
    "body_id",
    "surface",
}


@dataclass(frozen=True)
class SceneRouteRequest:
    intent_id: str
    route_id: str
    parameters: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "route_id": self.route_id,
            "parameters": dict(self.parameters),
        }


def build_scene_route_request(
    *,
    intent_id: str,
    route_id: str,
    parameters: Mapping[str, Any] | None = None,
) -> SceneRouteRequest:
    """Build a normalized request for Velvet Runtime's local gateway."""

    normalized_intent = _normalized(intent_id, "intent_id")
    normalized_route = _normalized(route_id, "route_id")
    values = dict(parameters or {})

    reserved = sorted(_RESERVED_PARAMETER_NAMES.intersection(values))
    if reserved:
        raise ValueError(f"scene parameters contain reserved authority fields: {reserved}")

    for key in values:
        _normalized(key, "parameter name")

    return SceneRouteRequest(
        intent_id=normalized_intent,
        route_id=normalized_route,
        parameters=values,
    )


def validate_scene_request_document(document: Mapping[str, Any]) -> SceneRouteRequest:
    """Validate a public scene request and reject extra top-level fields."""

    if not isinstance(document, Mapping):
        raise TypeError("scene route request must be a mapping")

    allowed = {"intent_id", "route_id", "parameters"}
    extra = sorted(set(document) - allowed)
    if extra:
        raise ValueError(f"scene route request contains unsupported fields: {extra}")

    parameters = document.get("parameters", {})
    if not isinstance(parameters, Mapping):
        raise ValueError("scene route request parameters must be a mapping")

    return build_scene_route_request(
        intent_id=document.get("intent_id"),
        route_id=document.get("route_id"),
        parameters=parameters,
    )


def _normalized(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty normalized string")
    normalized = " ".join(value.strip().split()).lower()
    if value != normalized:
        raise ValueError(f"{label} must already be normalized")
    return value
