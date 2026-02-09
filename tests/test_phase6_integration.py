import copy
import json
import random
import statistics
import unittest
from pathlib import Path

from life_sim.simulation import logic
from life_sim.simulation.state import SimState


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def collect_log_text(sim_state):
    entries = []
    for msg, _ in sim_state.current_year_data.get("events", []):
        entries.append(msg)
    for year in sim_state.history:
        for msg, _ in year.get("events", []):
            entries.append(msg)
    return entries


def ensure_player_enrolled(sim_state, target_age=14):
    if sim_state.player.school is not None:
        return

    grade_idx = None
    for idx, grade in enumerate(sim_state.school_system.grades):
        if int(grade["min_age"]) == int(target_age):
            grade_idx = idx
            break
    if grade_idx is None:
        grade_idx = 0
    grade = sim_state.school_system.grades[grade_idx]
    sim_state.player.school = {
        "school_id": sim_state.school_system.id,
        "school_name": sim_state.school_system.name,
        "stage": grade["stage"],
        "year_index": grade_idx,
        "year_label": grade["name"],
        "form_label": sim_state.school_system.form_labels[0],
        "performance": 50,
        "is_in_session": True,
        "attendance_months_total": 0,
        "attendance_months_present_equiv": 0.0,
    }
    sim_state.player.sync_subjects_with_school(sim_state.school_system, preserve_existing=True)


class Phase6IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()

    def make_config(self, initial_age=14, noise_cap=0.05):
        cfg = copy.deepcopy(self.base_config)
        cfg["agent"]["initial_age"] = initial_age
        school_cfg = cfg["education"]["schools"][cfg["education"]["active_school_id"]]
        school_cfg["academic_model"]["v2_enabled"] = True
        school_cfg["academic_model"]["noise_cap"] = float(noise_cap)
        return cfg

    def test_promotion_repeat_and_graduation_paths_through_main_loop(self):
        # Promotion case.
        random.seed(6001)
        sim = SimState(self.make_config(initial_age=14, noise_cap=0.0))
        ensure_player_enrolled(sim, target_age=14)
        sim.month_index = 4  # next turn advances to end_month=5
        sim.player.school["performance"] = 85
        sim.player.school["attendance_months_total"] = 10
        sim.player.school["attendance_months_present_equiv"] = 9.0
        start_idx = sim.player.school["year_index"]
        logic.process_turn(sim)
        self.assertIsNotNone(sim.player.school)
        self.assertEqual(sim.player.school["year_index"], start_idx + 1)
        self.assertEqual(sim.player.ap_locked, 0.0)

        # Repeat due to attendance case.
        random.seed(6002)
        sim = SimState(self.make_config(initial_age=14, noise_cap=0.0))
        ensure_player_enrolled(sim, target_age=14)
        sim.month_index = 4
        sim.player.school["performance"] = 95  # grade-pass, should still fail on attendance gate
        sim.player.school["attendance_months_total"] = 10
        sim.player.school["attendance_months_present_equiv"] = 5.0
        start_idx = sim.player.school["year_index"]
        logic.process_turn(sim)
        self.assertIsNotNone(sim.player.school)
        self.assertEqual(sim.player.school["year_index"], start_idx)
        self.assertEqual(sim.player.ap_locked, 0.0)
        self.assertTrue(any("Attendance too low" in m for m in collect_log_text(sim)))

        # Graduation case.
        random.seed(6003)
        sim = SimState(self.make_config(initial_age=17, noise_cap=0.0))
        ensure_player_enrolled(sim, target_age=17)
        sim.player.school["year_index"] = len(sim.school_system.grades) - 1
        sim.player.school["year_label"] = sim.school_system.grades[-1]["name"]
        sim.player.school["stage"] = sim.school_system.grades[-1]["stage"]
        sim.player.school["is_in_session"] = True
        sim.player.school["performance"] = 90
        sim.player.school["attendance_months_total"] = 10
        sim.player.school["attendance_months_present_equiv"] = 10.0
        sim.player.subjects = {
            "Group 1: Studies in Lang & Lit": {
                "current_grade": 90.0,
                "natural_aptitude": 85.0,
                "monthly_change": 0.0,
                "category": "language",
                "progression_rate": 0.02,
            }
        }
        sim.month_index = 4
        logic.process_turn(sim)
        self.assertIsNone(sim.player.school)
        self.assertEqual(sim.player.ap_locked, 0.0)

    def test_holiday_loss_applies_in_full_turn_loop(self):
        random.seed(6010)
        sim = SimState(self.make_config(initial_age=14, noise_cap=0.0))
        ensure_player_enrolled(sim, target_age=14)
        sim.player.school["is_in_session"] = False
        sim.player.ap_locked = 0.0
        # Pick a stable subject from current portfolio.
        subject = next(iter(sim.player.subjects.keys()))
        before = float(sim.player.subjects[subject]["current_grade"])
        sim.month_index = 6  # next month => 7 (August), still break and not transition month
        logic.process_turn(sim)
        after = float(sim.player.subjects[subject]["current_grade"])
        self.assertLess(after, before)

    def test_seeded_statistical_sanity_for_v2(self):
        means = []
        repeat_counts = []
        for seed in (7101, 7102, 7103):
            random.seed(seed)
            sim = SimState(self.make_config(initial_age=14, noise_cap=0.08))
            ensure_player_enrolled(sim, target_age=14)
            for _ in range(48):  # 4 years
                if not sim.player.is_alive:
                    break
                logic.process_turn(sim)
                if sim.player.school:
                    sim.player.attendance_rate = 0.9

            grades = []
            if sim.player.subjects:
                grades = [float(s["current_grade"]) for s in sim.player.subjects.values()]
            if grades:
                means.append(statistics.mean(grades))

            logs = collect_log_text(sim)
            repeat_counts.append(sum(1 for msg in logs if "You must repeat the year" in msg or "Attendance too low" in msg))

            # Hard bounds should always hold.
            for g in grades:
                self.assertGreaterEqual(g, 0.0)
                self.assertLessEqual(g, 100.0)

        self.assertTrue(means, "Expected at least one run with active subject grades")
        overall_mean = statistics.mean(means)
        self.assertGreater(overall_mean, 25.0)
        self.assertLess(overall_mean, 90.0)
        self.assertLess(statistics.mean(repeat_counts), 4.0)


if __name__ == "__main__":
    unittest.main()
