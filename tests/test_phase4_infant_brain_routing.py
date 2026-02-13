import copy
import json
import random
import unittest
from pathlib import Path
from unittest.mock import patch

from life_sim.simulation.events import Event, EventManager
from life_sim.simulation.state import SimState


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


class Phase4InfantBrainRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()

    def _make_cfg(self):
        cfg = copy.deepcopy(self.base_config)
        cfg["npc_brain"]["enabled"] = True
        cfg["npc_brain"]["events_enabled"] = True
        cfg["npc_brain"]["infant_brain_v2_enabled"] = True
        cfg["npc_brain"]["infant_brain_v2_debug_logging"] = False
        return cfg

    def test_infant_event_uses_infant_brain_path_when_enabled(self):
        cfg = self._make_cfg()
        random.seed(1111)
        sim = SimState(cfg)
        manager = EventManager(cfg)

        npc = sim._create_npc(age=0, first_name="Route", last_name="Infant")
        npc.age_months = 1
        npc.temperament = {
            "Activity": 50,
            "Regularity": 50,
            "Approach_Withdrawal": 50,
            "Adaptability": 50,
            "Threshold": 50,
            "Intensity": 50,
            "Mood": 50,
            "Distractibility": 50,
            "Persistence": 50,
        }

        event = Event(
            id="EVT_INFANT_ROUTE_TEST",
            title="Route Test",
            description="Routing",
            trigger={"min_age_months": 1, "max_age_months": 1},
            ui_type="single_select",
            once_per_lifetime=False,
            choices=[
                {
                    "text": "Safe soothing",
                    "effects": {
                        "infant_appraisal": {
                            "comfort_value": 0.70,
                            "energy_cost": 0.20,
                            "safety_risk": 0.05,
                            "novelty_load": 0.30,
                            "familiarity": 0.80,
                            "social_soothing": 0.70,
                        }
                    },
                },
                {
                    "text": "High-risk novelty",
                    "effects": {
                        "infant_appraisal": {
                            "comfort_value": 0.90,
                            "energy_cost": 0.40,
                            "safety_risk": 0.95,
                            "novelty_load": 0.95,
                            "familiarity": 0.10,
                            "social_soothing": 0.10,
                        }
                    },
                },
            ],
        )

        with patch("life_sim.simulation.events.NPCBrain.choose", side_effect=AssertionError("NPCBrain route should not be used for infant v2-enabled infant events")):
            selected = manager._choose_indices_with_brain(
                sim,
                npc,
                event,
                domain="event_choice",
                age_months_override=1,
            )

        self.assertEqual(len(selected), 1)
        self.assertIn(selected[0], [0, 1])

    def test_non_infant_event_keeps_npc_brain_route(self):
        cfg = self._make_cfg()
        random.seed(2222)
        sim = SimState(cfg)
        manager = EventManager(cfg)

        npc = sim._create_npc(age=10, first_name="Route", last_name="Older")
        npc.age_months = 120
        npc.temperament = None

        event = Event(
            id="EVT_ROUTE_NON_INFANT",
            title="Route Non Infant",
            description="Routing",
            trigger={"min_age": 8, "max_age": 12},
            ui_type="single_select",
            once_per_lifetime=False,
            choices=[
                {"text": "Choice A", "effects": {"stats": {"happiness": 1}}},
                {"text": "Choice B", "effects": {"stats": {"happiness": -1}}},
            ],
        )

        with patch("life_sim.simulation.events.InfantBrain.choose", side_effect=AssertionError("InfantBrain route should not be used for non-infant events")):
            selected = manager._choose_indices_with_brain(
                sim,
                npc,
                event,
                domain="event_choice",
                age_months_override=120,
            )

        self.assertEqual(len(selected), 1)
        self.assertIn(selected[0], [0, 1])


if __name__ == "__main__":
    unittest.main()
