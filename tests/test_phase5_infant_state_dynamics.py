import copy
import json
import random
import unittest
from pathlib import Path

from life_sim.simulation.events import EventManager
from life_sim.simulation.state import SimState


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


class Phase5InfantStateDynamicsTests(unittest.TestCase):
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

    def _spawn_infant(self, sim):
        npc = sim._create_npc(age=0, first_name="State", last_name="Infant")
        npc.age_months = 2
        npc.temperament = {
            "Activity": 60,
            "Regularity": 55,
            "Approach_Withdrawal": 45,
            "Adaptability": 52,
            "Threshold": 50,
            "Intensity": 48,
            "Mood": 57,
            "Distractibility": 49,
            "Persistence": 54,
        }
        return npc

    def test_monthly_homeostasis_updates_infant_state_when_enabled(self):
        cfg = self._make_cfg()
        random.seed(731)
        sim = SimState(cfg)
        infant = self._spawn_infant(sim)
        sim._ensure_infant_brain_state(infant)
        before = dict(infant.brain.get("infant_state", {}))

        sim._update_infant_state_monthly(infant)
        after = dict(infant.brain.get("infant_state", {}))

        self.assertNotEqual(before, after)
        for key, value in after.items():
            self.assertGreaterEqual(float(value), 0.0)
            self.assertLessEqual(float(value), 1.0)

    def test_event_resolution_applies_post_choice_infant_state_transition(self):
        cfg = self._make_cfg()
        random.seed(911)
        sim = SimState(cfg)
        manager = EventManager(cfg)
        infant = self._spawn_infant(sim)
        sim._ensure_infant_brain_state(infant)
        before = dict(infant.brain.get("infant_state", {}))

        event = next(e for e in manager.events if e.id == "EVT_INFANT_NEW_FOOD_01")
        manager.apply_resolution_to_agent(
            sim,
            infant,
            event,
            [0],
            history_store=sim.agent_event_history.setdefault(infant.uid, []),
            emit_output=False,
        )
        after = dict(infant.brain.get("infant_state", {}))

        self.assertNotEqual(before, after)
        self.assertIn("last_event_novelty", after)
        self.assertGreaterEqual(float(after["last_event_novelty"]), 0.0)
        self.assertLessEqual(float(after["last_event_novelty"]), 1.0)

    def test_monthly_update_skips_non_infant_agents(self):
        cfg = self._make_cfg()
        random.seed(121)
        sim = SimState(cfg)
        older = sim._create_npc(age=10, first_name="State", last_name="Older")
        older.age_months = 120
        older.temperament = None
        sim._ensure_infant_brain_state(older)
        before = dict(older.brain.get("infant_state", {}))

        sim._update_infant_state_monthly(older)
        after = dict(older.brain.get("infant_state", {}))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
