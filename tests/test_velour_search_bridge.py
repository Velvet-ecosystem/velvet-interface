# SPDX-License-Identifier: GPL-3.0-only

import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from velvet_interface.velour_search_bridge import (
    VelourSearchBridge,
    VelourSearchUnavailable,
)


class VelourSearchBridgeTests(unittest.TestCase):
    def _executable(self, root: Path) -> Path:
        path = root / "velour-search"
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        return path

    def test_search_invokes_fixed_cli_and_maps_reference_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = self._executable(root)
            library = root / "library"
            library.mkdir()
            payload = {
                "schema": "velour.federated_search.v1",
                "query": "automotive linux",
                "authority": "none",
                "external_reference": True,
                "sources": {
                    "library": {"status": "ok", "count": 1},
                    "zim": {"status": "disabled", "count": 0},
                    "web": {"status": "ok", "count": 1},
                },
                "results": [
                    {
                        "result_id": "fs_local",
                        "provider": "library",
                        "title": "AGL notes",
                        "source": "Velour",
                        "uri": "velour-library:lib_123",
                        "summary": "Local reference",
                        "authority": "none",
                        "external_reference": True,
                        "metadata": {"trust_class": "owner"},
                    },
                    {
                        "result_id": "web:r1",
                        "provider": "web",
                        "title": "AGL",
                        "source": "automotivelinux.org",
                        "uri": "https://www.automotivelinux.org/",
                        "summary": "Web reference",
                        "authority": "none",
                        "external_reference": True,
                        "metadata": {},
                    },
                ],
            }
            completed = SimpleNamespace(
                returncode=0,
                stdout=json.dumps(payload),
                stderr="",
            )
            bridge = VelourSearchBridge(
                executable,
                library,
                kiwix_endpoint="http://127.0.0.1:8080",
                web_endpoint="https://search.example/search",
                timeout_seconds=4.0,
            )
            with patch(
                "velvet_interface.velour_search_bridge.subprocess.run",
                return_value=completed,
            ) as run:
                snapshot = bridge.search("automotive linux", 6)

            self.assertEqual(snapshot.query, "automotive linux")
            self.assertEqual([item.provider for item in snapshot.results], ["library", "web"])
            self.assertEqual(snapshot.sources["zim"]["status"], "disabled")
            argv = run.call_args.args[0]
            self.assertEqual(argv[0], str(executable))
            self.assertIn("--root", argv)
            self.assertIn(str(library), argv)
            self.assertIn("--kiwix-endpoint", argv)
            self.assertIn("http://127.0.0.1:8080", argv)
            self.assertIn("--web-endpoint", argv)
            self.assertIn("https://search.example/search", argv)
            self.assertFalse(run.call_args.kwargs["shell"])

    def test_rejects_authority_crossing_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = self._executable(root)
            payload = {
                "schema": "velour.federated_search.v1",
                "query": "test",
                "authority": "court",
                "external_reference": True,
                "sources": {},
                "results": [],
            }
            bridge = VelourSearchBridge(executable, root / "library")
            completed = SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
            with patch(
                "velvet_interface.velour_search_bridge.subprocess.run",
                return_value=completed,
            ):
                with self.assertRaises(VelourSearchUnavailable):
                    bridge.search("test")

    def test_missing_executable_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bridge = VelourSearchBridge(root / "missing", root / "library")
            with self.assertRaises(VelourSearchUnavailable):
                bridge.search("test")


if __name__ == "__main__":
    unittest.main()
