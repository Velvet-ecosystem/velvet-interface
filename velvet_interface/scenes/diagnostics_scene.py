# velvet_interface/scenes/diagnostics_scene.py
from __future__ import annotations
"""Evidence-backed diagnostics scene.

The scene consumes a read-only body-state snapshot supplied by Runtime or a
local adapter. It never invents hardware state and never gains authority from
what it displays.
"""

from typing import Any, Callable, Dict, Mapping, Optional
import logging

try:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from velvet_interface.core.body_state import BodyStateSnapshot
from velvet_interface.core.scene import Scene
from velvet_interface.core.surface import Surface

logger = logging.getLogger(__name__)

BodyStateProvider = Callable[[], Any]


class DiagnosticsScene(Scene):
    """Display trusted body health, sensors, and receipt evidence."""

    def __init__(self, body_state_provider: Optional[BodyStateProvider] = None):
        super().__init__("diagnostics")
        self._body_state_provider = body_state_provider
        self.status_data = {}  # type: Dict[str, str]
        self.body_state = None  # type: Optional[Dict[str, Any]]

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        super().on_enter(context)
        logger.info("Diagnostics scene entered")
        self.refresh()

    def on_exit(self) -> None:
        super().on_exit()
        logger.info("Diagnostics scene exited")

    def refresh(self) -> Dict[str, str]:
        """Refresh display state from the configured read-only provider."""

        if self._body_state_provider is None:
            self.body_state = None
            self.status_data = {
                "Body": "Awaiting Runtime body state",
                "Mode": "DISPLAY-ONLY",
                "Physical control": "DISABLED",
            }
            return dict(self.status_data)

        try:
            raw = self._body_state_provider()
            state = _normalize_body_state(raw)
        except Exception as exc:
            logger.warning("Body-state provider failed: %s", exc)
            self.body_state = None
            self.status_data = {
                "Body": "STATE UNAVAILABLE",
                "Detail": str(exc),
                "Mode": "DISPLAY-ONLY",
                "Physical control": "DISABLED",
            }
            return dict(self.status_data)

        self.body_state = state
        sensors = state.get("sensors", [])
        health_events = state.get("health_events", [])
        receipts = state.get("receipt_ids", [])
        summary = str(state.get("summary", "No body summary"))
        presence = str(state.get("presence_state", "unknown")).upper()

        stale = 0
        degraded = 0
        failed = 0
        for sensor in sensors if isinstance(sensors, list) else []:
            if not isinstance(sensor, Mapping):
                continue
            if str(sensor.get("freshness", "")).lower() == "stale":
                stale += 1
            health = str(sensor.get("health_state", "UNKNOWN")).upper()
            if health == "DEGRADED":
                degraded += 1
            elif health == "FAILED":
                failed += 1

        self.status_data = {
            "Presence": presence,
            "Body": summary,
            "Sensors": str(len(sensors) if isinstance(sensors, list) else 0),
            "Health records": str(
                len(health_events) if isinstance(health_events, list) else 0
            ),
            "Stale sensors": str(stale),
            "Degraded sensors": str(degraded),
            "Failed sensors": str(failed),
            "Receipts": str(len(receipts) if isinstance(receipts, list) else 0),
            "Mode": "DISPLAY-ONLY",
            "Physical control": "DISABLED",
        }
        return dict(self.status_data)

    def status_snapshot(self) -> Dict[str, Any]:
        """Return the current surface-neutral diagnostics projection."""

        return {
            "scene_id": self.scene_id,
            "active": self.is_active,
            "status": dict(self.status_data),
            "body_state": dict(self.body_state) if self.body_state is not None else None,
            "mode": "display-only",
            "read_only": True,
            "actuation_granted": False,
            "actuation_performed": False,
        }

    def render(self, surface: Surface) -> Any:
        if surface.surface_id == "qt" and PYQT_AVAILABLE:
            return self._render_qt(surface)
        raise NotImplementedError("Surface %s not supported" % surface.surface_id)

    def _render_qt(self, surface: Surface) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel("Velvet Body Diagnostics")
        title.setFont(QFont("Arial", 24))
        layout.addWidget(title)

        for key, value in self.status_data.items():
            status_label = QLabel("%s: %s" % (key, value))
            status_label.setFont(QFont("Arial", 14))
            layout.addWidget(status_label)

        return widget

    def update_status(self, key: str, value: str) -> None:
        """Update presentation-only local text.

        This helper cannot update the underlying trusted body-state snapshot.
        """

        self.status_data[str(key)] = str(value)
        logger.debug("Local status text updated: %s = %s", key, value)


def _normalize_body_state(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, BodyStateSnapshot):
        return raw.to_dict()
    if isinstance(raw, Mapping):
        state = dict(raw)
    else:
        raise TypeError("body-state provider must return BodyStateSnapshot or mapping")

    if state.get("read_only") is not True:
        raise ValueError("body-state snapshot must be read_only")
    if state.get("actuation_granted") is not False:
        raise ValueError("body-state snapshot cannot grant actuation")
    if state.get("actuation_performed") is not False:
        raise ValueError("body-state snapshot cannot claim actuation")
    return state
