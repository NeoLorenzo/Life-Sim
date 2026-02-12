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


class Phase5NpcInfantAutoResolveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()

    def _make_enabled_config(self):
        cfg = copy.deepcopy(self.base_config)
        cfg["npc_brain"]["enabled"] = True
        cfg["npc_brain"]["events_enabled"] = True
        cfg["npc_brain"]["ap_enabled"] = False
        return cfg

    def _spawn_test_infant(self, sim_state):
        npc = sim_state._create_npc(age=0, first_name="Infant", last_name="Test")
        npc.age_months = 1
        npc.plasticity = 1.0
        npc.is_personality_locked = False
        return npc

    def test_auto_resolve_infant_npc_event_updates_target_npc(self):
        cfg = self._make_enabled_config()
        sim = SimState(cfg)
        manager = EventManager(cfg)

        npc = self._spawn_test_infant(sim)
        before = dict(npc.temperament)
        player_before = dict(sim.player.temperament) if sim.player.temperament else None
        sim.pending_event = "player-modal-sentinel"

        resolved = manager.auto_resolve_npc_infant_events(sim)
        self.assertGreaterEqual(resolved, 1)
        self.assertNotEqual(before, npc.temperament)
        self.assertIn("EVT_INFANT_NEW_FOOD_01", sim.agent_event_history[npc.uid])
        # NPC autoresolve must not hijack/clear player modal slot.
        self.assertEqual(sim.pending_event, "player-modal-sentinel")
        if player_before is not None:
            self.assertEqual(player_before, sim.player.temperament)

    def test_auto_resolve_is_deterministic_for_same_seed(self):
        cfg = self._make_enabled_config()

        random.seed(5511)
        sim1 = SimState(copy.deepcopy(cfg))
        random.seed(5511)
        sim2 = SimState(copy.deepcopy(cfg))

        m1 = EventManager(cfg)
        m2 = EventManager(cfg)

        random.seed(8821)
        npc1 = self._spawn_test_infant(sim1)
        random.seed(8821)
        npc2 = self._spawn_test_infant(sim2)

        r1 = m1.auto_resolve_npc_infant_events(sim1)
        r2 = m2.auto_resolve_npc_infant_events(sim2)

        self.assertEqual(r1, r2)
        self.assertEqual(sim1.agent_event_history[npc1.uid], sim2.agent_event_history[npc2.uid])
        self.assertEqual(npc1.temperament, npc2.temperament)


if __name__ == "__main__":
    unittest.main()
