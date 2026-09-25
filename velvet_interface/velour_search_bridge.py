# SPDX-License-Identifier: GPL-3.0-only
"""Narrow presentation bridge to Velour's federated reference search CLI."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from velvet_interface.archive_search import ArchiveSearchResult, ArchiveSearchSnapshot


class VelourSearchUnavailable(RuntimeError):
    """Raised when the configured federated search adapter cannot respond safely."""


class VelourSearchBridge:
    """Read-only subprocess bridge over the allow-listed ``velour-search`` command."""

    def __init__(
        self,
        executable: Path,
        library_root: Path,
        *,
        kiwix_endpoint: str = "",
        web_endpoint: str = "",
        allow_loopback_web: bool = False,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.executable = Path(executable).expanduser()
        self.library_root = Path(library_root).expanduser()
        self.kiwix_endpoint = str(kiwix_endpoint or "").strip()
        self.web_endpoint = str(web_endpoint or "").strip()
        self.allow_loopback_web = bool(allow_loopback_web)
        self.timeout_seconds = float(timeout_seconds)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def search(self, query: str, limit: int = 8) -> ArchiveSearchSnapshot:
        query = str(query or "").strip()
        if not query:
            raise ValueError("Archive search query cannot be empty")
        if len(query) > 500:
            raise ValueError("Archive search query is too long")
        if int(limit) < 1 or int(limit) > 25:
            raise ValueError("Archive search limit must be between 1 and 25")
        if not self.executable.is_file():
            raise VelourSearchUnavailable("Velour federated search executable not found: %s" % self.executable)

        argv = [
            str(self.executable),
            query,
            "--root",
            str(self.library_root),
            "--limit",
            str(int(limit)),
            "--timeout",
            str(self.timeout_seconds),
        ]
        if self.kiwix_endpoint:
            argv.extend(["--kiwix-endpoint", self.kiwix_endpoint])
        if self.web_endpoint:
            argv.extend(["--web-endpoint", self.web_endpoint])
            if self.allow_loopback_web:
                argv.append("--allow-loopback-web")

        try:
            completed = subprocess.run(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout_seconds + 2.0,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise VelourSearchUnavailable("Velour federated search unavailable: %s" % exc) from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
            raise VelourSearchUnavailable("Velour federated search failed: %s" % detail[:400])
        try:
            payload = json.loads(completed.stdout)
        except (TypeError, ValueError) as exc:
            raise VelourSearchUnavailable("Velour federated search returned invalid JSON") from exc
        return self._snapshot(payload)

    @staticmethod
    def _snapshot(payload: object) -> ArchiveSearchSnapshot:
        if not isinstance(payload, dict):
            raise VelourSearchUnavailable("Velour federated search response must be an object")
        if payload.get("schema") != "velour.federated_search.v1":
            raise VelourSearchUnavailable("unexpected Velour federated search schema")
        if payload.get("authority") != "none" or payload.get("external_reference") is not True:
            raise VelourSearchUnavailable("Velour federated search crossed the authority boundary")

        query = payload.get("query")
        sources = payload.get("sources")
        raw_results = payload.get("results")
        if not isinstance(query, str) or not query.strip():
            raise VelourSearchUnavailable("Velour federated search omitted its query")
        if not isinstance(sources, dict) or not isinstance(raw_results, list):
            raise VelourSearchUnavailable("Velour federated search response is incomplete")

        clean_sources: Dict[str, Mapping[str, object]] = {}
        for provider, status in sources.items():
            if provider not in {"library", "zim", "web"} or not isinstance(status, dict):
                raise VelourSearchUnavailable("Velour federated search returned invalid provider status")
            clean_sources[str(provider)] = dict(status)

        results: List[ArchiveSearchResult] = []
        for row in raw_results:
            if not isinstance(row, dict):
                raise VelourSearchUnavailable("Velour federated search returned an invalid result")
            metadata = row.get("metadata")
            if metadata is None:
                metadata = {}
            if not isinstance(metadata, dict):
                raise VelourSearchUnavailable("Velour federated result metadata must be an object")
            results.append(
                ArchiveSearchResult(
                    result_id=str(row.get("result_id") or ""),
                    provider=str(row.get("provider") or ""),
                    title=str(row.get("title") or ""),
                    source=str(row.get("source") or ""),
                    uri=str(row.get("uri") or ""),
                    summary=str(row.get("summary") or ""),
                    metadata=dict(metadata),
                    authority=str(row.get("authority") or ""),
                    external_reference=row.get("external_reference") is True,
                )
            )
        return ArchiveSearchSnapshot(
            query=query,
            results=tuple(results),
            sources=clean_sources,
            authority="none",
            external_reference=True,
        )
