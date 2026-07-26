# SPDX-License-Identifier: GPL-3.0-only

import importlib.util
import unittest

from velvet_interface import InterfaceLifecycle as RootInterfaceLifecycle
from velvet_interface.lifecycle import InterfaceLifecycle


class TestInterfaceLifecycle(unittest.TestCase):
    def test_package_and_lifecycle_modules_are_discoverable(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("velvet_interface"))
        self.assertIsNotNone(importlib.util.find_spec("velvet_interface.lifecycle"))

    def test_package_root_exports_same_lifecycle_contract(self) -> None:
        self.assertIs(RootInterfaceLifecycle, InterfaceLifecycle)

    def test_starts_inactive(self) -> None:
        lifecycle = InterfaceLifecycle()
        self.assertFalse(lifecycle.runtime_started)

    def test_runtime_start_is_idempotent(self) -> None:
        lifecycle = InterfaceLifecycle()
        lifecycle.on_runtime_start()
        lifecycle.on_runtime_start()
        self.assertTrue(lifecycle.runtime_started)

    def test_has_no_dynamic_authority_storage(self) -> None:
        lifecycle = InterfaceLifecycle()
        self.assertFalse(hasattr(lifecycle, "__dict__"))

    def test_exposes_no_execution_or_hardware_methods(self) -> None:
        lifecycle = InterfaceLifecycle()
        forbidden = (
            "execute",
            "publish",
            "authorize",
            "open_route",
            "shell",
            "write_can",
            "control_hardware",
        )
        for name in forbidden:
            self.assertFalse(hasattr(lifecycle, name), name)


if __name__ == "__main__":
    unittest.main()
