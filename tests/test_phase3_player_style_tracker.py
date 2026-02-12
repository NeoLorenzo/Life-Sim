import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from life_sim.simulation.events import EventManager
from life_sim.simulation.state import SimState, Agent
from life_sim.simulation.school import School


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def make_school_payload(school_system: School, stage: str, year_label: str = "Year 9", year_index: int = 8):
    return {
        "school_id": school_system.id,
        "school_name": school_system.name,
        "stage": stage,
        "year_index": year_index,
        "year_label": year_label,
        "form_label": "A",
        "performance": 50,
        "is_in_session": True,
    }


def make_sim_state_stub(player, school_system):
    return SimpleNamespace(
        player=player,
        school_system=school_system,
        event_history=[],
        pending_event=None,
        npcs={},
        month_index=1,
        add_log=lambda message, color=None: None,
        _logs=[],
    )


class Phase3PlayerStyleTrackerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def test_tracker_ema_updates_and_observation_count(self):
        cfg = copy.deepcopy(self.config)
        sim = SimState(cfg)
        before = copy.deepcopy(sim.player_style_tracker)

        sim._update_player_style_tracker({"delta_happiness": 0.8, "delta_health": -0.2})
        after = sim.player_style_tracker

        self.assertEqual(int(after["observations"]), int(before["observations"]) + 1)
        self.assertNotEqual(float(after["weights"]["delta_happiness"]), float(before["weights"]["delta_happiness"]))
        self.assertNotEqual(float(after["weights"]["delta_health"]), float(before["weights"]["delta_health"]))

    def test_effective_weights_respect_alpha_toggle_and_bounds(self):
        cfg = copy.deepcopy(self.config)
        cfg["npc_brain"]["player_mimic_enabled"] = False
        sim = SimState(cfg)
        npc = next(iter(sim.npcs.values()))
        base = dict(npc.brain["base_weights"])
        blended = sim.get_effective_brain_weights(npc, relationship_type="Mother")
        self.assertEqual(blended, base)

        cfg2 = copy.deepcopy(self.config)
        cfg2["npc_brain"]["player_mimic_enabled"] = True
        sim2 = SimState(cfg2)
        npc2 = next(iter(sim2.npcs.values()))
        # Force extreme style values to test bounded output.
        sim2.player_style_tracker["weights"] = {k: 9.0 for k in npc2.brain["base_weights"].keys()}
        blended2 = sim2.get_effective_brain_weights(npc2, relationship_type="Mother")
        self.assertTrue(all(-2.0 <= float(v) <= 2.0 for v in blended2.values()))

    def test_relation_override_changes_blend(self):
        cfg = copy.deepcopy(self.config)
        cfg["npc_brain"]["player_mimic_enabled"] = True
        sim = SimState(cfg)
        npc = next(iter(sim.npcs.values()))
        sim.player_style_tracker["weights"] = {k: 1.0 for k in npc.brain["base_weights"].keys()}

        w_classmate = sim.get_effective_brain_weights(npc, relationship_type="Classmate")
        w_mother = sim.get_effective_brain_weights(npc, relationship_type="Mother")
        # Relation alpha override for Mother > Classmate in config, so blend should be further from base.
        diff_classmate = abs(w_classmate["delta_happiness"] - npc.brain["base_weights"]["delta_happiness"])
        diff_mother = abs(w_mother["delta_happiness"] - npc.brain["base_weights"]["delta_happiness"])
        self.assertGreater(diff_mother, diff_classmate)

    def test_event_resolution_updates_tracker_when_method_exists(self):
        cfg = copy.deepcopy(self.config)
        manager = EventManager(cfg)
        school_system = School(cfg["education"])
        player = Agent(cfg["agent"], is_player=True, age=1, time_config=cfg.get("time_management", {}))
        player.school = make_school_payload(school_system, "EYFS", year_label="Nursery", year_index=0)
        sim_state = make_sim_state_stub(player, school_system)

        # Minimal tracker hook as expected by events.apply_resolution.
        tracker = {"count": 0}
        def _update(features):
            tracker["count"] += 1
            tracker["last"] = dict(features)
        sim_state._update_player_style_tracker = _update

        event = next(e for e in manager.events if e.id == "EVT_INFANT_NEW_FOOD_01")
        sim_state.pending_event = event
        manager.apply_resolution(sim_state, event, [0])

        self.assertEqual(tracker["count"], 1)
        self.assertIn("delta_happiness", tracker["last"])


if __name__ == "__main__":
    unittest.main()
