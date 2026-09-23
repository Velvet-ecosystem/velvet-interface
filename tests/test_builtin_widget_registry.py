# SPDX-License-Identifier: GPL-3.0-only

import os
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

    def test_development_marker_is_presentation_only_input(self):
        with patch.dict(os.environ, {"VELVET_INTERFACE_DEVELOPMENT": "true"}, clear=True):
            self.assertTrue(_development_mode())
        with patch.dict(os.environ, {"VELVET_RUNTIME_MODE": "development"}, clear=True):
            self.assertTrue(_development_mode())
        with patch.dict(os.environ, {"VELVET_INTERFACE_DEVELOPMENT": "false"}, clear=True):
            self.assertFalse(_development_mode())


if __name__ == "__main__":
    unittest.main()
