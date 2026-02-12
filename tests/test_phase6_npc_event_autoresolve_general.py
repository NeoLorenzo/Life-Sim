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


class Phase6NpcEventAutoResolveGeneralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()

    def _cfg_enabled(self):
        cfg = copy.deepcopy(self.base_config)
        cfg["npc_brain"]["enabled"] = True
        cfg["npc_brain"]["events_enabled"] = True
        return cfg

    def test_per_event_npc_auto_opt_out_is_respected(self):
        cfg = self._cfg_enabled()
        random.seed(6101)
        sim = SimState(cfg)
        manager = EventManager(cfg)

        npc = sim._create_npc(age=0, first_name="OptOut", last_name="NPC")
        npc.age_months = 1
        npc.plasticity = 1.0
        npc.is_personality_locked = False
        sim.npcs = {npc.uid: npc}
        sim.agent_event_history = {sim.player.uid: sim.agent_event_history.get(sim.player.uid, []), npc.uid: []}

        target = next(e for e in manager.events if e.id == "EVT_INFANT_NEW_FOOD_01")
        target.npc_auto = False

        before = dict(npc.temperament)
        resolved = manager.auto_resolve_npc_events(sim)
        self.assertEqual(resolved, 0)
        self.assertEqual(before, npc.temperament)
        self.assertEqual(sim.agent_event_history[npc.uid], [])

    def test_non_infant_npc_event_autoresolves_igcse(self):
        cfg = self._cfg_enabled()
        random.seed(6202)
        sim = SimState(cfg)
        manager = EventManager(cfg)

        npc = sim._create_npc(age=14, first_name="IG", last_name="CSE")
        # Ensure this NPC is in IGCSE stage context.
        npc.school = {
            "school_id": sim.school_system.id,
            "school_name": sim.school_system.name,
            "stage": "Key Stage 4 (IGCSE)",
            "year_index": 9,
            "year_label": "Year 10",
            "form_label": "A",
            "performance": 50,
            "is_in_session": True,
            "attendance_months_total": 0,
            "attendance_months_present_equiv": 0.0,
        }
        npc.sync_subjects_with_school(sim.school_system, preserve_existing=True)

        resolved = manager.auto_resolve_npc_events(sim)
        self.assertGreaterEqual(resolved, 1)
        self.assertIn("EVT_IGCSE_SUBJECTS", sim.agent_event_history[npc.uid])
        self.assertIsInstance(npc.school.get("igcse_subjects"), list)
        self.assertGreater(len(npc.school.get("igcse_subjects")), 0)

    def test_phase5_infant_wrapper_still_works(self):
        cfg = self._cfg_enabled()
        random.seed(6303)
        sim = SimState(cfg)
        manager = EventManager(cfg)

        npc = sim._create_npc(age=0, first_name="Inf", last_name="Wrap")
        npc.age_months = 1
        npc.plasticity = 1.0
        npc.is_personality_locked = False

        resolved = manager.auto_resolve_npc_infant_events(sim)
        self.assertGreaterEqual(resolved, 1)
        self.assertIn("EVT_INFANT_NEW_FOOD_01", sim.agent_event_history[npc.uid])


if __name__ == "__main__":
    unittest.main()
