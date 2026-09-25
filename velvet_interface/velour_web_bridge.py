# SPDX-License-Identifier: GPL-3.0-only
"""Narrow presentation bridge to Velour's controlled web-research adapter.

The Interface owns no sockets or browser engine here. It invokes the reviewed
``velour-web`` CLI with an allow-listed command shape, validates its JSON, and
projects only reference-only data into the existing UI contracts.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from velvet_interface.web_research import WebResearchDocument, WebResearchResult


class VelourWebUnavailable(RuntimeError):
    """Raised when Velour's reviewed research adapter cannot serve the UI."""


class VelourWebBridge:
    """Read-only adapter over the ``velour-web`` CLI."""

    SEARCH_SCHEMA = "velour.web_research.search.v1"
    DOCUMENT_SCHEMA = "velour.web_research.document.v1"

    def __init__(
        self,
        executable: Path,
        search_endpoint: str,
        *,
        timeout_seconds: float = 12.0,
        result_limit: int = 8,
        max_output_bytes: int = 3 * 1024 * 1024,
        allow_loopback_endpoint: bool = False,
    ) -> None:
        self.executable = Path(executable).expanduser()
        self.search_endpoint = str(search_endpoint).strip()
        self.timeout_seconds = float(timeout_seconds)
        self.result_limit = int(result_limit)
        self.max_output_bytes = int(max_output_bytes)
        self.allow_loopback_endpoint = bool(allow_loopback_endpoint)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.result_limit < 1 or self.result_limit > 25:
            raise ValueError("result_limit must be between 1 and 25")
        if self.max_output_bytes < 1:
            raise ValueError("max_output_bytes must be positive")
        if not self.search_endpoint:
            raise ValueError("search_endpoint must be configured explicitly")

    def _run_json(self, args: Sequence[str]) -> Dict[str, Any]:
        if not self.executable.is_file():
            raise VelourWebUnavailable(
                "Velour web executable not found: %s" % self.executable
            )
        argv = [str(self.executable)] + [str(value) for value in args]
        try:
            result = subprocess.run(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise VelourWebUnavailable(
                "Velour web command unavailable: %s" % exc
            ) from exc

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        if len(stdout.encode("utf-8", errors="replace")) > self.max_output_bytes:
            raise VelourWebUnavailable("Velour web response exceeded bridge maximum")
        if result.returncode != 0:
            detail = stderr.strip() or stdout.strip() or "no detail"
            raise VelourWebUnavailable("Velour web request failed: %s" % detail)
        try:
            payload = json.loads(stdout)
        except (TypeError, ValueError) as exc:
            detail = stderr.strip() or stdout.strip() or "no output"
            raise VelourWebUnavailable(
                "Velour web adapter returned invalid JSON: %s" % detail
            ) from exc
        if not isinstance(payload, dict):
            raise VelourWebUnavailable("Velour web response must be a JSON object")
        return payload

    @staticmethod
    def _require_common(payload: Mapping[str, Any], schema: str) -> None:
        if payload.get("schema") != schema:
            raise VelourWebUnavailable("Velour web response schema mismatch")
        if payload.get("authority") != "none":
            raise VelourWebUnavailable("web reference attempted to claim authority")
        if payload.get("external_reference") is not True:
            raise VelourWebUnavailable("web response lost external-reference marking")

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise VelourWebUnavailable("Velour web response missing %s" % field)
        return value.strip()

    def search(self, query: str) -> List[WebResearchResult]:
        query = str(query).strip()
        if not query:
            raise ValueError("research query cannot be empty")
        if len(query) > 500:
            raise ValueError("research query is too long")
        args = [
            "search",
            query,
            "--endpoint",
            self.search_endpoint,
            "--limit",
            str(self.result_limit),
        ]
        if self.allow_loopback_endpoint:
            args.append("--allow-loopback-endpoint")
        payload = self._run_json(args)
        self._require_common(payload, self.SEARCH_SCHEMA)
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise VelourWebUnavailable("Velour search response is missing results")
        if len(raw_results) > self.result_limit:
            raise VelourWebUnavailable("Velour search response exceeded result limit")

        results = []  # type: List[WebResearchResult]
        seen = set()
        for raw in raw_results:
            if not isinstance(raw, dict):
                raise VelourWebUnavailable("Velour search result must be an object")
            result = WebResearchResult(
                result_id=self._required_text(raw, "result_id"),
                title=self._required_text(raw, "title"),
                source=self._required_text(raw, "source"),
                url=self._required_text(raw, "url"),
                summary=str(raw.get("summary") or "").strip(),
            )
            if result.result_id in seen:
                raise VelourWebUnavailable("Velour search returned duplicate result ids")
            seen.add(result.result_id)
            results.append(result)
        return results

    def fetch(self, result: WebResearchResult) -> WebResearchDocument:
        if not isinstance(result, WebResearchResult):
            raise ValueError("fetch requires a WebResearchResult")
        payload = self._run_json(
            [
                "fetch",
                result.url,
                "--result-id",
                result.result_id,
                "--title",
                result.title,
                "--source",
                result.source,
            ]
        )
        self._require_common(payload, self.DOCUMENT_SCHEMA)
        result_id = self._required_text(payload, "result_id")
        if result_id != result.result_id:
            raise VelourWebUnavailable("Velour document result id mismatch")
        text = payload.get("text", "")
        sanitized_html = payload.get("html", "")
        if not isinstance(text, str) or not isinstance(sanitized_html, str):
            raise VelourWebUnavailable("Velour document content must be text")
        byte_length = payload.get("byte_length", 0)
        if not isinstance(byte_length, int) or isinstance(byte_length, bool) or byte_length < 0:
            raise VelourWebUnavailable("Velour document byte length is invalid")

        return WebResearchDocument(
            result_id=result_id,
            title=self._required_text(payload, "title"),
            source=self._required_text(payload, "source"),
            url=self._required_text(payload, "url"),
            text=text,
            html=sanitized_html,
            retrieved_at=self._required_text(payload, "retrieved_at"),
            content_sha256=self._required_text(payload, "content_sha256"),
            content_type=self._required_text(payload, "content_type"),
            byte_length=byte_length,
            authority="none",
            external_reference=True,
        )
