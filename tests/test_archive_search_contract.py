# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet_interface.archive_search import ArchiveSearchResult, ArchiveSearchSnapshot


class ArchiveSearchContractTests(unittest.TestCase):
    def test_result_requires_known_provider_and_no_authority(self):
        result = ArchiveSearchResult(
            result_id="fs_1",
            provider="library",
            title="Owner notes",
            source="Velour",
            uri="velour-library:lib_1",
        )
        self.assertEqual(result.authority, "none")
        self.assertTrue(result.external_reference)

        with self.assertRaises(ValueError):
            ArchiveSearchResult(
                result_id="fs_2",
                provider="unknown",
                title="Bad provider",
                source="test",
                uri="test:bad",
            )
        with self.assertRaises(ValueError):
            ArchiveSearchResult(
                result_id="fs_3",
                provider="web",
                title="Unsafe",
                source="example.org",
                uri="https://example.org/",
                authority="court",
            )

    def test_snapshot_preserves_known_source_status_only(self):
        snapshot = ArchiveSearchSnapshot(
            query="test",
            results=(),
            sources={
                "library": {"status": "ok", "count": 0},
                "zim": {"status": "disabled", "count": 0},
                "web": {"status": "disabled", "count": 0},
            },
        )
        self.assertEqual(snapshot.authority, "none")

        with self.assertRaises(ValueError):
            ArchiveSearchSnapshot(
                query="test",
                results=(),
                sources={"mystery": {"status": "ok"}},
            )


if __name__ == "__main__":
    unittest.main()
