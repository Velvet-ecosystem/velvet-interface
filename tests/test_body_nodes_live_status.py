import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from velvet_interface.body_nodes_live_status import load_body_nodes_status


class BodyNodesLiveStatusTests(unittest.TestCase):
    def _journal(self, root, records):
        path = Path(root) / "distributed-lifecycle.jsonl"
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        return path

    def _node_record(self, node_id, heartbeat, **overrides):
        payload = {
            "node_id": node_id,
            "body_id": "velvet-body",
            "organ": "velour",
            "tier": "specialist_linux",
            "capabilities": ["library.retrieve"],
            "current_load": 0.25,
            "health": 0.95,
            "availability": "available",
            "last_heartbeat": heartbeat,
            "max_concurrent_tasks": 1,
            "current_tasks": 0,
            "accepted_work_classes": ["record-summary"],
            "refused_work_classes": [],
            "overflow_capabilities": [],
            "temporary_absorption_capabilities": [],
            "fallback_options": [],
            "body_verified": True,
            "continuity_verified": True,
            "transport_only": True,
            "canonical": False,
            "grants_authority": False,
            "grants_execution": False,
            "grants_actuation": False,
            "authority": "none",
        }
        payload.update(overrides)
        return {
            "schema": "velvet.runtime.lifecycle_journal.v1",
            "recorded_at": heartbeat,
            "event_type": "NODE_ADVERTISEMENT_PUBLISHED",
            "subject_id": node_id,
            "receipt_id": "receipt-%s" % node_id,
            "payload": payload,
        }

    def test_fresh_node_is_online_and_uses_newest_heartbeat(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = self._journal(
                directory,
                [
                    self._node_record("velour-lyra-1", 80.0, current_load=0.9),
                    self._node_record("velour-lyra-1", 95.0, current_load=0.2),
                ],
            )
            status = load_body_nodes_status(journal, now=100.0)

        self.assertEqual(len(status.nodes), 1)
        node = status.nodes[0]
        self.assertEqual(node.node_id, "velour-lyra-1")
        self.assertEqual(node.state, "ONLINE")
        self.assertEqual(node.heartbeat_age_seconds, 5.0)
        self.assertEqual(node.current_load, 0.2)
        self.assertFalse(node.resource_visible)

    def test_stale_node_is_not_reported_online(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = self._journal(
                directory,
                [self._node_record("security-lyra-1", 50.0, organ="security")],
            )
            status = load_body_nodes_status(
                journal,
                now=100.0,
                max_heartbeat_age_seconds=20.0,
            )

        self.assertEqual(status.nodes[0].state, "STALE")

    def test_resource_snapshot_merges_founder_and_body_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = self._journal(
                directory,
                [self._node_record("velour-lyra-1", 99.0)],
            )

            def resources(_now):
                return SimpleNamespace(
                    body_id="velvet-body",
                    node_ids=("founder", "velour-lyra-1"),
                    totals=(
                        SimpleNamespace(
                            kind=SimpleNamespace(value="memory"),
                            unit="bytes",
                            capacity=1024.0,
                            available=512.0,
                            resource_count=2,
                        ),
                    ),
                )

            status = load_body_nodes_status(
                journal,
                resource_snapshot_provider=resources,
                now=100.0,
                local_node_id="founder",
            )

        self.assertEqual([item.node_id for item in status.nodes], ["founder", "velour-lyra-1"])
        self.assertEqual(status.nodes[0].state, "LOCAL")
        self.assertTrue(status.nodes[0].resource_visible)
        self.assertTrue(status.nodes[1].resource_visible)
        self.assertTrue(status.resource_snapshot_available)
        self.assertEqual(status.body_id, "velvet-body")
        self.assertEqual(status.resource_totals[0].kind, "memory")
        self.assertEqual(status.resource_totals[0].available, 512.0)

    def test_bad_resource_provider_does_not_erase_functional_nodes(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = self._journal(
                directory,
                [self._node_record("velour-lyra-1", 99.0)],
            )

            def broken(_now):
                raise RuntimeError("offline")

            status = load_body_nodes_status(
                journal,
                resource_snapshot_provider=broken,
                now=100.0,
            )

        self.assertEqual(len(status.nodes), 1)
        self.assertEqual(status.nodes[0].state, "ONLINE")
        self.assertFalse(status.resource_snapshot_available)
        self.assertIn("Resource snapshot unavailable", status.message)

    def test_authority_bearing_journal_entry_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            unsafe = self._node_record("rogue", 99.0)
            unsafe["payload"]["authority"] = "court"
            journal = self._journal(directory, [unsafe])
            status = load_body_nodes_status(journal, now=100.0)

        self.assertEqual(status.nodes, ())


if __name__ == "__main__":
    unittest.main()
