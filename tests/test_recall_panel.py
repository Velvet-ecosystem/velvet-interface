import unittest

from velvet_interface.core.recall_card import RecallCard
from velvet_interface.core.recall_panel import RecallPanel, RecallPanelSnapshot


class RecallPanelTests(unittest.TestCase):
    def card(self, event_id="memory-1"):
        return RecallCard(event_id, "fact", 0.9, 1.0, 0.8, 0.7, "accepted")

    def test_state_transitions_are_display_only(self):
        panel = RecallPanel(max_cards=2)
        self.assertEqual(panel.snapshot()["state"], "empty")

        panel.set_loading("query-1")
        loading = panel.snapshot()
        self.assertEqual(loading["state"], "loading")
        self.assertEqual(loading["card_count"], 0)

        panel.set_ready([self.card()], "query-1")
        ready = panel.snapshot()
        self.assertEqual(ready["state"], "ready")
        self.assertEqual(ready["card_count"], 1)
        self.assertFalse(ready["truth_claimed"])
        self.assertFalse(ready["authority_granted"])
        self.assertFalse(ready["actuation_granted"])

        panel.set_failed("query-1", "RECALL_UNAVAILABLE")
        failed = panel.snapshot()
        self.assertEqual(failed["state"], "failed")
        self.assertEqual(failed["error_code"], "RECALL_UNAVAILABLE")
        self.assertEqual(failed["cards"], [])

    def test_cards_are_bounded(self):
        panel = RecallPanel(max_cards=1)
        panel.set_ready([self.card("one"), self.card("two")], "query-1")
        snapshot = panel.snapshot()
        self.assertEqual(snapshot["card_count"], 1)
        self.assertEqual(snapshot["cards"][0]["memory_event_id"], "one")

    def test_empty_results_become_empty_state(self):
        panel = RecallPanel()
        panel.set_ready([], "query-1")
        snapshot = panel.snapshot()
        self.assertEqual(snapshot["state"], "empty")
        self.assertEqual(snapshot["query_event_id"], "query-1")

    def test_invalid_state_shapes_are_rejected(self):
        with self.assertRaises(ValueError):
            RecallPanelSnapshot("ready", ()).to_dict()
        with self.assertRaises(ValueError):
            RecallPanelSnapshot("failed", ()).to_dict()


if __name__ == "__main__":
    unittest.main()
