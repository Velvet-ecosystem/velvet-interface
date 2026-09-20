# SPDX-License-Identifier: GPL-3.0-only
"""Narrow presentation bridge to Eleanor's isolated engineering environment."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
from typing import Any, Dict

class EleanorUnavailable(RuntimeError):
    """Raised when the canonical Eleanor CLI cannot provide presentation data."""

class EleanorBridge:
    """Read-only adapter over the canonical Eleanor CLI."""
    def __init__(self, executable: Path, manifest: Path, timeout_seconds: float = 5.0) -> None:
        self.executable = Path(executable).expanduser()
        self.manifest = Path(manifest).expanduser()
        self.timeout_seconds = float(timeout_seconds)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def _run_json(self, command: str) -> Dict[str, Any]:
        if command not in {"validate", "coverage"}:
            raise ValueError("Eleanor bridge command is not allow-listed")
        if not self.executable.is_file():
            raise EleanorUnavailable("Eleanor executable not found: %s" % self.executable)
        if not self.manifest.is_file():
            raise EleanorUnavailable("Eleanor project manifest not found: %s" % self.manifest)
        try:
            result = subprocess.run(
                [str(self.executable), command, str(self.manifest), "--json"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=self.timeout_seconds, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise EleanorUnavailable("Eleanor command unavailable: %s" % exc) from exc
        try:
            payload = json.loads(result.stdout)
        except (TypeError, ValueError) as exc:
            detail = result.stderr.strip() or result.stdout.strip() or "no output"
            raise EleanorUnavailable("Eleanor returned invalid JSON: %s" % detail) from exc
        if not isinstance(payload, dict):
            raise EleanorUnavailable("Eleanor response must be a JSON object")
        return payload

    def validate(self) -> Dict[str, Any]:
        return self._run_json("validate")

    def coverage(self) -> Dict[str, Any]:
        return self._run_json("coverage")
