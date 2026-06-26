import json
import pathlib
import unittest

from velvet_interface.core.recall_adapter import recall_card_from_runtime_result


class RecallAdapterTests(unittest.TestCase):
    def fixture(self):
        path = pathlib.Path(__file__).parent / "fixtures" / "runtime_memory_recall_result_v1.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_projects_runtime_fixture_without_field_drift(self):
        card = recall_card_from_runtime_result(self.fixture()).to_dict()
        self.assertEqual(card["memory_event_id"], "memory-1")
        self.assertEqual(card["memory_kind"], "fact")
        self.assertEqual(card["score"], 0.985)
        self.assertEqual(card["authority_status"], "accepted")
        self.assertEqual(card["receipt_id"], "receipt-1")
        self.assertNotIn("authority_weight", card)
        self.assertNotIn("record", card)
        self.assertFalse(card["truth_claimed"])
        self.assertFalse(card["authority_granted"])

    def test_rejects_private_nested_fields(self):
        document = self.fixture()
        document["record"]["raw_memory"] = "hidden"
        with self.assertRaises(ValueError):
            recall_card_from_runtime_result(document)

    def test_rejects_event_id_mismatch(self):
        document = self.fixture()
        document["score"]["event_id"] = "other"
        with self.assertRaises(ValueError):
            recall_card_from_runtime_result(document)


if __name__ == "__main__":
    unittest.main()
