# SPDX-License-Identifier: GPL-3.0-only
"""Presentation-only contracts for Velour's federated Archive search."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence


_ALLOWED_PROVIDERS = {"library", "zim", "web"}


@dataclass(frozen=True)
class ArchiveSearchResult:
    result_id: str
    provider: str
    title: str
    source: str
    uri: str
    summary: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)
    authority: str = "none"
    external_reference: bool = True

    def __post_init__(self) -> None:
        for label, value in (
            ("result_id", self.result_id),
            ("provider", self.provider),
            ("title", self.title),
            ("source", self.source),
            ("uri", self.uri),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("%s must be a non-empty string" % label)
        if self.provider not in _ALLOWED_PROVIDERS:
            raise ValueError("unknown Archive search provider: %s" % self.provider)
        if self.authority != "none":
            raise ValueError("Archive search results never carry Velvet authority")
        if self.external_reference is not True:
            raise ValueError("Archive search results remain external references")


@dataclass(frozen=True)
class ArchiveSearchSnapshot:
    query: str
    results: Sequence[ArchiveSearchResult]
    sources: Mapping[str, Mapping[str, object]]
    authority: str = "none"
    external_reference: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("Archive search query must be non-empty")
        if self.authority != "none":
            raise ValueError("Archive search never carries Velvet authority")
        if self.external_reference is not True:
            raise ValueError("Archive search remains reference-only")
        unknown = set(self.sources) - _ALLOWED_PROVIDERS
        if unknown:
            raise ValueError("unknown Archive search source status: %s" % sorted(unknown))


ArchiveSearchProvider = Callable[[str], ArchiveSearchSnapshot]
