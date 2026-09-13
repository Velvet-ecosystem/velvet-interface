# SPDX-License-Identifier: GPL-3.0-only
"""Read-only preview boundary for the Founder Library Reader.

This module is intentionally small. It does not replace the canonical offline
library/catalog owned elsewhere in the Velvet ecosystem. It provides a bounded
local preview seam so Interface can browse a configured library root without
executing active content or granting authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".log",
}
HTML_SUFFIXES = {".html", ".htm", ".xhtml"}
KNOWN_LIBRARY_SUFFIXES = TEXT_SUFFIXES | HTML_SUFFIXES | {".pdf", ".epub", ".zim"}


@dataclass(frozen=True)
class LibraryPreviewItem:
    """One bounded local library item visible to Interface."""

    relative_path: str
    title: str
    suffix: str
    size_bytes: int
    preview_kind: str


class LocalLibraryPreviewProvider:
    """Bounded read-only browser for a configured local library root.

    The provider never executes files, follows symlinks outside the configured
    root, or writes library state. It exists only as an Interface preview seam
    until a canonical Velour/library service owns this presentation contract.
    """

    def __init__(
        self,
        root: Path,
        *,
        max_items: int = 2000,
        max_text_bytes: int = 4 * 1024 * 1024,
    ) -> None:
        self.root = Path(root).expanduser()
        self.max_items = int(max_items)
        self.max_text_bytes = int(max_text_bytes)
        if self.max_items <= 0:
            raise ValueError("max_items must be positive")
        if self.max_text_bytes <= 0:
            raise ValueError("max_text_bytes must be positive")

    def list_items(self, query: str = "") -> List[LibraryPreviewItem]:
        if not self.root.is_dir():
            return []
        needle = query.strip().lower()
        items = []  # type: List[LibraryPreviewItem]
        root_resolved = self.root.resolve()
        for path in self._iter_candidates():
            if len(items) >= self.max_items:
                break
            try:
                resolved = path.resolve()
                resolved.relative_to(root_resolved)
                stat = resolved.stat()
            except (FileNotFoundError, OSError, RuntimeError, ValueError):
                continue
            suffix = resolved.suffix.lower()
            if suffix not in KNOWN_LIBRARY_SUFFIXES:
                continue
            relative = resolved.relative_to(root_resolved).as_posix()
            title = resolved.stem.replace("_", " ").replace("-", " ").strip() or resolved.name
            if needle and needle not in relative.lower() and needle not in title.lower():
                continue
            items.append(
                LibraryPreviewItem(
                    relative_path=relative,
                    title=title,
                    suffix=suffix,
                    size_bytes=int(stat.st_size),
                    preview_kind=self._preview_kind(suffix),
                )
            )
        items.sort(key=lambda item: (item.title.lower(), item.relative_path.lower()))
        return items

    def read_text(self, item: LibraryPreviewItem) -> str:
        if item.preview_kind not in {"text", "html"}:
            raise ValueError("item does not have a text preview")
        path = self._resolve_item(item)
        size = path.stat().st_size
        if size > self.max_text_bytes:
            raise ValueError("item exceeds preview byte limit")
        data = path.read_bytes()
        return data.decode("utf-8", errors="replace")

    def path_for(self, item: LibraryPreviewItem) -> Path:
        return self._resolve_item(item)

    def _iter_candidates(self) -> Iterable[Path]:
        try:
            return self.root.rglob("*")
        except OSError:
            return ()

    def _resolve_item(self, item: LibraryPreviewItem) -> Path:
        root_resolved = self.root.resolve()
        candidate = (root_resolved / item.relative_path).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError("library item escapes configured root") from exc
        if not candidate.is_file():
            raise FileNotFoundError(str(candidate))
        return candidate

    @staticmethod
    def _preview_kind(suffix: str) -> str:
        if suffix in HTML_SUFFIXES:
            return "html"
        if suffix in TEXT_SUFFIXES:
            return "text"
        if suffix == ".pdf":
            return "pdf"
        if suffix == ".epub":
            return "epub"
        if suffix == ".zim":
            return "zim"
        return "unknown"
