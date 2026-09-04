# SPDX-License-Identifier: GPL-3.0-only
"""Read-only projection of Runtime node/resource evidence for the Founder UI.

The Interface does not own the distributed node registry. It reads the append-only
Runtime lifecycle journal for functional heartbeats and may consume an injected
read-only body-capacity snapshot provider. Missing evidence stays unavailable.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple


NODE_EVENT = "NODE_ADVERTISEMENT_PUBLISHED"
LIFECYCLE_SCHEMA = "velvet.runtime.lifecycle_journal.v1"
DEFAULT_MAX_HEARTBEAT_AGE_SECONDS = 20.0
DEFAULT_MAX_JOURNAL_BYTES = 1024 * 1024
DEFAULT_MAX_JOURNAL_LINES = 2048


@dataclass(frozen=True)
class BodyNodeStatus:
    node_id: str
    organ: str
    state: str
    availability: str
    last_heartbeat: Optional[float]
    heartbeat_age_seconds: Optional[float]
    health: Optional[float]
    current_load: Optional[float]
    current_tasks: Optional[int]
    max_concurrent_tasks: Optional[int]
    capabilities: Tuple[str, ...]
    body_verified: bool
    continuity_verified: bool
    resource_visible: bool


@dataclass(frozen=True)
class BodyResourceTotal:
    kind: str
    unit: str
    capacity: float
    available: float
    resource_count: int


@dataclass(frozen=True)
class BodyNodesStatus:
    nodes: Tuple[BodyNodeStatus, ...]
    resource_totals: Tuple[BodyResourceTotal, ...]
    body_id: Optional[str]
    resource_snapshot_available: bool
    message: str


def load_body_nodes_status(
    lifecycle_journal: Path,
    *,
    resource_snapshot_provider: Optional[Callable[[float], Any]] = None,
    now: Optional[float] = None,
    max_heartbeat_age_seconds: float = DEFAULT_MAX_HEARTBEAT_AGE_SECONDS,
    local_node_id: str = "founder",
) -> BodyNodesStatus:
    """Project current node evidence without acquiring Runtime authority."""

    timestamp = time.time() if now is None else _nonnegative_number(now, "now")
    if (
        isinstance(max_heartbeat_age_seconds, bool)
        or not isinstance(max_heartbeat_age_seconds, (int, float))
        or float(max_heartbeat_age_seconds) <= 0.0
    ):
        raise ValueError("max_heartbeat_age_seconds must be positive")
    if not isinstance(local_node_id, str) or not local_node_id.strip():
        raise ValueError("local_node_id must be non-empty text")
    local_id = local_node_id.strip()

    latest = _latest_node_records(Path(lifecycle_journal))
    resource_node_ids = set()  # type: set[str]
    resource_totals = ()  # type: Tuple[BodyResourceTotal, ...]
    body_id = None  # type: Optional[str]
    resource_available = False

    if resource_snapshot_provider is not None:
        if not callable(resource_snapshot_provider):
            raise TypeError("resource_snapshot_provider must be callable or None")
        try:
            snapshot = resource_snapshot_provider(timestamp)
            body_id, resource_node_ids, resource_totals = _normalize_resource_snapshot(snapshot)
            resource_available = True
        except Exception:
            # Resource transport is supplementary to functional node visibility.
            resource_available = False

    nodes = []
    for node_id, payload in latest.items():
        last_heartbeat = _optional_number(payload.get("last_heartbeat"))
        age = None if last_heartbeat is None else max(0.0, timestamp - last_heartbeat)
        availability = _text_or(payload.get("availability"), "unknown").lower()
        state = _functional_state(availability, age, float(max_heartbeat_age_seconds))
        nodes.append(
            BodyNodeStatus(
                node_id=node_id,
                organ=_text_or(payload.get("organ"), "unknown"),
                state=state,
                availability=availability,
                last_heartbeat=last_heartbeat,
                heartbeat_age_seconds=age,
                health=_bounded_fraction(payload.get("health")),
                current_load=_bounded_fraction(payload.get("current_load")),
                current_tasks=_optional_nonnegative_int(payload.get("current_tasks")),
                max_concurrent_tasks=_optional_nonnegative_int(
                    payload.get("max_concurrent_tasks")
                ),
                capabilities=_text_tuple(payload.get("capabilities")),
                body_verified=payload.get("body_verified") is True,
                continuity_verified=payload.get("continuity_verified") is True,
                resource_visible=node_id in resource_node_ids,
            )
        )

    known_ids = {item.node_id for item in nodes}
    for node_id in sorted(resource_node_ids - known_ids):
        nodes.append(
            BodyNodeStatus(
                node_id=node_id,
                organ="local host" if node_id == local_id else "resource host",
                state="LOCAL" if node_id == local_id else "RESOURCE",
                availability="resource-visible",
                last_heartbeat=None,
                heartbeat_age_seconds=None,
                health=None,
                current_load=None,
                current_tasks=None,
                max_concurrent_tasks=None,
                capabilities=(),
                body_verified=True,
                continuity_verified=True,
                resource_visible=True,
            )
        )

    nodes.sort(key=lambda item: (0 if item.node_id == local_id else 1, item.node_id))
    if nodes:
        message = "Verified Runtime evidence. Touch a node for details."
    else:
        message = "Awaiting verified node heartbeats."
    if not resource_available:
        message += " Resource snapshot unavailable."

    return BodyNodesStatus(
        nodes=tuple(nodes),
        resource_totals=resource_totals,
        body_id=body_id,
        resource_snapshot_available=resource_available,
        message=message,
    )


def _latest_node_records(path: Path) -> Dict[str, Mapping[str, Any]]:
    latest = {}  # type: Dict[str, Mapping[str, Any]]
    for line in _bounded_tail_lines(path):
        try:
            record = json.loads(line)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(record, Mapping):
            continue
        if record.get("schema") != LIFECYCLE_SCHEMA:
            continue
        if record.get("event_type") != NODE_EVENT:
            continue
        payload = record.get("payload")
        if not isinstance(payload, Mapping):
            continue
        if payload.get("authority") != "none":
            continue
        if payload.get("transport_only") is not True:
            continue
        if payload.get("canonical") is not False:
            continue
        node_id = payload.get("node_id")
        if not isinstance(node_id, str) or not node_id.strip():
            continue
        node = node_id.strip()
        heartbeat = _optional_number(payload.get("last_heartbeat"))
        prior = latest.get(node)
        prior_heartbeat = (
            None if prior is None else _optional_number(prior.get("last_heartbeat"))
        )
        if prior is None or (
            heartbeat is not None
            and (prior_heartbeat is None or heartbeat >= prior_heartbeat)
        ):
            latest[node] = dict(payload)
    return latest


def _bounded_tail_lines(
    path: Path,
    *,
    max_bytes: int = DEFAULT_MAX_JOURNAL_BYTES,
    max_lines: int = DEFAULT_MAX_JOURNAL_LINES,
) -> Sequence[str]:
    try:
        size = path.stat().st_size
    except OSError:
        return ()
    if size <= 0:
        return ()
    start = max(0, size - int(max_bytes))
    try:
        with path.open("rb") as handle:
            handle.seek(start)
            raw = handle.read(int(max_bytes))
    except OSError:
        return ()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if start > 0 and lines:
        lines = lines[1:]
    return tuple(lines[-int(max_lines) :])


def _normalize_resource_snapshot(
    snapshot: Any,
) -> Tuple[Optional[str], set, Tuple[BodyResourceTotal, ...]]:
    if isinstance(snapshot, Mapping):
        body_id = snapshot.get("body_id")
        node_ids = snapshot.get("node_ids", ())
        totals = snapshot.get("totals", ())
    else:
        body_id = getattr(snapshot, "body_id", None)
        node_ids = getattr(snapshot, "node_ids", ())
        totals = getattr(snapshot, "totals", ())
    normalized_ids = set()
    if isinstance(node_ids, (list, tuple, set)):
        for node_id in node_ids:
            if isinstance(node_id, str) and node_id.strip():
                normalized_ids.add(node_id.strip())

    normalized_totals = []
    if isinstance(totals, (list, tuple)):
        for total in totals:
            try:
                if isinstance(total, Mapping):
                    kind_value = total.get("kind")
                    unit = total.get("unit")
                    capacity = total.get("capacity")
                    available = total.get("available")
                    resource_count = total.get("resource_count")
                else:
                    kind_value = getattr(total, "kind")
                    unit = getattr(total, "unit")
                    capacity = getattr(total, "capacity")
                    available = getattr(total, "available")
                    resource_count = getattr(total, "resource_count")
                kind = getattr(kind_value, "value", kind_value)
                if not isinstance(kind, str) or not kind:
                    continue
                if not isinstance(unit, str) or not unit:
                    continue
                cap = float(capacity)
                avail = float(available)
                count = int(resource_count)
                if cap < 0.0 or avail < 0.0 or avail > cap or count < 0:
                    continue
            except (AttributeError, TypeError, ValueError):
                continue
            normalized_totals.append(
                BodyResourceTotal(
                    kind=kind,
                    unit=unit,
                    capacity=cap,
                    available=avail,
                    resource_count=count,
                )
            )
    normalized_totals.sort(key=lambda item: (item.kind, item.unit))
    normalized_body_id = body_id.strip() if isinstance(body_id, str) and body_id.strip() else None
    return normalized_body_id, normalized_ids, tuple(normalized_totals)


def _functional_state(
    availability: str,
    age: Optional[float],
    max_age: float,
) -> str:
    if age is None or age >= max_age:
        return "STALE"
    if availability == "available":
        return "ONLINE"
    if availability == "saturated":
        return "BUSY"
    if availability == "draining":
        return "DRAINING"
    if availability == "quarantined":
        return "QUARANTINED"
    if availability == "offline":
        return "OFFLINE"
    return availability.upper() if availability else "UNKNOWN"


def _text_or(value: Any, default: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def _text_tuple(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    result = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return tuple(result)


def _optional_number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if number >= 0.0 else None


def _nonnegative_number(value: Any, name: str) -> float:
    number = _optional_number(value)
    if number is None:
        raise ValueError("%s must be a non-negative number" % name)
    return number


def _bounded_fraction(value: Any) -> Optional[float]:
    number = _optional_number(value)
    if number is None or number > 1.0:
        return None
    return number


def _optional_nonnegative_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
