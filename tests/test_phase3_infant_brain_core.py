import unittest

from life_sim.simulation.brain import (
    CANONICAL_INFANT_APPRAISAL_KEYS,
    DEFAULT_INFANT_PARAMS,
    InfantBrain,
    choice_to_infant_appraisal,
    make_decision_rng,
    temperament_to_infant_params,
)


class Phase3InfantBrainCoreTests(unittest.TestCase):
    def test_infant_appraisal_schema_is_stable(self):
        expected = {
            "comfort_value",
            "energy_cost",
            "safety_risk",
            "novelty_load",
            "familiarity",
            "social_soothing",
        }
        self.assertEqual(set(CANONICAL_INFANT_APPRAISAL_KEYS), expected)

    def test_temperament_mapping_is_bounded(self):
        params = temperament_to_infant_params(
            {
                "Activity": -999,
                "Regularity": 999,
                "Approach_Withdrawal": -50,
                "Adaptability": 500,
                "Threshold": 1000,
                "Intensity": -1000,
                "Mood": 230,
                "Distractibility": -100,
                "Persistence": 400,
            }
        )
        for key in DEFAULT_INFANT_PARAMS.keys():
            self.assertIn(key, params)
            self.assertGreaterEqual(float(params[key]), 0.0)
            self.assertLessEqual(float(params[key]), 1.0)

    def test_novelty_tolerance_moves_with_approach_withdrawal(self):
        base = {
            "Activity": 50,
            "Regularity": 50,
            "Adaptability": 50,
            "Threshold": 50,
            "Intensity": 50,
            "Mood": 50,
            "Distractibility": 50,
            "Persistence": 50,
        }
        low = dict(base, Approach_Withdrawal=10)
        high = dict(base, Approach_Withdrawal=90)
        p_low = temperament_to_infant_params(low)
        p_high = temperament_to_infant_params(high)
        self.assertGreater(p_high["novelty_tolerance"], p_low["novelty_tolerance"])

    def test_choice_appraisal_uses_fallback_when_missing(self):
        choice = {
            "effects": {
                "temperament": {
                    "Activity": 6,
                    "Intensity": 2,
                }
            }
        }
        appraisal = choice_to_infant_appraisal(choice)
        self.assertEqual(set(appraisal.keys()), set(CANONICAL_INFANT_APPRAISAL_KEYS))
        self.assertGreater(appraisal["novelty_load"], 0.35)
        self.assertLess(appraisal["familiarity"], 0.55)

    def test_choice_appraisal_clamps_explicit_values(self):
        choice = {
            "effects": {
                "temperament": {"Activity": 4},
                "infant_appraisal": {
                    "comfort_value": 1.9,
                    "energy_cost": -2.0,
                    "safety_risk": 0.4,
                },
            }
        }
        appraisal = choice_to_infant_appraisal(choice)
        self.assertEqual(appraisal["comfort_value"], 1.0)
        self.assertEqual(appraisal["energy_cost"], 0.0)
        self.assertEqual(appraisal["safety_risk"], 0.4)
        # Missing explicit keys should still be populated via deterministic fallback.
        self.assertIn("novelty_load", appraisal)
        self.assertIn("familiarity", appraisal)
        self.assertIn("social_soothing", appraisal)

    def test_choose_is_deterministic_for_same_seed(self):
        brain = InfantBrain(temperature=0.9)
        options = [
            {"id": "familiar_soothe", "appraisal": {"comfort_value": 0.8, "energy_cost": 0.2, "safety_risk": 0.1, "novelty_load": 0.2, "familiarity": 0.9, "social_soothing": 0.8}},
            {"id": "novel_high", "appraisal": {"comfort_value": 0.5, "energy_cost": 0.7, "safety_risk": 0.3, "novelty_load": 0.9, "familiarity": 0.1, "social_soothing": 0.2}},
            {"id": "neutral", "appraisal": {"comfort_value": 0.5, "energy_cost": 0.4, "safety_risk": 0.2, "novelty_load": 0.5, "familiarity": 0.5, "social_soothing": 0.3}},
        ]
        context = {
            "infant_params": {
                "novelty_tolerance": 0.4,
                "threat_sensitivity": 0.6,
                "energy_budget": 0.4,
                "self_regulation": 0.5,
                "comfort_bias": 0.7,
            },
            "infant_state": {
                "energy_level": 0.55,
                "satiety_level": 0.50,
                "security_level": 0.65,
                "stimulation_load": 0.20,
                "last_event_novelty": 0.30,
            },
        }
        r1 = make_decision_rng(1101, "npc-123", 5, "event_choice", "EVT_INFANT_X")
        r2 = make_decision_rng(1101, "npc-123", 5, "event_choice", "EVT_INFANT_X")
        d1 = brain.choose(options, context=context, rng=r1)
        d2 = brain.choose(options, context=context, rng=r2)
        self.assertEqual(d1["chosen_index"], d2["chosen_index"])
        self.assertEqual(d1["scores"], d2["scores"])
        self.assertEqual(d1["probabilities"], d2["probabilities"])

    def test_safety_penalty_lowers_high_risk_score(self):
        brain = InfantBrain(temperature=1.0)
        context = {
            "infant_params": {
                "novelty_tolerance": 0.5,
                "threat_sensitivity": 0.9,
                "energy_budget": 0.5,
                "self_regulation": 0.5,
                "comfort_bias": 0.5,
            },
            "infant_state": {
                "energy_level": 0.7,
                "satiety_level": 0.7,
                "security_level": 0.7,
                "stimulation_load": 0.2,
                "last_event_novelty": 0.2,
            },
        }

        low_risk = {
            "appraisal": {
                "comfort_value": 0.6,
                "energy_cost": 0.3,
                "safety_risk": 0.2,
                "novelty_load": 0.5,
                "familiarity": 0.5,
                "social_soothing": 0.4,
            }
        }
        high_risk = {
            "appraisal": {
                "comfort_value": 0.6,
                "energy_cost": 0.3,
                "safety_risk": 0.95,
                "novelty_load": 0.5,
                "familiarity": 0.5,
                "social_soothing": 0.4,
            }
        }
        low_score, _ = brain.score_option(low_risk, context=context)
        high_score, _ = brain.score_option(high_risk, context=context)
        self.assertGreater(low_score, high_score)


if __name__ == "__main__":
    unittest.main()
