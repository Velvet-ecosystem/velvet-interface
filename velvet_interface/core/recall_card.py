# SPDX-License-Identifier: GPL-3.0-only
"""Display-only recall card contract for public-safe memory evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

_FORBIDDEN_FIELDS = {
    "payload",
    "raw_memory",
    "conversation",
    "embedding",
    "executor",
    "capability_token",
    "command",
    "route_id",
}


@dataclass(frozen=True)
class RecallCard:
    memory_event_id: str
    memory_kind: str
    score: float
    association: float
    confidence: float
    salience: float
    authority_status: str
    receipt_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        _text(self.memory_event_id, "memory_event_id")
        _text(self.memory_kind, "memory_kind")
        _unit(self.score, "score")
        _unit(self.association, "association")
        _unit(self.confidence, "confidence")
        _unit(self.salience, "salience")
        _text(self.authority_status, "authority_status")
        if self.receipt_id is not None:
            _text(self.receipt_id, "receipt_id")

        document: Dict[str, Any] = {
            "memory_event_id": self.memory_event_id,
            "memory_kind": self.memory_kind,
            "score": float(self.score),
            "association": float(self.association),
            "confidence": float(self.confidence),
            "salience": float(self.salience),
            "authority_status": self.authority_status,
            "mode": "display-only",
            "truth_claimed": False,
            "authority_granted": False,
            "actuation_granted": False,
            "actuation_performed": False,
        }
        if self.receipt_id is not None:
            document["receipt_id"] = self.receipt_id
        return document


def recall_card_from_mapping(document: Mapping[str, Any]) -> RecallCard:
    if not isinstance(document, Mapping):
        raise ValueError("recall card source must be a mapping")
    forbidden = _FORBIDDEN_FIELDS.intersection(document)
    if forbidden:
        raise ValueError("recall card contains forbidden private or authority fields")
    return RecallCard(
        memory_event_id=document.get("memory_event_id") or document.get("event_id"),
        memory_kind=document.get("memory_kind") or document.get("kind"),
        score=document.get("score"),
        association=document.get("association"),
        confidence=document.get("confidence"),
        salience=document.get("salience"),
        authority_status=document.get("authority_status"),
        receipt_id=document.get("receipt_id"),
    )


def _unit(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("{} must be numeric".format(name))
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("{} must be between 0 and 1".format(name))


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("{} must be a non-empty string".format(name))
