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


def make_cfg(v2_enabled):
    cfg = load_config()
    cfg = copy.deepcopy(cfg)
    cfg["npc_brain"]["enabled"] = True
    cfg["npc_brain"]["events_enabled"] = True
    cfg["npc_brain"]["infant_brain_v2_enabled"] = bool(v2_enabled)
    cfg["npc_brain"]["infant_brain_v2_debug_logging"] = False
    return cfg


def make_infant_event(event_id="EVT_INFANT_REGRESSION_TEST"):
    return Event(
        id=event_id,
        title="Infant Regression Test",
        description="Infant routing test event.",
        trigger={"min_age_months": 1, "max_age_months": 1},
        ui_type="single_select",
        once_per_lifetime=False,
        choices=[
            {
                "text": "Comfort-first",
                "effects": {
                    "temperament": {"Mood": 2},
                    "infant_appraisal": {
                        "comfort_value": 0.85,
                        "energy_cost": 0.20,
                        "safety_risk": 0.05,
                        "novelty_load": 0.25,
                        "familiarity": 0.90,
                        "social_soothing": 0.80,
                    },
                },
            },
            {
                "text": "Novel-risky",
                "effects": {
                    "temperament": {"Intensity": 3},
                    "infant_appraisal": {
                        "comfort_value": 0.55,
                        "energy_cost": 0.70,
                        "safety_risk": 0.80,
                        "novelty_load": 0.95,
                        "familiarity": 0.15,
                        "social_soothing": 0.10,
                    },
                },
            },
        ],
    )


def make_non_infant_event(event_id="EVT_NON_INFANT_PARITY_TEST"):
    return Event(
        id=event_id,
        title="Non-Infant Parity Test",
        description="Non-infant route should be unaffected by infant-v2 flag.",
        trigger={"min_age": 8, "max_age": 12},
        ui_type="single_select",
        once_per_lifetime=False,
        choices=[
            {"text": "Option A", "effects": {"stats": {"happiness": 2}}},
            {"text": "Option B", "effects": {"stats": {"happiness": -1}}},
        ],
    )


class Phase7InfantBrainRegressionShieldTests(unittest.TestCase):
    def _spawn_infant(self, sim):
        npc = sim._create_npc(age=0, first_name="Shield", last_name="Infant")
        npc.age_months = 1
        npc.plasticity = 1.0
        npc.is_personality_locked = False
        npc.temperament = {
            "Activity": 55,
            "Regularity": 52,
            "Approach_Withdrawal": 49,
            "Adaptability": 50,
            "Threshold": 48,
            "Intensity": 51,
            "Mood": 57,
            "Distractibility": 47,
            "Persistence": 54,
        }
        return npc

    def test_infant_v2_path_does_not_call_legacy_event_feature_mapper(self):
        cfg = make_cfg(v2_enabled=True)
        random.seed(7001)
        sim = SimState(cfg)
        manager = EventManager(cfg)
        npc = self._spawn_infant(sim)
        event = make_infant_event()

        with patch(
            "life_sim.simulation.events.event_choice_to_features",
            side_effect=AssertionError("legacy mapper must not be used in infant v2 path"),
        ):
            selected = manager._choose_indices_with_brain(
                sim,
                npc,
                event,
                domain="event_choice",
                age_months_override=1,
            )
        self.assertEqual(len(selected), 1)
        self.assertIn(selected[0], [0, 1])

    def test_non_infant_behavior_is_identical_with_v2_toggle(self):
        cfg_off = make_cfg(v2_enabled=False)
        cfg_on = make_cfg(v2_enabled=True)
        random.seed(7002)
        sim_off = SimState(copy.deepcopy(cfg_off))
        random.seed(7002)
        sim_on = SimState(copy.deepcopy(cfg_on))
        manager_off = EventManager(cfg_off)
        manager_on = EventManager(cfg_on)

        npc_off = sim_off._create_npc(age=10, first_name="Parity", last_name="Off")
        npc_off.age_months = 120
        npc_off.temperament = None

        npc_on = sim_on._create_npc(age=10, first_name="Parity", last_name="Off")
        npc_on.age_months = 120
        npc_on.temperament = None

        event = make_non_infant_event()
        selected_off = manager_off._choose_indices_with_brain(
            sim_off, npc_off, event, domain="event_choice", age_months_override=120
        )
        selected_on = manager_on._choose_indices_with_brain(
            sim_on, npc_on, event, domain="event_choice", age_months_override=120
        )
        self.assertEqual(selected_off, selected_on)

    def test_infant_v2_selection_is_deterministic_same_seed_and_inputs(self):
        cfg = make_cfg(v2_enabled=True)
        random.seed(7003)
        sim1 = SimState(copy.deepcopy(cfg))
        random.seed(7003)
        sim2 = SimState(copy.deepcopy(cfg))
        manager1 = EventManager(cfg)
        manager2 = EventManager(cfg)
        npc1 = self._spawn_infant(sim1)
        npc2 = self._spawn_infant(sim2)
        event = make_infant_event(event_id="EVT_INFANT_DETERMINISM_TEST")

        out1 = manager1._choose_indices_with_brain(
            sim1, npc1, event, domain="event_choice", age_months_override=1
        )
        out2 = manager2._choose_indices_with_brain(
            sim2, npc2, event, domain="event_choice", age_months_override=1
        )
        self.assertEqual(out1, out2)

    def test_infant_context_params_follow_temperament_differences(self):
        cfg = make_cfg(v2_enabled=True)
        random.seed(7004)
        sim = SimState(cfg)
        manager = EventManager(cfg)

        a = self._spawn_infant(sim)
        b = self._spawn_infant(sim)
        a.temperament["Approach_Withdrawal"] = 90
        b.temperament["Approach_Withdrawal"] = 10
        event = make_infant_event(event_id="EVT_INFANT_PARAM_DIFF_TEST")

        ctx_a = manager._build_infant_brain_context(sim, a)
        ctx_b = manager._build_infant_brain_context(sim, b)
        self.assertGreater(
            float(ctx_a["infant_params"]["novelty_tolerance"]),
            float(ctx_b["infant_params"]["novelty_tolerance"]),
        )


if __name__ == "__main__":
    unittest.main()
