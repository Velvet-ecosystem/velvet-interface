from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import unittest

from velvet_interface.foundry_bridge import FoundryBridge
from velvet_interface.scenes.character_foundry_scene import CharacterFoundryScene


@dataclass(frozen=True)
class _Summary:
    candidate_id: str
    candidate_kind: str
    display_name: str
    identity_level: int
    content_hash: str


@dataclass(frozen=True)
class _Snapshot:
    summary: _Summary
    normalized: dict


class _FakeService:
    def __init__(self) -> None:
        self.mapping = {
            "candidate": {
                "candidate_id": "candidate_one",
                "candidate_kind": "character",
                "display_name": "Candidate One",
                "identity_level": 2,
            },
            "security_invariants": {"authority_source": "none"},
        }
        self.summary = _Summary(
            candidate_id="candidate_one",
            candidate_kind="character",
            display_name="Candidate One",
            identity_level=2,
            content_hash="sha256:one",
        )

    def scaffold(self, candidate_id, candidate_kind, display_name="", identity_level=None):
        result = dict(self.mapping)
        result["candidate"] = dict(self.mapping["candidate"])
        result["candidate"]["candidate_id"] = candidate_id
        result["candidate"]["candidate_kind"] = candidate_kind
        result["candidate"]["display_name"] = display_name
        if identity_level is not None:
            result["candidate"]["identity_level"] = identity_level
        return result

    def validate(self, mapping):
        return {
            "valid": True,
            "candidate_id": mapping["candidate"]["candidate_id"],
            "normalized": mapping,
            "errors": (),
        }

    def create(self, mapping):
        return _Snapshot(summary=self.summary, normalized=mapping)

    def inspect(self, candidate_id):
        return _Snapshot(summary=self.summary, normalized=self.mapping)

    def list_candidates(self):
        return (self.summary,)

    def update(self, mapping, expected_content_hash):
        return _Snapshot(summary=self.summary, normalized=mapping)

    def discard(self, candidate_id, expected_content_hash):
        return self.summary

    def propose_promotion(self, candidate_id):
        return {
            "candidate_id": candidate_id,
            "promotion_decision": "external_review_required",
            "authority_source": "none",
            "automatic_actions": (),
        }


class _FakeRouter:
    def __init__(self) -> None:
        self.back_calls = 0

    def back(self):
        self.back_calls += 1
        return True


class CharacterFoundryInterfaceTests(unittest.TestCase):
    def test_bridge_is_thin_and_converts_dataclasses_to_plain_data(self):
        bridge = FoundryBridge(Path("unused"), service=_FakeService())
        listed = bridge.list_candidates()
        self.assertEqual(listed[0]["candidate_id"], "candidate_one")
        self.assertEqual(listed[0]["identity_level"], 2)
        created = bridge.create(bridge.scaffold("candidate_one", "character", "Candidate One"))
        self.assertEqual(created["summary"]["content_hash"], "sha256:one")
        self.assertEqual(created["content_hash"], "sha256:one")
        self.assertEqual(created["normalized"]["security_invariants"]["authority_source"], "none")

    def test_bridge_does_not_change_promotion_decision_or_authority(self):
        bridge = FoundryBridge(Path("unused"), service=_FakeService())
        plan = bridge.propose_promotion("candidate_one")
        self.assertEqual(plan["promotion_decision"], "external_review_required")
        self.assertEqual(plan["authority_source"], "none")
        self.assertEqual(plan["automatic_actions"], [])

    def test_scene_access_fails_closed(self):
        bridge = FoundryBridge(Path("unused"), service=_FakeService())
        denied = CharacterFoundryScene(bridge=bridge, access_provider=lambda: False)
        broken = CharacterFoundryScene(
            bridge=bridge,
            access_provider=lambda: (_ for _ in ()).throw(RuntimeError("no access evidence")),
        )
        self.assertFalse(denied._has_access())
        self.assertFalse(broken._has_access())

    def test_scene_back_uses_router_history(self):
        bridge = FoundryBridge(Path("unused"), service=_FakeService())
        scene = CharacterFoundryScene(bridge=bridge, access_provider=lambda: True)
        router = _FakeRouter()
        scene.bind_router(router)
        self.assertTrue(scene._go_back())
        self.assertEqual(router.back_calls, 1)

    def test_scene_defaults_to_reusable_workspace_scroll(self):
        bridge = FoundryBridge(Path("unused"), service=_FakeService())
        scene = CharacterFoundryScene(bridge=bridge, access_provider=lambda: True)
        self.assertEqual(scene.scene_id, "character_foundry")
        self.assertEqual(scene.background_path.as_posix(), "examples/assets/workspace_scroll.png")
        self.assertFalse(scene.is_active)
        scene.on_enter()
        self.assertTrue(scene.is_active)
        scene.on_exit()
        self.assertFalse(scene.is_active)


if __name__ == "__main__":
    unittest.main()
