# SPDX-License-Identifier: GPL-3.0-only

import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from velvet_interface.surfaces.pyqt.builtin_widget_registry import (
    _development_mode,
    resolve_builtin_widget,
)


class BuiltinWidgetRegistryTests(unittest.TestCase):
    def test_unknown_widget_id_does_not_resolve(self):
        self.assertIsNone(resolve_builtin_widget("python:os.system"))
        self.assertIsNone(resolve_builtin_widget("forge_unknown"))

    def test_velour_web_research_resolves_offline_without_explicit_endpoint(self):
        marker = object()
        with patch.dict(os.environ, {}, clear=True), patch(
            "velvet_interface.surfaces.pyqt.web_research_widget.QtWebResearchWidget",
            return_value=marker,
        ) as factory:
            self.assertIs(resolve_builtin_widget("velour_web_research"), marker)
            factory.assert_called_once_with()

    def test_velour_web_research_wires_only_explicit_provider_boundary(self):
        marker = object()
        bridge_marker = SimpleNamespace(search=object(), fetch=object())
        with patch(
            "velvet_interface.surfaces.pyqt.web_research_widget.QtWebResearchWidget",
            return_value=marker,
        ) as factory, patch(
            "velvet_interface.velour_web_bridge.VelourWebBridge",
            return_value=bridge_marker,
        ) as bridge_factory:
            resolved = resolve_builtin_widget(
                "velour_web_research",
                velour_web_executable=Path("/opt/velour/bin/velour-web"),
                velour_search_endpoint="https://search.example/search",
                velour_allow_loopback_search=False,
            )
        self.assertIs(resolved, marker)
        bridge_factory.assert_called_once_with(
            Path("/opt/velour/bin/velour-web"),
            "https://search.example/search",
            allow_loopback_endpoint=False,
        )
        factory.assert_called_once_with(
            search_provider=bridge_marker.search,
            document_provider=bridge_marker.fetch,
        )

    def test_development_marker_is_presentation_only_input(self):
        with patch.dict(os.environ, {"VELVET_INTERFACE_DEVELOPMENT": "true"}, clear=True):
            self.assertTrue(_development_mode())
        with patch.dict(os.environ, {"VELVET_RUNTIME_MODE": "development"}, clear=True):
            self.assertTrue(_development_mode())
        with patch.dict(os.environ, {"VELVET_INTERFACE_DEVELOPMENT": "false"}, clear=True):
            self.assertFalse(_development_mode())


if __name__ == "__main__":
    unittest.main()
