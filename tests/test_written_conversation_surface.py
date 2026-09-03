import pytest

from velvet_interface.scenes.written_conversation_scene import WrittenConversationScene
from velvet_interface.surfaces.pyqt.written_conversation_widget import (
    normalize_conversation_reply,
)


def safe_reply(**overrides):
    value = {
        "conversation_id": "founder-local-conversation",
        "turn_id": "founder-local-conversation:1",
        "turn_number": 1,
        "text": "Cabin temperature is 21.5 °C.",
        "generator": "core-grounded-conversation",
        "requires_authority_check": False,
        "authority_granted": False,
        "grants_execution": False,
        "grants_actuation": False,
    }
    value.update(overrides)
    return value


def test_reply_normalizer_rejects_authority_and_execution_claims():
    assert normalize_conversation_reply(safe_reply())["text"].startswith("Cabin")

    with pytest.raises(ValueError, match="grant authority"):
        normalize_conversation_reply(safe_reply(authority_granted=True))
    with pytest.raises(ValueError, match="grant execution"):
        normalize_conversation_reply(safe_reply(grants_execution=True))
    with pytest.raises(ValueError, match="grant actuation"):
        normalize_conversation_reply(safe_reply(grants_actuation=True))


def test_scene_delegates_only_when_access_is_currently_allowed():
    allowed = {"value": True}
    calls = []

    def submit(text):
        calls.append(text)
        return safe_reply()

    scene = WrittenConversationScene(
        submit_turn=submit,
        access_provider=lambda: allowed["value"],
    )

    result = scene._submit_bounded("What is the cabin temperature?")
    assert result["authority_granted"] is False
    assert calls == ["What is the cabin temperature?"]

    allowed["value"] = False
    with pytest.raises(PermissionError, match="access"):
        scene._submit_bounded("What is the vehicle voltage?")
    assert len(calls) == 1


def test_scene_rejects_non_mapping_submitter_result():
    scene = WrittenConversationScene(
        submit_turn=lambda _text: "not-a-mapping",
        access_provider=lambda: True,
    )
    with pytest.raises(TypeError, match="mapping"):
        scene._submit_bounded("hello")
