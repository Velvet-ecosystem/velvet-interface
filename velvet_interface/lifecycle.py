# SPDX-License-Identifier: GPL-3.0-only
"""Narrow lifecycle boundary used by Velvet Runtime.

This hook reports that the presentation layer may begin its normal lifecycle
after Runtime has completed secure boot. It grants no authority, opens no
routes, creates no display, and performs no hardware or shell action.
"""

from __future__ import annotations


class InterfaceLifecycle:
    """Idempotent, non-authoritative Interface lifecycle marker."""

    __slots__ = ("_runtime_started",)

    def __init__(self) -> None:
        self._runtime_started = False

    @property
    def runtime_started(self) -> bool:
        """Whether Runtime has announced successful post-secure-boot start."""

        return self._runtime_started

    def on_runtime_start(self) -> None:
        """Record Runtime start without acquiring capabilities or authority."""

        self._runtime_started = True
