# SPDX-License-Identifier: GPL-3.0-only
"""Small data contracts for Velour's controlled web-research surface.

This module intentionally contains no networking. Providers are injected by
trusted application code and the Interface consumes their results as untrusted
reference material only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(frozen=True)
class WebResearchResult:
    """One bounded search result presented by the research surface."""

    result_id: str
    title: str
    source: str
    url: str
    summary: str = ""

    def __post_init__(self) -> None:
        for label, value in (
            ("result_id", self.result_id),
            ("title", self.title),
            ("source", self.source),
            ("url", self.url),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("%s must be a non-empty string" % label)


@dataclass(frozen=True)
class WebResearchDocument:
    """Sanitized reference document returned by a future fetch adapter."""

    result_id: str
    title: str
    source: str
    url: str
    text: str = ""
    html: str = ""
    retrieved_at: str = ""
    authority: str = "none"
    external_reference: bool = True

    def __post_init__(self) -> None:
        for label, value in (
            ("result_id", self.result_id),
            ("title", self.title),
            ("source", self.source),
            ("url", self.url),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("%s must be a non-empty string" % label)
        if self.authority != "none":
            raise ValueError("web research documents never carry Velvet authority")
        if self.external_reference is not True:
            raise ValueError("web research documents must remain external references")
        if not self.text and not self.html:
            raise ValueError("web research document requires text or sanitized html")


SearchProvider = Callable[[str], Sequence[WebResearchResult]]
DocumentProvider = Callable[[WebResearchResult], WebResearchDocument]
