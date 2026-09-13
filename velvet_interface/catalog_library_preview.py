# SPDX-License-Identifier: GPL-3.0-only
"""Catalog-aware read-only provider for Velour's Library Reader.

The Interface does not import Cyberdeck code directly. It consumes the stable
on-disk catalog contract when present and falls back to the existing bounded
filesystem preview only when no catalog exists.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from velvet_interface.library_preview import (
    KNOWN_LIBRARY_SUFFIXES,
    LibraryPreviewItem,
    LocalLibraryPreviewProvider,
)


@dataclass(frozen=True)
class CatalogPreviewMetadata:
    item_id: str
    collection: str
    source: str
    media_type: str
    extraction_status: str
    extraction_note: Optional[str]
    adapter_id: Optional[str]
    adapter_version: Optional[str]
    extracted_text_relative_path: Optional[str]


class CatalogLibraryPreviewProvider(LocalLibraryPreviewProvider):
    """Prefer Velour's canonical JSONL catalog without creating a repo dependency."""

    def __init__(
        self,
        root: Path,
        *,
        catalog_path: Optional[Path] = None,
        max_items: int = 2000,
        max_text_bytes: int = 4 * 1024 * 1024,
        max_catalog_entries: int = 100000,
        max_catalog_line_bytes: int = 1024 * 1024,
    ) -> None:
        super().__init__(root, max_items=max_items, max_text_bytes=max_text_bytes)
        self.catalog_path = Path(catalog_path) if catalog_path else self.root / "catalog" / "items.jsonl"
        self.max_catalog_entries = int(max_catalog_entries)
        self.max_catalog_line_bytes = int(max_catalog_line_bytes)
        if self.max_catalog_entries <= 0:
            raise ValueError("max_catalog_entries must be positive")
        if self.max_catalog_line_bytes <= 0:
            raise ValueError("max_catalog_line_bytes must be positive")
        self._metadata = {}  # type: Dict[str, CatalogPreviewMetadata]

    @property
    def catalog_available(self) -> bool:
        return self.catalog_path.is_file()

    def list_items(self, query: str = "") -> List[LibraryPreviewItem]:
        if not self.catalog_available:
            self._metadata.clear()
            return super().list_items(query=query)
        if not self.root.is_dir():
            self._metadata.clear()
            return []

        needle = query.strip().lower()
        items = []  # type: List[LibraryPreviewItem]
        metadata = {}  # type: Dict[str, CatalogPreviewMetadata]
        root_resolved = self.root.resolve()

        with self.catalog_path.open("r", encoding="utf-8", errors="replace") as handle:
            for entry_index, raw_line in enumerate(handle):
                if entry_index >= self.max_catalog_entries or len(items) >= self.max_items:
                    break
                if not raw_line.strip() or len(raw_line.encode("utf-8")) > self.max_catalog_line_bytes:
                    continue
                try:
                    data = json.loads(raw_line)
                except (TypeError, ValueError):
                    continue

                resolved = self._catalog_payload_path(data.get("file_path"), root_resolved)
                if resolved is None:
                    continue
                suffix = resolved.suffix.lower()
                if suffix not in KNOWN_LIBRARY_SUFFIXES:
                    continue
                try:
                    stat = resolved.stat()
                    relative = resolved.relative_to(root_resolved).as_posix()
                except (FileNotFoundError, OSError, ValueError):
                    continue

                title = str(data.get("title") or resolved.stem).strip() or resolved.name
                collection = str(data.get("collection") or "").strip()
                source = str(data.get("source") or "").strip()
                searchable = " ".join(
                    [
                        title,
                        relative,
                        collection,
                        source,
                        " ".join(str(value) for value in data.get("subjects", []) if value),
                        " ".join(str(value) for value in data.get("tags", []) if value),
                    ]
                ).lower()
                if needle and needle not in searchable:
                    continue

                item = LibraryPreviewItem(
                    relative_path=relative,
                    title=title,
                    suffix=suffix,
                    size_bytes=int(stat.st_size),
                    preview_kind=self._preview_kind(suffix),
                )
                extracted_relative = self._catalog_extracted_text_path(
                    data.get("extracted_text_path"), root_resolved
                )
                metadata[relative] = CatalogPreviewMetadata(
                    item_id=str(data.get("item_id") or ""),
                    collection=collection,
                    source=source,
                    media_type=str(data.get("media_type") or ""),
                    extraction_status=str(data.get("extraction_status") or "not_attempted"),
                    extraction_note=(
                        str(data.get("extraction_note")) if data.get("extraction_note") else None
                    ),
                    adapter_id=str(data.get("adapter_id")) if data.get("adapter_id") else None,
                    adapter_version=(
                        str(data.get("adapter_version")) if data.get("adapter_version") else None
                    ),
                    extracted_text_relative_path=extracted_relative,
                )
                items.append(item)

        items.sort(key=lambda item: (item.title.lower(), item.relative_path.lower()))
        self._metadata = metadata
        return items

    def metadata_for(self, item: LibraryPreviewItem) -> Optional[CatalogPreviewMetadata]:
        return self._metadata.get(item.relative_path)

    def has_extracted_text(self, item: LibraryPreviewItem) -> bool:
        metadata = self.metadata_for(item)
        return bool(
            metadata
            and metadata.extraction_status == "extracted"
            and metadata.extracted_text_relative_path
        )

    def read_text(self, item: LibraryPreviewItem) -> str:
        if item.preview_kind in {"text", "html"}:
            return super().read_text(item)
        metadata = self.metadata_for(item)
        if not metadata or metadata.extraction_status != "extracted":
            raise ValueError("item has no extracted text preview")
        if not metadata.extracted_text_relative_path:
            raise ValueError("catalog entry has no extracted text path")
        path = self._resolve_relative(metadata.extracted_text_relative_path)
        size = path.stat().st_size
        if size > self.max_text_bytes:
            raise ValueError("extracted text exceeds preview byte limit")
        return path.read_bytes().decode("utf-8", errors="replace")

    def _catalog_payload_path(self, value, root_resolved: Path) -> Optional[Path]:  # type: ignore[no-untyped-def]
        if not value:
            return None
        candidate = Path(str(value)).expanduser()
        if not candidate.is_absolute():
            candidate = self.root / candidate
        try:
            resolved = candidate.resolve()
            resolved.relative_to(root_resolved)
        except (OSError, RuntimeError, ValueError):
            return None
        return resolved if resolved.is_file() else None

    def _catalog_extracted_text_path(self, value, root_resolved: Path) -> Optional[str]:  # type: ignore[no-untyped-def]
        if not value:
            return None
        candidate = Path(str(value)).expanduser()
        if not candidate.is_absolute():
            candidate = self.root / candidate
        try:
            resolved = candidate.resolve()
            relative = resolved.relative_to(root_resolved)
        except (OSError, RuntimeError, ValueError):
            return None
        return relative.as_posix() if resolved.is_file() else None

    def _resolve_relative(self, relative_path: str) -> Path:
        root_resolved = self.root.resolve()
        candidate = (root_resolved / relative_path).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError("catalog preview path escapes configured root") from exc
        if not candidate.is_file():
            raise FileNotFoundError(str(candidate))
        return candidate
