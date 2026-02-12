import json
import statistics
import unittest
from pathlib import Path

from life_sim.simulation.brain import (
    CANONICAL_FEATURE_KEYS,
    NPCBrain,
    make_decision_rng,
)


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


class Phase1NpcBrainCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def test_canonical_feature_schema_is_stable(self):
        expected = {
            "delta_happiness",
            "delta_health",
            "delta_money",
            "delta_school",
            "delta_relationship",
            "risk",
            "effort",
            "novelty",
        }
        self.assertEqual(set(CANONICAL_FEATURE_KEYS), expected)

    def test_make_decision_rng_is_deterministic(self):
        r1 = make_decision_rng(42, "npc-00000001", 18, "event_choice", "EVT_X")
        r2 = make_decision_rng(42, "npc-00000001", 18, "event_choice", "EVT_X")
        seq1 = [r1.random() for _ in range(6)]
        seq2 = [r2.random() for _ in range(6)]
        self.assertEqual(seq1, seq2)

    def test_choose_is_deterministic_for_same_seed_and_inputs(self):
        options = [
            {"id": "safe", "features": {"delta_happiness": 0.1, "risk": -0.8, "effort": -0.2}},
            {"id": "bold", "features": {"delta_happiness": 0.4, "novelty": 0.6, "risk": 0.6}},
            {"id": "study", "features": {"delta_school": 0.8, "effort": 0.4, "novelty": 0.1}},
        ]
        brain = NPCBrain(temperature=0.8)
        rng1 = make_decision_rng(123, "npc-00000012", 7, "event_choice", "EVT_TEST")
        rng2 = make_decision_rng(123, "npc-00000012", 7, "event_choice", "EVT_TEST")

        d1 = brain.choose(options, context={"age_months": 7}, rng=rng1)
        d2 = brain.choose(options, context={"age_months": 7}, rng=rng2)
        self.assertEqual(d1["chosen_index"], d2["chosen_index"])
        self.assertEqual(d1["scores"], d2["scores"])
        self.assertEqual(d1["probabilities"], d2["probabilities"])

    def test_temperature_changes_choice_concentration(self):
        options = [
            {"id": "best", "features": {"delta_school": 1.0, "risk": -0.2}},
            {"id": "mid", "features": {"delta_school": 0.6, "risk": 0.0}},
            {"id": "weak", "features": {"delta_school": 0.1, "risk": 0.2}},
        ]
        low_t = NPCBrain(temperature=0.15)
        high_t = NPCBrain(temperature=2.0)

        low_choices = []
        high_choices = []
        for i in range(300):
            rng_low = make_decision_rng(9001, "npc-00000100", i, "event_choice", "EVT_TEMP")
            rng_high = make_decision_rng(9001, "npc-00000100", i, "event_choice", "EVT_TEMP")
            low_choices.append(low_t.choose(options, rng=rng_low)["chosen_index"])
            high_choices.append(high_t.choose(options, rng=rng_high)["chosen_index"])

        low_best_rate = low_choices.count(0) / len(low_choices)
        high_best_rate = high_choices.count(0) / len(high_choices)
        self.assertGreater(low_best_rate, high_best_rate)
        self.assertGreater(low_best_rate, 0.5)

    def test_probabilities_are_valid_distribution(self):
        options = [
            {"features": {"delta_health": 0.5}},
            {"features": {"delta_happiness": 0.4}},
            {"features": {"delta_money": 0.3}},
        ]
        brain = NPCBrain(temperature=1.0)
        out = brain.choose(options, rng=make_decision_rng(77, "npc-7", 2, "ap_choice", "MONTHLY_AP"))
        probs = out["probabilities"]
        self.assertEqual(len(probs), 3)
        self.assertTrue(all(p >= 0.0 for p in probs))
        self.assertAlmostEqual(sum(probs), 1.0, places=8)
        self.assertIn(out["chosen_index"], [0, 1, 2])
        self.assertGreater(statistics.mean(out["scores"]), -1.0)


if __name__ == "__main__":
    unittest.main()
