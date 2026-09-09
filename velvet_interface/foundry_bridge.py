# SPDX-License-Identifier: GPL-3.0-only
"""Thin Interface bridge to the Persona Continuity Character Foundry service.

Interface does not own Foundry candidate semantics, validation, persistence, or
promotion logic. This bridge lazily loads Persona Continuity when present and
converts its dataclass results into plain presentation data for Interface.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


class FoundryUnavailable(RuntimeError):
    """Raised when the canonical Persona Continuity Foundry service is absent."""


class FoundryBridge:
    """Presentation-only adapter over ``velvet_persona.foundry_service``.

    The bridge intentionally contains no fallback Foundry implementation. If the
    canonical service cannot be loaded, Interface reports the tool unavailable
    rather than inventing separate candidate behavior.
    """

    def __init__(self, state_dir: Path, service: Any = None) -> None:
        self.state_dir = Path(state_dir)
        self._service = service if service is not None else self._load_service()

    def _load_service(self) -> Any:
        try:
            module = import_module("velvet_persona.foundry_service")
            service_type = getattr(module, "FoundryService")
            return service_type(self.state_dir)
        except (ImportError, AttributeError, TypeError, ValueError) as exc:
            raise FoundryUnavailable(
                "Persona Continuity Character Foundry service is unavailable: %s" % exc
            ) from exc

    @staticmethod
    def _plain(value: Any) -> Any:
        if is_dataclass(value):
            return FoundryBridge._plain(asdict(value))
        if isinstance(value, Mapping):
            return {str(key): FoundryBridge._plain(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return [FoundryBridge._plain(item) for item in value]
        if isinstance(value, list):
            return [FoundryBridge._plain(item) for item in value]
        return value

    def scaffold(
        self,
        candidate_id: str,
        candidate_kind: str,
        display_name: str = "",
        identity_level: Optional[int] = None,
    ) -> Dict[str, Any]:
        return self._plain(
            self._service.scaffold(
                candidate_id,
                candidate_kind,
                display_name=display_name,
                identity_level=identity_level,
            )
        )

    def validate(self, mapping: Mapping[str, Any]) -> Dict[str, Any]:
        return self._plain(self._service.validate(mapping))

    def create(self, mapping: Mapping[str, Any]) -> Dict[str, Any]:
        return self._plain(self._service.create(mapping))

    def inspect(self, candidate_id: str) -> Dict[str, Any]:
        return self._plain(self._service.inspect(candidate_id))

    def list_candidates(self) -> Tuple[Dict[str, Any], ...]:
        values = self._service.list_candidates()
        return tuple(self._plain(item) for item in values)

    def update(
        self,
        mapping: Mapping[str, Any],
        expected_content_hash: str,
    ) -> Dict[str, Any]:
        return self._plain(self._service.update(mapping, expected_content_hash))

    def discard(self, candidate_id: str, expected_content_hash: str) -> Dict[str, Any]:
        return self._plain(self._service.discard(candidate_id, expected_content_hash))

    def propose_promotion(self, candidate_id: str) -> Dict[str, Any]:
        return self._plain(self._service.propose_promotion(candidate_id))
