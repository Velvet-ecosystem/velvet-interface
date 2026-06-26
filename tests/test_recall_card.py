import unittest

from velvet_interface.core.recall_card import RecallCard, recall_card_from_mapping


class RecallCardTests(unittest.TestCase):
    def source(self):
        return {
            "event_id": "memory-1",
            "kind": "fact",
            "score": 0.985,
            "association": 1.0,
            "confidence": 0.9,
            "salience": 1.0,
            "authority_status": "accepted",
            "receipt_id": "receipt-1",
        }

    def test_projects_public_safe_display_state(self):
        card = recall_card_from_mapping(self.source()).to_dict()
        self.assertEqual(card["memory_event_id"], "memory-1")
        self.assertEqual(card["receipt_id"], "receipt-1")
        self.assertEqual(card["mode"], "display-only")
        self.assertFalse(card["truth_claimed"])
        self.assertFalse(card["authority_granted"])
        self.assertFalse(card["actuation_granted"])

    def test_rejects_private_payload(self):
        source = self.source()
        source["raw_memory"] = "hidden"
        with self.assertRaises(ValueError):
            recall_card_from_mapping(source)

    def test_rejects_unbounded_scores(self):
        card = RecallCard("m", "fact", 1.1, 1.0, 0.9, 1.0, "accepted")
        with self.assertRaises(ValueError):
            card.to_dict()


if __name__ == "__main__":
    unittest.main()
