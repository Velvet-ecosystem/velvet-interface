# SPDX-License-Identifier: GPL-3.0-only
"""Small registration seam for the trusted Founder Library Reader scene."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Optional

from velvet_interface.catalog_library_preview import CatalogLibraryPreviewProvider
from velvet_interface.scenes.library_reader_scene import LibraryReaderScene


AccessProvider = Callable[[], bool]


def default_library_root() -> Path:
    """Return the reviewed library root override or the shared vault convention."""

    return Path(os.environ.get("VELVET_LIBRARY_ROOT", "/srv/velvet")).expanduser()


def default_catalog_path() -> Optional[Path]:
    """Return an explicit catalog override when one is configured."""

    value = os.environ.get("VELVET_LIBRARY_CATALOG", "").strip()
    return Path(value).expanduser() if value else None


def build_library_reader_scene(
    *,
    access_provider: AccessProvider,
    library_root: Optional[Path] = None,
    catalog_path: Optional[Path] = None,
    background_path: Optional[Path] = None,
) -> LibraryReaderScene:
    """Build the read-only catalog-aware Library Reader without registering it."""

    root = Path(library_root) if library_root is not None else default_library_root()
    catalog = catalog_path if catalog_path is not None else default_catalog_path()
    provider = CatalogLibraryPreviewProvider(root, catalog_path=catalog)
    return LibraryReaderScene(
        provider=provider,
        access_provider=access_provider,
        background_path=background_path,
    )


def register_library_reader(
    router: Any,
    *,
    access_provider: AccessProvider,
    library_root: Optional[Path] = None,
    catalog_path: Optional[Path] = None,
    background_path: Optional[Path] = None,
) -> LibraryReaderScene:
    """Register one trusted Library Reader scene with an existing Founder router."""

    scene = build_library_reader_scene(
        access_provider=access_provider,
        library_root=library_root,
        catalog_path=catalog_path,
        background_path=background_path,
    )
    scene.bind_router(router)
    router.register_scene(scene)
    return scene
