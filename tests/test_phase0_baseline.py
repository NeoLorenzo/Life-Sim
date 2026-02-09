import copy
import json
import random
import unittest
from pathlib import Path
from types import SimpleNamespace

from life_sim.simulation import school as school_logic
from life_sim.simulation.school import School
from life_sim.simulation.state import Agent


ROOT = Path(__file__).resolve().parents[1]
BASELINE_FILE = ROOT / "tests" / "baselines" / "phase0_school_snapshot.json"


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def make_school_payload(school_system, stage, year_label, year_index):
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


def make_state_stub(player, school_system):
    logs = []
    return SimpleNamespace(
        player=player,
        school_system=school_system,
        event_history=[],
        pending_event=None,
        npcs={},
        month_index=8,  # September
        add_log=lambda message, color=None: logs.append((message, color)),
        populate_classmates=lambda: None,
        _logs=logs,
    )


def generate_phase0_snapshot(config):
    random.seed(20260209)
    school_system = School(config["education"])
    player = Agent(
        config["agent"],
        is_player=True,
        age=14,
        time_config=config.get("time_management", {}),
    )
    player.school = make_school_payload(
        school_system,
        stage="Key Stage 4 (IGCSE)",
        year_label="Year 10",
        year_index=9,
    )
    player.sync_subjects_with_school(school_system, preserve_existing=False, reset_monthly_change=True)
    sim_state = make_state_stub(player, school_system)

    # Simulate one school year from Sep -> Jun.
    school_months = [8, 9, 10, 11, 0, 1, 2, 3, 4, 5]
    for month in school_months:
        sim_state.month_index = month
        school_logic.process_school_turn(sim_state)

    subject_snapshot = {}
    for name in sorted(player.subjects.keys())[:5]:
        subject_snapshot[name] = round(float(player.subjects[name]["current_grade"]), 3)

    logs = [msg for msg, _ in sim_state._logs]
    return {
        "seed": 20260209,
        "months_simulated": school_months,
        "school": {
            "is_in_session": bool(player.school["is_in_session"]),
            "year_index": int(player.school["year_index"]),
            "year_label": str(player.school["year_label"]),
            "stage": str(player.school["stage"]),
            "performance": int(player.school["performance"]),
            "ap_locked": float(player.ap_locked),
        },
        "subjects": {
            "count": len(player.subjects),
            "sample_first_five_sorted": subject_snapshot,
        },
        "log_count": len(logs),
        "log_tail_last_5": logs[-5:],
    }


class Phase0BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def test_school_future_config_defaults_are_present(self):
        cfg = copy.deepcopy(self.config)
        school_cfg = cfg["education"]["schools"][cfg["education"]["active_school_id"]]
        school_cfg.pop("attendance", None)
        school_cfg.pop("calendar", None)
        school_cfg.pop("academic_model", None)
        school_cfg["structure"].pop("students_per_form", None)
        school_cfg["structure"].pop("form_labels", None)

        school_system = School(cfg["education"])
        self.assertEqual(school_system.attendance_policy["min_promotion_rate"], 0.0)
        self.assertFalse(school_system.calendar_policy["enabled"])
        self.assertEqual(school_system.calendar_policy["base_monthly_loss"], 0.0)
        self.assertEqual(school_system.academic_policy["version"], "v1")
        self.assertFalse(school_system.academic_policy["v2_enabled"])
        self.assertEqual(school_system.students_per_form, school_system.class_capacity)
        self.assertEqual(len(school_system.form_labels), school_system.forms_per_year)

    def test_phase0_snapshot_matches_baseline(self):
        with open(BASELINE_FILE, "r", encoding="utf-8") as f:
            expected = json.load(f)
        current = generate_phase0_snapshot(self.config)
        self.assertEqual(current, expected)


if __name__ == "__main__":
    unittest.main()
