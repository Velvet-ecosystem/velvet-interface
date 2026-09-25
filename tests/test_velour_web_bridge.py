# SPDX-License-Identifier: GPL-3.0-only

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from velvet_interface.velour_web_bridge import VelourWebBridge, VelourWebUnavailable
from velvet_interface.web_research import WebResearchResult


class VelourWebBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.executable = Path(self.tempdir.name) / "velour-web"
        self.executable.write_text("#!/bin/sh\n", encoding="utf-8")
        self.bridge = VelourWebBridge(
            self.executable,
            "https://search.example/search",
            result_limit=3,
        )

    def tearDown(self):
        self.tempdir.cleanup()

    @staticmethod
    def _completed(payload, returncode=0, stderr=""):
        return type(
            "Completed",
            (),
            {
                "stdout": json.dumps(payload) if not isinstance(payload, str) else payload,
                "stderr": stderr,
                "returncode": returncode,
            },
        )()

    def test_search_maps_only_valid_reference_contract(self):
        completed = self._completed(
            {
                "schema": "velour.web_research.search.v1",
                "authority": "none",
                "external_reference": True,
                "query": "embedded ai",
                "results": [
                    {
                        "result_id": "r1",
                        "title": "Reference",
                        "source": "example.org",
                        "url": "https://example.org/reference",
                        "summary": "bounded summary",
                    }
                ],
            }
        )
        with patch(
            "velvet_interface.velour_web_bridge.subprocess.run",
            return_value=completed,
        ) as run:
            results = self.bridge.search("embedded ai")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].result_id, "r1")
        argv = run.call_args.args[0]
        self.assertEqual(argv[0], str(self.executable))
        self.assertEqual(argv[1:3], ["search", "embedded ai"])
        self.assertIn("--endpoint", argv)
        self.assertEqual(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["check"], False)

    def test_search_rejects_authority_claim(self):
        completed = self._completed(
            {
                "schema": "velour.web_research.search.v1",
                "authority": "court",
                "external_reference": True,
                "results": [],
            }
        )
        with patch(
            "velvet_interface.velour_web_bridge.subprocess.run",
            return_value=completed,
        ):
            with self.assertRaises(VelourWebUnavailable):
                self.bridge.search("unsafe")

    def test_fetch_preserves_provenance_and_external_reference(self):
        result = WebResearchResult(
            result_id="r1",
            title="Reference",
            source="example.org",
            url="https://example.org/reference",
        )
        completed = self._completed(
            {
                "schema": "velour.web_research.document.v1",
                "authority": "none",
                "external_reference": True,
                "result_id": "r1",
                "title": "Reference",
                "source": "example.org",
                "url": "https://example.org/reference",
                "text": "Sanitized reference text",
                "html": "<p>Sanitized reference text</p>",
                "retrieved_at": "2026-09-25T07:00:00Z",
                "content_sha256": "a" * 64,
                "content_type": "text/html",
                "byte_length": 128,
            }
        )
        with patch(
            "velvet_interface.velour_web_bridge.subprocess.run",
            return_value=completed,
        ):
            document = self.bridge.fetch(result)
        self.assertEqual(document.content_sha256, "a" * 64)
        self.assertEqual(document.content_type, "text/html")
        self.assertEqual(document.byte_length, 128)
        self.assertEqual(document.authority, "none")
        self.assertTrue(document.external_reference)

    def test_nonzero_adapter_exit_fails_closed(self):
        completed = self._completed("", returncode=2, stderr="blocked by policy")
        with patch(
            "velvet_interface.velour_web_bridge.subprocess.run",
            return_value=completed,
        ):
            with self.assertRaises(VelourWebUnavailable):
                self.bridge.search("blocked")

    def test_missing_executable_fails_closed(self):
        bridge = VelourWebBridge(
            Path(self.tempdir.name) / "missing",
            "https://search.example/search",
        )
        with self.assertRaises(VelourWebUnavailable):
            bridge.search("query")


if __name__ == "__main__":
    unittest.main()
