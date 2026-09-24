# SPDX-License-Identifier: GPL-3.0-only
"""Fail-closed configuration helpers for Velour's local Kiwix reader."""

from __future__ import annotations

import ipaddress
import os
from urllib.parse import SplitResult, urlsplit, urlunsplit


DEFAULT_KIWIX_URL = "http://127.0.0.1:8080/"
KIWIX_URL_ENV = "VELOUR_KIWIX_URL"


def _host_is_loopback(host: str) -> bool:
    lowered = host.strip().lower()
    if lowered == "localhost":
        return True
    try:
        return ipaddress.ip_address(lowered).is_loopback
    except ValueError:
        return False


def normalize_kiwix_url(value: str) -> str:
    """Return a normalized HTTP loopback URL or reject it.

    The embedded reader is deliberately not a general-purpose browser.  Kiwix
    may be moved to another loopback port for bench work, but a configured host
    must remain local to Founder.
    """

    raw = str(value).strip()
    if not raw:
        raise ValueError("Kiwix URL is empty")
    parsed = urlsplit(raw)
    if parsed.scheme.lower() != "http":
        raise ValueError("Kiwix URL must use local HTTP")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Kiwix URL must not contain credentials")
    host = parsed.hostname or ""
    if not _host_is_loopback(host):
        raise ValueError("Kiwix URL must remain on loopback")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Kiwix URL contains an invalid port") from exc
    if port is not None and not 1 <= int(port) <= 65535:
        raise ValueError("Kiwix URL port must be between 1 and 65535")

    path = parsed.path or "/"
    normalized = SplitResult(
        scheme="http",
        netloc=parsed.netloc,
        path=path,
        query=parsed.query,
        fragment=parsed.fragment,
    )
    return urlunsplit(normalized)


def configured_kiwix_url() -> str:
    """Return the reviewed embedded Kiwix endpoint from environment/defaults."""

    return normalize_kiwix_url(os.environ.get(KIWIX_URL_ENV, DEFAULT_KIWIX_URL))


def request_url_is_allowed(value: str) -> bool:
    """Return True only for loopback HTTP plus inert in-page URL schemes."""

    parsed = urlsplit(str(value))
    scheme = parsed.scheme.lower()
    if scheme in {"about", "data", "blob"}:
        return True
    if scheme != "http":
        return False
    return _host_is_loopback(parsed.hostname or "")
