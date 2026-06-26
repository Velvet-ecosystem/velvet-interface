# SPDX-License-Identifier: GPL-3.0-only
"""Project Runtime recall results into public-safe Interface cards."""

from __future__ import annotations

from typing import Any, Mapping

from velvet_interface.core.recall_card import RecallCard

_PRIVATE_FIELDS = {
    "payload",
    "raw_memory",
    "conversation",
    "embedding",
    "capability_token",
    "executor",
    "command",
    "route_id",
}


def recall_card_from_runtime_result(document: Mapping[str, Any]) -> RecallCard:
    if not isinstance(document, Mapping):
        raise ValueError("Runtime recall result must be a mapping")
    _reject_private_fields(document)

    record = document.get("record")
    score = document.get("score")
    if not isinstance(record, Mapping):
        raise ValueError("Runtime recall result record must be a mapping")
    if not isinstance(score, Mapping):
        raise ValueError("Runtime recall result score must be a mapping")
    _reject_private_fields(record)
    _reject_private_fields(score)

    record_event_id = record.get("event_id")
    score_event_id = score.get("event_id")
    if record_event_id != score_event_id:
        raise ValueError("record and score event_id values must match")

    card = RecallCard(
        memory_event_id=record_event_id,
        memory_kind=record.get("kind"),
        score=score.get("score"),
        association=score.get("association"),
        confidence=score.get("confidence"),
        salience=score.get("salience"),
        authority_status=record.get("authority_status"),
        receipt_id=document.get("receipt_id"),
    )
    card.to_dict()
    return card


def _reject_private_fields(document: Mapping[str, Any]) -> None:
    if _PRIVATE_FIELDS.intersection(document):
        raise ValueError("Runtime recall result contains forbidden private or authority fields")
