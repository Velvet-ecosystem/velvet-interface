# SPDX-License-Identifier: GPL-3.0-only
"""Small data contracts for Velour's controlled web-research surface.

This module intentionally contains no networking. Providers are injected by
trusted application code and the Interface consumes their results as untrusted
reference material only.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
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
    """Sanitized external reference projected by the reviewed Velour adapter."""

    result_id: str
    title: str
    source: str
    url: str
    text: str = ""
    html: str = ""
    retrieved_at: str = ""
    content_sha256: str = ""
    content_type: str = ""
    byte_length: int = 0
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
        if self.content_sha256 and not re.fullmatch(r"[0-9a-fA-F]{64}", self.content_sha256):
            raise ValueError("content_sha256 must be a 64-character hexadecimal digest")
        if not isinstance(self.byte_length, int) or isinstance(self.byte_length, bool):
            raise ValueError("byte_length must be an integer")
        if self.byte_length < 0:
            raise ValueError("byte_length cannot be negative")
        if not isinstance(self.content_type, str):
            raise ValueError("content_type must be a string")
        if not isinstance(self.retrieved_at, str):
            raise ValueError("retrieved_at must be a string")


SearchProvider = Callable[[str], Sequence[WebResearchResult]]
DocumentProvider = Callable[[WebResearchResult], WebResearchDocument]
