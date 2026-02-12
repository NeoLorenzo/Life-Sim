import copy
import json
import random
import unittest
from pathlib import Path

from life_sim.simulation import logic
from life_sim.simulation.state import SimState


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


class Phase7NpcApBrainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()

    def _cfg(self, enabled):
        cfg = copy.deepcopy(self.base_config)
        cfg["npc_brain"]["enabled"] = bool(enabled)
        cfg["npc_brain"]["ap_enabled"] = bool(enabled)
        return cfg

    def test_strict_parity_uses_legacy_ap_path_even_when_enabled(self):
        random.seed(7401)
        sim = SimState(self._cfg(True))
        npc = sim._create_npc(age=25, first_name="AP", last_name="Brain")
        npc.job = {"title": "Tester", "salary": 12000}
        npc.school = None
        npc.attendance_rate = 1.0
        npc.target_sleep_hours = 8.0
        npc.ap_used = 0.0

        logic._simulate_npc_routine(sim, npc)

        self.assertGreaterEqual(npc.ap_used, 0.0)
        self.assertLessEqual(npc.ap_used, npc.ap_max)
        self.assertEqual(npc.ap_locked, 8.0)
        # Strict parity: no internal discretionary AP actions yet.
        self.assertNotIn("last_ap_action", npc.brain.get("history", {}))
        self.assertEqual(int(npc.brain["history"].get("ap_decisions", 0)), 0)

    def test_ap_routine_deterministic_same_seed_under_parity_mode(self):
        cfg = self._cfg(True)

        random.seed(7502)
        sim1 = SimState(copy.deepcopy(cfg))
        random.seed(7502)
        sim2 = SimState(copy.deepcopy(cfg))

        random.seed(8801)
        npc1 = sim1._create_npc(age=23, first_name="Det", last_name="One")
        random.seed(8801)
        npc2 = sim2._create_npc(age=23, first_name="Det", last_name="One")

        # Normalize mutable preconditions.
        npc1.job = {"title": "Worker", "salary": 24000}
        npc2.job = {"title": "Worker", "salary": 24000}
        npc1.school = None
        npc2.school = None
        npc1.attendance_rate = npc2.attendance_rate = 1.0
        npc1.target_sleep_hours = npc2.target_sleep_hours = 8.0
        npc1.ap_used = npc2.ap_used = 0.0
        npc1.money = npc2.money = 0
        npc1.health = npc2.health = 50
        npc1.happiness = npc2.happiness = 50

        logic._simulate_npc_routine(sim1, npc1)
        logic._simulate_npc_routine(sim2, npc2)

        self.assertEqual(npc1.ap_used, npc2.ap_used)
        self.assertEqual(npc1.money, npc2.money)
        self.assertEqual(round(float(npc1.health), 6), round(float(npc2.health), 6))
        self.assertEqual(round(float(npc1.happiness), 6), round(float(npc2.happiness), 6))
        self.assertEqual(npc1.brain["history"].get("ap_decisions", 0), npc2.brain["history"].get("ap_decisions", 0))

    def test_legacy_ap_routine_used_when_disabled(self):
        random.seed(7603)
        sim = SimState(self._cfg(False))
        npc = sim._create_npc(age=20, first_name="Legacy", last_name="Path")
        npc.job = None
        npc.school = None
        npc.ap_used = 0.0
        npc.ap_sleep = 9.0

        logic._simulate_npc_routine(sim, npc)

        self.assertEqual(npc.ap_locked, 0.0)
        self.assertEqual(npc.ap_used, 9.0)


if __name__ == "__main__":
    unittest.main()
