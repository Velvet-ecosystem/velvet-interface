# SPDX-License-Identifier: GPL-3.0-only
"""Display-only view model for Velvet ghost CAN observations.

The ghost CAN panel is a public-safe interface adapter. It renders sanitized
Runtime/event-protocol observations from the jarred vehicle path and refuses
payloads that imply live CAN access, command routing, or actuation authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

_FORBIDDEN_AUTHORITY_FIELDS = {"action","actuate","actuation","capability","command","executor","executor_name","hardware","hardware_bus","hardware_target","route_id","send","shell","target","token","transmit","write"}
_REQUIRED_FALSE_FLAGS = ("physical_bus_opened","hardware_bus_opened","can_transmission_attempted","can_transmission_performed","actuation_granted","actuation_performed","authority_granted")
_REQUIRED_TRUE_FLAGS = ("read_only","synthetic_fixture")

@dataclass(frozen=True)
class GhostCanSignalView:
    name: str
    value: Any
    confidence: float
    observed_at: float
    source_profile: str
    unit: Optional[str] = None
    def label(self) -> str:
        suffix = " %s" % self.unit if self.unit else ""
        return "%s: %s%s" % (self.name, self.value, suffix)
    def to_dict(self) -> Dict[str, Any]:
        return {"name":self.name,"value":self.value,"unit":self.unit,"confidence":float(self.confidence),"observed_at":float(self.observed_at),"source_profile":self.source_profile,"status":"observation-only","read_only":True,"actuation_granted":False,"actuation_performed":False}

@dataclass(frozen=True)
class GhostCanPanelViewModel:
    title: str
    subtitle: str
    event_type: str
    source: str
    safety_banner: str
    signals: Tuple[GhostCanSignalView, ...]
    receipt_id: Optional[str]
    blocked_reasons: Tuple[str, ...]
    @property
    def is_safe_to_display(self) -> bool:
        return not self.blocked_reasons
    def to_dict(self) -> Dict[str, Any]:
        return {"title":self.title,"subtitle":self.subtitle,"event_type":self.event_type,"source":self.source,"safety_banner":self.safety_banner,"signal_count":len(self.signals),"signals":[signal.to_dict() for signal in self.signals],"receipt_id":self.receipt_id,"blocked_reasons":list(self.blocked_reasons),"display_only":True,"physical_control":"disabled","actuation_granted":False,"actuation_performed":False}

def view_model_from_ghost_can_event(event: Mapping[str, Any]) -> GhostCanPanelViewModel:
    if not isinstance(event, Mapping):
        return _blocked_panel("Event root must be a mapping")
    payload = _select_payload(event)
    blocked_reasons = list(_validate_safety(payload))
    event_type = str(event.get("event_type") or payload.get("event_type") or "vehicle.can.ghost_observation")
    source = str(payload.get("source") or payload.get("source_profile") or "ghost-can")
    receipt_id = _optional_text(event.get("receipt_id") or payload.get("receipt_id") or payload.get("receipt_hash"))
    signals: Tuple[GhostCanSignalView, ...] = ()
    if not blocked_reasons:
        try:
            signals = tuple(_collect_signals(payload))
        except ValueError as exc:
            blocked_reasons.append(str(exc))
    return GhostCanPanelViewModel(title="Ghost CAN",subtitle="Jarred Tiburon, synthetic CAN" if not blocked_reasons else "Ghost CAN blocked",event_type=event_type,source=source,safety_banner="Display-only synthetic fixture. No physical bus opened." if not blocked_reasons else "Blocked: display payload failed ghost CAN safety checks.",signals=signals,receipt_id=receipt_id,blocked_reasons=tuple(blocked_reasons))

def render_ghost_can_text(view_model: GhostCanPanelViewModel) -> str:
    lines=[view_model.title,view_model.subtitle,view_model.safety_banner]
    if view_model.receipt_id: lines.append("receipt: %s" % view_model.receipt_id)
    if view_model.blocked_reasons:
        lines.extend("blocked: %s" % reason for reason in view_model.blocked_reasons)
        return "\n".join(lines)
    for signal in view_model.signals: lines.append("- %s (confidence %.2f)" % (signal.label(), signal.confidence))
    if not view_model.signals: lines.append("- no decoded signals")
    return "\n".join(lines)

def _select_payload(event: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("payload","observation","observations"):
        value=event.get(key)
        if isinstance(value, Mapping): return value
    return event

def _validate_safety(payload: Mapping[str, Any]) -> Tuple[str, ...]:
    reasons=[]
    forbidden=sorted(_FORBIDDEN_AUTHORITY_FIELDS.intersection(payload.keys()))
    if forbidden: reasons.append("payload contains authority fields: %s" % forbidden)
    if payload.get("status") not in (None,"observation-only","ghost-observation"): reasons.append("status must be observation-only or ghost-observation")
    for flag in _REQUIRED_TRUE_FLAGS:
        if payload.get(flag) is not True: reasons.append("%s must be true" % flag)
    for flag in _REQUIRED_FALSE_FLAGS:
        value=payload.get(flag)
        if flag=="hardware_bus_opened" and value is None: continue
        if value is not False: reasons.append("%s must be false" % flag)
    if payload.get("synthetic") not in (True,None): reasons.append("synthetic must not be false")
    return tuple(reasons)

def _collect_signals(payload: Mapping[str, Any]) -> Iterable[GhostCanSignalView]:
    raw_signals=payload.get("signals") or payload.get("decoded_signals") or payload.get("values")
    if raw_signals is None: raw_signals=[payload]
    if not isinstance(raw_signals,list): raise ValueError("signals must be a list")
    signals=[]
    for raw in raw_signals:
        if not isinstance(raw,Mapping): raise ValueError("signal entry must be a mapping")
        forbidden=sorted(_FORBIDDEN_AUTHORITY_FIELDS.intersection(raw.keys()))
        if forbidden: raise ValueError("signal contains authority fields: %s" % forbidden)
        signals.append(GhostCanSignalView(name=_required_text(raw,"name",alias="signal_name"),value=_required_scalar(raw.get("value")),unit=_optional_text(raw.get("unit")),confidence=_required_number(raw,"confidence",default=1.0),observed_at=_required_number(raw,"observed_at",alias="timestamp",default=0.0),source_profile=_required_text(raw,"source_profile",default=str(payload.get("source_profile") or "ghost-profile"))))
    return signals

def _required_text(raw,key,alias=None,default=None):
    value=raw.get(key)
    if value is None and alias is not None: value=raw.get(alias)
    if value is None: value=default
    if not isinstance(value,str) or not value.strip(): raise ValueError("%s must be a non-empty string" % key)
    return value.strip()

def _optional_text(value):
    if value is None: return None
    if not isinstance(value,str) or not value.strip(): raise ValueError("optional text must be a non-empty string")
    return value.strip()

def _required_number(raw,key,alias=None,default=None):
    value=raw.get(key)
    if value is None and alias is not None: value=raw.get(alias)
    if value is None: value=default
    if isinstance(value,bool) or not isinstance(value,(int,float)): raise ValueError("%s must be numeric" % key)
    return float(value)

def _required_scalar(value):
    if value is None or isinstance(value,(dict,list,tuple,set)): raise ValueError("signal value must be a scalar")
    return value

def _blocked_panel(reason):
    return GhostCanPanelViewModel(title="Ghost CAN",subtitle="Ghost CAN blocked",event_type="vehicle.can.ghost_observation",source="unknown",safety_banner="Blocked: display payload failed ghost CAN safety checks.",signals=(),receipt_id=None,blocked_reasons=(reason,))
