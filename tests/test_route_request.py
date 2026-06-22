import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from velvet_interface.route_request import build_scene_route_request, validate_scene_request_document


class TestSceneRouteRequest(unittest.TestCase):
    def test_builds_minimal_gateway_shape(self):
        request = build_scene_route_request(
            intent_id="intent-1",
            route_id="runtime-status",
            parameters={"detail": "summary"},
        )
        self.assertEqual(request.to_dict()["route_id"], "runtime-status")
        self.assertEqual(request.to_dict()["parameters"], {"detail": "summary"})

    def test_rejects_reserved_parameter(self):
        with self.assertRaises(ValueError):
            build_scene_route_request(
                intent_id="intent-1",
                route_id="runtime-status",
                parameters={"surface": "drive"},
            )

    def test_rejects_extra_top_level_field(self):
        with self.assertRaises(ValueError):
            validate_scene_request_document({
                "intent_id": "intent-1",
                "route_id": "runtime-status",
                "parameters": {},
                "extra": "no",
            })

    def test_requires_normalized_identifiers(self):
        with self.assertRaises(ValueError):
            build_scene_route_request(intent_id="Intent 1", route_id="runtime-status")


if __name__ == "__main__":
    unittest.main()
