import unittest
from pathlib import Path

import yaml

from velvet_interface.founder_surface_launcher import build_parser


class MaintenanceBodyNodesMappingTests(unittest.TestCase):
    def test_right_electronics_desk_keeps_bench_mapped_geometry(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "surfaces" / "vehicle.surface.yaml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        points = {item["id"]: item for item in document["press_points"]}
        desk = points["right_electronics_desk"]

        self.assertEqual(
            desk["polygon"],
            [
                [0.808160, 0.259259],
                [0.841146, 0.209877],
                [0.959833, 0.308519],
                [0.860056, 0.308642],
            ],
        )
        self.assertEqual(desk["action"], "emit:vehicle.electronics.selected")
        self.assertEqual(desk["label"], "Nodes / Body Systems")
        self.assertTrue(desk["enabled"])

    def test_launcher_exposes_read_only_node_evidence_paths(self):
        args = build_parser().parse_args([])
        self.assertEqual(
            args.distributed_lifecycle_journal,
            Path("/var/lib/velvet-runtime/distributed-lifecycle.jsonl"),
        )
        self.assertEqual(args.body_resource_socket, Path("/run/velvet/body-resources.sock"))
        self.assertEqual(args.node_heartbeat_max_age, 20.0)
        self.assertEqual(args.local_node_id, "founder")


if __name__ == "__main__":
    unittest.main()
