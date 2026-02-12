import copy
import json
import random
import unittest
from pathlib import Path

from life_sim.simulation.brain import CANONICAL_FEATURE_KEYS, DEFAULT_BASE_WEIGHTS
from life_sim.simulation.state import Agent, SimState


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def assert_brain_shape(testcase, brain):
    testcase.assertIsInstance(brain, dict)
    testcase.assertIn("version", brain)
    testcase.assertIn("drives", brain)
    testcase.assertIn("decision_style", brain)
    testcase.assertIn("base_weights", brain)
    testcase.assertIn("player_style_weights", brain)
    testcase.assertIn("history", brain)

    for key in ("comfort", "achievement", "social", "risk_avoidance", "novelty", "discipline"):
        testcase.assertIn(key, brain["drives"])
        testcase.assertGreaterEqual(float(brain["drives"][key]), 0.0)
        testcase.assertLessEqual(float(brain["drives"][key]), 1.0)

    for key in CANONICAL_FEATURE_KEYS:
        testcase.assertIn(key, brain["base_weights"])
        testcase.assertIn(key, brain["player_style_weights"])


class Phase2NpcBrainWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def test_agent_has_brain_scaffold_even_without_simstate(self):
        random.seed(9201)
        agent = Agent(self.config["agent"], is_player=False, age=10, time_config=self.config.get("time_management", {}))
        assert_brain_shape(self, agent.brain)

    def test_simstate_initializes_brains_for_player_and_npcs(self):
        random.seed(9202)
        sim_state = SimState(copy.deepcopy(self.config))

        assert_brain_shape(self, sim_state.player.brain)
        self.assertFalse(bool(sim_state.player.brain.get("enabled", True)))
        self.assertGreater(len(sim_state.npcs), 0)

        for npc in sim_state.npcs.values():
            assert_brain_shape(self, npc.brain)
            self.assertFalse(bool(npc.brain.get("enabled", True)))
            self.assertEqual(set(npc.brain["base_weights"].keys()), set(DEFAULT_BASE_WEIGHTS.keys()))

    def test_brain_profiles_are_reproducible_for_same_seed(self):
        cfg = copy.deepcopy(self.config)

        random.seed(9303)
        s1 = SimState(copy.deepcopy(cfg))
        random.seed(9303)
        s2 = SimState(copy.deepcopy(cfg))

        self.assertEqual(s1.player.brain, s2.player.brain)

        npc1_uids = sorted(s1.npcs.keys())
        npc2_uids = sorted(s2.npcs.keys())
        self.assertEqual(npc1_uids, npc2_uids)
        # Compare first few to keep test quick/clear.
        for uid in npc1_uids[:5]:
            self.assertEqual(s1.npcs[uid].brain, s2.npcs[uid].brain)


if __name__ == "__main__":
    unittest.main()
