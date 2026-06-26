# SPDX-License-Identifier: GPL-3.0-only
"""Bounded display-only panel state for recall cards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

from velvet_interface.core.recall_card import RecallCard

_ALLOWED_STATES = {"empty", "loading", "ready", "failed"}


@dataclass(frozen=True)
class RecallPanelSnapshot:
    state: str
    cards: Tuple[RecallCard, ...]
    query_event_id: Optional[str] = None
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        if self.state not in _ALLOWED_STATES:
            raise ValueError("unsupported recall panel state")
        if self.query_event_id is not None and (
            not isinstance(self.query_event_id, str) or not self.query_event_id.strip()
        ):
            raise ValueError("query_event_id must be a non-empty string")
        if self.error_code is not None and (
            not isinstance(self.error_code, str) or not self.error_code.strip()
        ):
            raise ValueError("error_code must be a non-empty string")
        if self.state == "ready" and not self.cards:
            raise ValueError("ready state requires at least one card")
        if self.state in {"empty", "loading", "failed"} and self.cards:
            raise ValueError("non-ready states cannot carry cards")
        if self.state == "failed" and self.error_code is None:
            raise ValueError("failed state requires error_code")
        if self.state != "failed" and self.error_code is not None:
            raise ValueError("error_code is only valid for failed state")

        return {
            "state": self.state,
            "query_event_id": self.query_event_id,
            "card_count": len(self.cards),
            "cards": [card.to_dict() for card in self.cards],
            "error_code": self.error_code,
            "mode": "display-only",
            "truth_claimed": False,
            "authority_granted": False,
            "actuation_granted": False,
            "actuation_performed": False,
        }


class RecallPanel:
    def __init__(self, max_cards: int = 8) -> None:
        if isinstance(max_cards, bool) or not isinstance(max_cards, int):
            raise TypeError("max_cards must be an integer")
        if not 1 <= max_cards <= 16:
            raise ValueError("max_cards must be between 1 and 16")
        self._max_cards = max_cards
        self._snapshot = RecallPanelSnapshot("empty", ())

    def set_loading(self, query_event_id: str) -> None:
        self._snapshot = RecallPanelSnapshot("loading", (), query_event_id=query_event_id)

    def set_ready(self, cards: Iterable[RecallCard], query_event_id: str) -> None:
        bounded = tuple(cards)[: self._max_cards]
        if not bounded:
            self._snapshot = RecallPanelSnapshot("empty", (), query_event_id=query_event_id)
            return
        for card in bounded:
            if not isinstance(card, RecallCard):
                raise ValueError("recall panel cards must be RecallCard instances")
            card.to_dict()
        self._snapshot = RecallPanelSnapshot("ready", bounded, query_event_id=query_event_id)

    def set_failed(self, query_event_id: str, error_code: str) -> None:
        self._snapshot = RecallPanelSnapshot(
            "failed", (), query_event_id=query_event_id, error_code=error_code
        )

    def clear(self) -> None:
        self._snapshot = RecallPanelSnapshot("empty", ())

    def snapshot(self) -> Dict[str, Any]:
        return self._snapshot.to_dict()
