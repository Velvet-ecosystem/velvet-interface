import unittest

from velvet_interface.core.ghost_can_panel import render_ghost_can_text, view_model_from_ghost_can_event


def safe_event():
    return {"event_type":"vehicle.can.ghost_observation","receipt_id":"receipt-abc","payload":{"status":"observation-only","source":"runtime-can-ghost","source_profile":"tiburon-public-ghost","read_only":True,"synthetic":True,"synthetic_fixture":True,"physical_bus_opened":False,"hardware_bus_opened":False,"can_transmission_attempted":False,"can_transmission_performed":False,"actuation_granted":False,"actuation_performed":False,"authority_granted":False,"signals":[{"signal_name":"vehicle_speed","value":0,"unit":"km/h","confidence":1.0,"observed_at":10.0,"source_profile":"tiburon-public-ghost"},{"name":"engine_rpm","value":850,"unit":"rpm","confidence":0.91,"timestamp":10.0,"source_profile":"tiburon-public-ghost"}]}}


class TestGhostCanPanel(unittest.TestCase):
    def test_accepts_safe_ghost_event(self):
        view_model=view_model_from_ghost_can_event(safe_event())
        self.assertTrue(view_model.is_safe_to_display)
        self.assertEqual(len(view_model.signals),2)
        self.assertFalse(view_model.to_dict()["actuation_granted"])

    def test_renders_terminal_text(self):
        text=render_ghost_can_text(view_model_from_ghost_can_event(safe_event()))
        self.assertIn("Jarred Tiburon",text)
        self.assertIn("vehicle_speed: 0 km/h",text)

    def test_blocks_authority_fields(self):
        event=safe_event(); event["payload"]["route_id"]="can-ghost"
        self.assertFalse(view_model_from_ghost_can_event(event).is_safe_to_display)

    def test_blocks_actuation_claim(self):
        event=safe_event(); event["payload"]["actuation_performed"]=True
        self.assertFalse(view_model_from_ghost_can_event(event).is_safe_to_display)

    def test_blocks_signal_authority_fields(self):
        event=safe_event(); event["payload"]["signals"][0]["command"]="unlock"
        self.assertFalse(view_model_from_ghost_can_event(event).is_safe_to_display)


if __name__ == "__main__":
    unittest.main()
