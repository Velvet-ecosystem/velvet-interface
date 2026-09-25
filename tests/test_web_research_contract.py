# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet_interface.web_research import WebResearchDocument, WebResearchResult


class WebResearchContractTests(unittest.TestCase):
    def test_search_result_requires_identity_and_source(self):
        result = WebResearchResult(
            result_id="r1",
            title="Example reference",
            source="example.org",
            url="https://example.org/reference",
            summary="External research result",
        )
        self.assertEqual(result.result_id, "r1")
        self.assertEqual(result.source, "example.org")

        with self.assertRaises(ValueError):
            WebResearchResult(
                result_id="",
                title="Missing identity",
                source="example.org",
                url="https://example.org/",
            )

    def test_document_is_always_external_and_authority_free(self):
        document = WebResearchDocument(
            result_id="r1",
            title="Example reference",
            source="example.org",
            url="https://example.org/reference",
            text="Sanitized reference text",
        )
        self.assertEqual(document.authority, "none")
        self.assertTrue(document.external_reference)

        with self.assertRaises(ValueError):
            WebResearchDocument(
                result_id="r1",
                title="Unsafe",
                source="example.org",
                url="https://example.org/",
                text="payload",
                authority="court",
            )

    def test_document_requires_renderable_reference_content(self):
        with self.assertRaises(ValueError):
            WebResearchDocument(
                result_id="r1",
                title="Empty",
                source="example.org",
                url="https://example.org/",
            )

    def test_document_carries_bounded_fetch_provenance(self):
        document = WebResearchDocument(
            result_id="r1",
            title="Reference",
            source="example.org",
            url="https://example.org/reference",
            html="<p>reference</p>",
            retrieved_at="2026-09-25T07:00:00Z",
            content_sha256="a" * 64,
            content_type="text/html",
            byte_length=128,
        )
        self.assertEqual(document.content_sha256, "a" * 64)
        self.assertEqual(document.byte_length, 128)

        with self.assertRaises(ValueError):
            WebResearchDocument(
                result_id="r1",
                title="Bad digest",
                source="example.org",
                url="https://example.org/reference",
                text="reference",
                content_sha256="not-a-digest",
            )
        with self.assertRaises(ValueError):
            WebResearchDocument(
                result_id="r1",
                title="Bad length",
                source="example.org",
                url="https://example.org/reference",
                text="reference",
                byte_length=-1,
            )


if __name__ == "__main__":
    unittest.main()
