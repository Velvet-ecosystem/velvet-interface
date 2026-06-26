# SPDX-License-Identifier: GPL-3.0-only
"""Project Runtime recall views into public-safe Interface cards."""

from __future__ import annotations

from typing import Any, Mapping

from velvet_interface.core.recall_card import RecallCard

_PRIVATE_FIELDS = {
    "payload", "raw_memory", "conversation", "embedding",
    "capability_token", "executor", "command", "route_id",
}


def recall_card_from_runtime_result(document: Mapping[str, Any]) -> RecallCard:
    if not isinstance(document, Mapping):
        raise ValueError("Runtime recall result must be a mapping")
    _reject_private_fields(document)

    card = RecallCard(
        memory_event_id=document.get("event_id"),
        memory_kind=document.get("memory_kind"),
        score=document.get("score"),
        association=document.get("association"),
        confidence=document.get("confidence"),
        salience=document.get("salience"),
        authority_status=document.get("authority_status"),
        receipt_id=document.get("receipt_id"),
    )
    card.to_dict()
    return card


def _reject_private_fields(document: Mapping[str, Any]) -> None:
    if _PRIVATE_FIELDS.intersection(document):
        raise ValueError("Runtime recall result contains forbidden private or authority fields")
