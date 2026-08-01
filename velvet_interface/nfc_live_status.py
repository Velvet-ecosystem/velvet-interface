# SPDX-License-Identifier: GPL-3.0-only
"""Read-only contactless verification-factor projection."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from velvet_interface.core.body_state import BodyStateStore


BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"
_MATCH_STATES = {"MATCHED", "UNKNOWN", "DISABLED"}
_RAW_IDENTIFIER_KEYS = {
    "uid",
    "tag_id",
    "raw_tag",
    "raw_identifier",
    "serial_number",
    "data_hex",
    "tag_hex",
}


@dataclass(frozen=True)
class NfcLiveStatus:
    available: bool
    state: str
    match_state: str
    freshness: str
    reader_state: str
    label: Optional[str] = None
    principal_ref: Optional[str] = None
    role_hint: Optional[str] = None
    factor_confidence: Optional[float] = None
    receipt_id: Optional[str] = None
    message: str = ""


def load_nfc_live_status(
    body_path: Path,
    now_monotonic: Optional[float] = None,
) -> NfcLiveStatus:
    try:
        document = json.loads(Path(body_path).read_text(encoding="utf-8"))
        _validate_snapshot(document)
        store = BodyStateStore()
        store.apply_many(document["records"])
        current = time.monotonic() if now_monotonic is None else float(now_monotonic)
        body = store.snapshot(current)
        sensor = next(
            (
                item
                for item in body.sensors
                if item.sensor_type == "contactless_token_presentation"
                or item.module_id == "contactless-token-main"
            ),
            None,
        )
        health = next(
            (
                item
                for item in body.health_events
                if item.module_id == "contactless-token-main"
            ),
            None,
        )

        if sensor is None:
            if health is not None and health.state_after == "FAILED":
                detail = str(
                    health.diagnostic_payload.get(
                        "detail", "Contactless reader failed"
                    )
                )
                return NfcLiveStatus(
                    available=True,
                    state="FAILED",
                    match_state="NO PRESENTATION",
                    freshness="unknown",
                    reader_state="FAILED",
                    receipt_id=health.receipt_id,
                    message=detail,
                )
            if health is not None and health.state_after == "ONLINE":
                return NfcLiveStatus(
                    available=True,
                    state="IDLE",
                    match_state="NO PRESENTATION",
                    freshness="none",
                    reader_state="ONLINE",
                    receipt_id=health.receipt_id,
                    message="Reader ready; no fresh contactless factor",
                )
            return NfcLiveStatus(
                available=False,
                state="UNAVAILABLE",
                match_state="NO DATA",
                freshness="unknown",
                reader_state="UNKNOWN",
                message="Contactless evidence awaiting Runtime",
            )

        payload = sensor.payload
        _reject_raw_identifiers(payload)
        if payload.get("verification_only") is not True:
            raise ValueError("contactless evidence must be verification-only")
        if payload.get("presence_claimed") is not False:
            raise ValueError("contactless evidence cannot claim presence")
        if payload.get("grants_authority") is not False:
            raise ValueError("contactless evidence cannot grant authority")
        if payload.get("static_identifier") is not True:
            raise ValueError("contactless evidence must identify its static factor")
        if payload.get("cryptographic_challenge") is not False:
            raise ValueError("contactless evidence cannot claim challenge-response")
        if payload.get("read_only") is not True:
            raise ValueError("contactless evidence must be read-only")

        match_state = _required_text(payload, "match_state").upper()
        if match_state not in _MATCH_STATES:
            raise ValueError("unsupported contactless match state")
        token_ref = _required_text(payload, "token_ref")
        if not token_ref.startswith("hmac-sha256:") or len(token_ref) != 76:
            raise ValueError("contactless evidence requires a private HMAC reference")
        try:
            int(token_ref[12:], 16)
        except ValueError as exc:
            raise ValueError("contactless HMAC reference is malformed") from exc

        confidence = _required_confidence(payload.get("factor_confidence"))
        freshness = sensor.freshness(current)
        state = match_state
        reader_state = sensor.health_state
        if health is not None and health.state_after == "FAILED":
            state = "FAILED"
            reader_state = "FAILED"
        elif freshness == "stale":
            state = "EXPIRED"

        label = _optional_text(payload.get("label"))
        principal_ref = _optional_text(payload.get("principal_ref"))
        role_hint = _optional_text(payload.get("role_hint"))
        if match_state == "UNKNOWN" and any(
            value is not None for value in (label, principal_ref, role_hint)
        ):
            raise ValueError("unknown contactless factor cannot claim a principal")

        return NfcLiveStatus(
            available=True,
            state=state,
            match_state=match_state,
            freshness=freshness,
            reader_state=reader_state,
            label=label,
            principal_ref=principal_ref,
            role_hint=role_hint,
            factor_confidence=confidence,
            receipt_id=sensor.receipt_id,
            message=_message(state, match_state),
        )
    except FileNotFoundError:
        message = "Contactless evidence awaiting Runtime snapshot"
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        message = "Contactless evidence unavailable: %s" % exc
    return NfcLiveStatus(
        available=False,
        state="UNAVAILABLE",
        match_state="NO DATA",
        freshness="unknown",
        reader_state="UNKNOWN",
        message=message,
    )


def _validate_snapshot(document: Any) -> None:
    if not isinstance(document, Mapping):
        raise ValueError("body snapshot root must be an object")
    if document.get("schema") != BODY_STATE_SNAPSHOT_SCHEMA:
        raise ValueError("unsupported body snapshot schema")
    if document.get("read_only") is not True:
        raise ValueError("body snapshot must be read-only")
    if document.get("authority", "none") != "none":
        raise ValueError("body snapshot cannot carry authority")
    if document.get("actuation_granted") is not False:
        raise ValueError("body snapshot cannot grant actuation")
    if document.get("actuation_performed") is not False:
        raise ValueError("body snapshot cannot claim actuation")
    if not isinstance(document.get("records"), list):
        raise ValueError("body snapshot records must be a list")


def _reject_raw_identifiers(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if str(key).lower() in _RAW_IDENTIFIER_KEYS:
            raise ValueError("contactless evidence contains a raw identifier field")


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("contactless %s must be non-empty text" % key)
    return value.strip()


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("contactless optional text must be non-empty")
    return value.strip()


def _required_confidence(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("contactless factor confidence must be numeric")
    confidence = float(value)
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ValueError("contactless factor confidence is outside bounds")
    return confidence


def _message(state: str, match_state: str) -> str:
    if state == "FAILED":
        return "Contactless reader failed"
    if state == "EXPIRED":
        return "Last genuine contactless presentation has expired"
    if match_state == "MATCHED":
        return "Known contactless factor observed; further verification required"
    if match_state == "DISABLED":
        return "Disabled contactless factor observed"
    return "Unknown contactless factor observed"
