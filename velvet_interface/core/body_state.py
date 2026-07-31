# SPDX-License-Identifier: GPL-3.0-only
"""Read-only body-state projection for Velvet Interface.

The store consumes standard SensorPacket and HealthEvent Event Protocol records
and produces bounded presentation state. It never selects routes, executors,
capabilities, or hardware targets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


_FORBIDDEN_AUTHORITY_FIELDS = {
    "action",
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

_ALLOWED_SENSOR_HEALTH = {
    "ONLINE",
    "DEGRADED",
    "FAILED",
    "RECOVERING",
    "RECOVERED",
    "UNKNOWN",
}

_ALLOWED_HEALTH_EVENTS = {
    "ONLINE",
    "READY",
    "DEGRADED",
    "FAILED",
    "RECOVERING",
    "RECOVERED",
    "OFFLINE",
    "STALE",
    "CALIBRATION_REQUIRED",
}

_ALLOWED_SEVERITIES = {"INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class SensorStatusView:
    module_id: str
    node_id: str
    owning_handmaiden: str
    sensor_type: str
    interface_type: str
    health_state: str
    confidence: float
    observed_at: float
    monotonic_time: float
    stale_after_ms: int
    receipt_id: str
    calibration_version: str
    payload: Mapping[str, Any]
    degraded_reason: Optional[str] = None
    raw_reference: Optional[str] = None

    def freshness(self, now_monotonic: Optional[float]) -> str:
        if now_monotonic is None:
            return "unknown"
        if now_monotonic < self.monotonic_time:
            return "fresh"
        age_ms = (float(now_monotonic) - self.monotonic_time) * 1000.0
        return "stale" if age_ms > float(self.stale_after_ms) else "fresh"

    def to_dict(self, now_monotonic: Optional[float] = None) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "node_id": self.node_id,
            "owning_handmaiden": self.owning_handmaiden,
            "sensor_type": self.sensor_type,
            "interface_type": self.interface_type,
            "health_state": self.health_state,
            "confidence": self.confidence,
            "observed_at": self.observed_at,
            "freshness": self.freshness(now_monotonic),
            "receipt_id": self.receipt_id,
            "calibration_version": self.calibration_version,
            "payload": dict(self.payload),
            "degraded_reason": self.degraded_reason,
            "raw_reference": self.raw_reference,
            "status": "observation-only",
            "read_only": True,
            "actuation_granted": False,
            "actuation_performed": False,
        }


@dataclass(frozen=True)
class HealthStatusView:
    event_id: str
    event_type: str
    module_id: str
    node_id: str
    owning_handmaiden: str
    observed_at: float
    severity: str
    state_before: str
    state_after: str
    confidence: float
    receipt_id: str
    diagnostic_payload: Mapping[str, Any]
    recovery_action: Optional[str] = None
    fallback_owner: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "module_id": self.module_id,
            "node_id": self.node_id,
            "owning_handmaiden": self.owning_handmaiden,
            "observed_at": self.observed_at,
            "severity": self.severity,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "confidence": self.confidence,
            "receipt_id": self.receipt_id,
            "diagnostic_payload": dict(self.diagnostic_payload),
            "recovery_action": self.recovery_action,
            "fallback_owner": self.fallback_owner,
            "status": "health-observation",
            "read_only": True,
            "actuation_granted": False,
            "actuation_performed": False,
        }


@dataclass(frozen=True)
class BodyStateSnapshot:
    sensors: Tuple[SensorStatusView, ...]
    health_events: Tuple[HealthStatusView, ...]
    presence_state: str
    summary: str
    receipt_ids: Tuple[str, ...]

    def to_dict(self, now_monotonic: Optional[float] = None) -> Dict[str, Any]:
        return {
            "presence_state": self.presence_state,
            "summary": self.summary,
            "sensor_count": len(self.sensors),
            "health_event_count": len(self.health_events),
            "sensors": [item.to_dict(now_monotonic) for item in self.sensors],
            "health_events": [item.to_dict() for item in self.health_events],
            "receipt_ids": list(self.receipt_ids),
            "mode": "display-only",
            "read_only": True,
            "actuation_granted": False,
            "actuation_performed": False,
        }


class BodyStateStore:
    """Latest-value projection of trusted body observation records."""

    def __init__(self) -> None:
        self._sensors = {}  # type: Dict[str, SensorStatusView]
        self._health = {}  # type: Dict[str, HealthStatusView]

    def apply(self, record: Mapping[str, Any]) -> None:
        if not isinstance(record, Mapping):
            raise TypeError("body-state record must be a mapping")
        _reject_authority_fields(record)

        family = str(record.get("family", "")).strip().lower()
        event_type = str(record.get("event_type", "")).strip().upper()
        payload = record.get("payload")
        if not isinstance(payload, Mapping):
            raise ValueError("body-state Event Protocol record requires a payload mapping")

        if family == "sensor" or event_type == "SENSOR_PACKET_OBSERVED":
            sensor = _sensor_from_payload(payload)
            self._sensors[sensor.module_id] = sensor
            return
        if family == "health" or event_type.startswith("HEALTH_"):
            health = _health_from_payload(payload)
            self._health[health.module_id] = health
            return
        raise ValueError("unsupported body-state record family")

    def apply_many(self, records: Iterable[Mapping[str, Any]]) -> None:
        for record in records:
            self.apply(record)

    def snapshot(self, now_monotonic: Optional[float] = None) -> BodyStateSnapshot:
        sensors = tuple(sorted(self._sensors.values(), key=lambda item: item.module_id))
        health_events = tuple(sorted(self._health.values(), key=lambda item: item.module_id))

        presence = "observing"
        states = {item.health_state for item in sensors}
        states.update(item.state_after for item in health_events)
        severities = {item.severity for item in health_events}
        stale_count = sum(
            1 for item in sensors if item.freshness(now_monotonic) == "stale"
        )

        if "FAILED" in states or "CRITICAL" in severities:
            presence = "critical"
        elif "RECOVERING" in states:
            presence = "recovery"
        elif "DEGRADED" in states or stale_count or "ERROR" in severities:
            presence = "warning"
        elif not sensors and not health_events:
            presence = "idle"

        degraded_count = sum(
            1 for item in sensors if item.health_state in {"DEGRADED", "FAILED"}
        )
        summary = "%d sensors, %d health records" % (len(sensors), len(health_events))
        if stale_count:
            summary += ", %d stale" % stale_count
        if degraded_count:
            summary += ", %d degraded or failed" % degraded_count

        receipt_ids = []
        for item in sensors:
            if item.receipt_id and item.receipt_id not in receipt_ids:
                receipt_ids.append(item.receipt_id)
        for item in health_events:
            if item.receipt_id and item.receipt_id not in receipt_ids:
                receipt_ids.append(item.receipt_id)

        return BodyStateSnapshot(
            sensors=sensors,
            health_events=health_events,
            presence_state=presence,
            summary=summary,
            receipt_ids=tuple(receipt_ids),
        )


def _sensor_from_payload(payload: Mapping[str, Any]) -> SensorStatusView:
    health_state = _required_enum(payload, "health_state", _ALLOWED_SENSOR_HEALTH)
    confidence = _required_confidence(payload)
    stale_after_ms = _required_positive_int(payload, "stale_after_ms")
    sensor_payload = payload.get("payload")
    if not isinstance(sensor_payload, Mapping):
        raise ValueError("sensor payload must be a mapping")
    return SensorStatusView(
        module_id=_required_text(payload, "module_id"),
        node_id=_required_text(payload, "node_id"),
        owning_handmaiden=_required_text(payload, "owning_handmaiden"),
        sensor_type=_required_text(payload, "sensor_type"),
        interface_type=_required_text(payload, "interface_type"),
        health_state=health_state,
        confidence=confidence,
        observed_at=_required_non_negative_number(payload, "timestamp"),
        monotonic_time=_required_non_negative_number(payload, "monotonic_time"),
        stale_after_ms=stale_after_ms,
        receipt_id=_required_text(payload, "receipt_id"),
        calibration_version=_required_text(payload, "calibration_version"),
        payload=dict(sensor_payload),
        degraded_reason=_optional_text(payload.get("degraded_reason"), "degraded_reason"),
        raw_reference=_optional_text(payload.get("raw_reference"), "raw_reference"),
    )


def _health_from_payload(payload: Mapping[str, Any]) -> HealthStatusView:
    diagnostic = payload.get("diagnostic_payload")
    if not isinstance(diagnostic, Mapping):
        raise ValueError("diagnostic_payload must be a mapping")
    return HealthStatusView(
        event_id=_required_text(payload, "event_id"),
        event_type=_required_enum(payload, "event_type", _ALLOWED_HEALTH_EVENTS),
        module_id=_required_text(payload, "module_id"),
        node_id=_required_text(payload, "node_id"),
        owning_handmaiden=_required_text(payload, "owning_handmaiden"),
        observed_at=_required_non_negative_number(payload, "timestamp"),
        severity=_required_enum(payload, "severity", _ALLOWED_SEVERITIES),
        state_before=_required_enum(payload, "state_before", _ALLOWED_SENSOR_HEALTH),
        state_after=_required_enum(payload, "state_after", _ALLOWED_SENSOR_HEALTH),
        confidence=_required_confidence(payload),
        receipt_id=_required_text(payload, "receipt_id"),
        diagnostic_payload=dict(diagnostic),
        recovery_action=_optional_text(payload.get("recovery_action"), "recovery_action"),
        fallback_owner=_optional_text(payload.get("fallback_owner"), "fallback_owner"),
    )


def _reject_authority_fields(value: Any, path: str = "record") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            text = str(key)
            if text in _FORBIDDEN_AUTHORITY_FIELDS:
                raise ValueError("body-state record contains forbidden authority field: %s.%s" % (path, text))
            _reject_authority_fields(item, "%s.%s" % (path, text))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_authority_fields(item, "%s[%d]" % (path, index))


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % key)
    return value.strip()


def _optional_text(value: Any, key: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string when provided" % key)
    return value.strip()


def _required_enum(payload: Mapping[str, Any], key: str, allowed: set) -> str:
    value = _required_text(payload, key).upper()
    if value not in allowed:
        raise ValueError("unsupported %s: %s" % (key, value))
    return value


def _required_confidence(payload: Mapping[str, Any]) -> float:
    value = payload.get("confidence")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("confidence must be numeric")
    confidence = float(value)
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")
    return confidence


def _required_non_negative_number(payload: Mapping[str, Any], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % key)
    number = float(value)
    if number < 0:
        raise ValueError("%s cannot be negative" % key)
    return number


def _required_positive_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an integer" % key)
    if value <= 0:
        raise ValueError("%s must be positive" % key)
    return value
