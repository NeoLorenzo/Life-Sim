import json
import random
import unittest
from pathlib import Path
from types import SimpleNamespace

from life_sim.simulation import school as school_logic
from life_sim.simulation.school import School
from life_sim.simulation.state import Agent


ROOT = Path(__file__).resolve().parents[1]


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
        "attendance_months_total": 0,
        "attendance_months_present_equiv": 0.0,
    }


def make_state_stub(player, school_system, month_index=1):
    logs = []
    return SimpleNamespace(
        player=player,
        school_system=school_system,
        event_history=[],
        pending_event=None,
        npcs={},
        month_index=month_index,
        add_log=lambda message, color=None: logs.append((message, color)),
        populate_classmates=lambda: None,
        _logs=logs,
    )


class Phase3AttendanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def setUp(self):
        random.seed(3303)
        self.school_system = School(self.config["education"])
        self.agent_conf = self.config["agent"]
        self.time_conf = self.config.get("time_management", {})

    def make_agent(self, age=14):
        return Agent(self.agent_conf, is_player=True, age=age, time_config=self.time_conf)

    def test_monthly_school_processing_records_attendance(self):
        player = self.make_agent(age=14)
        player.school = make_school_payload(
            self.school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.attendance_rate = 0.6
        player.subjects = {
            "Mathematics": {
                "current_grade": 50.0,
                "natural_aptitude": 70.0,
                "monthly_change": 0.0,
                "category": "stem",
                "progression_rate": 0.02,
            }
        }

        sim_state = make_state_stub(player, self.school_system, month_index=1)
        school_logic.process_school_turn(sim_state)

        self.assertEqual(player.school["attendance_months_total"], 1)
        self.assertAlmostEqual(player.school["attendance_months_present_equiv"], 0.6, places=6)

    def test_year_end_fails_on_attendance_gate_even_with_passing_grade(self):
        player = self.make_agent(age=14)
        player.school = make_school_payload(
            self.school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.school["performance"] = 88  # grade-pass
        player.school["attendance_months_total"] = 10
        player.school["attendance_months_present_equiv"] = 6.0  # 60%

        sim_state = make_state_stub(player, self.school_system, month_index=self.school_system.end_month)
        school_logic._handle_school_end(sim_state, player, self.school_system)

        self.assertIsNotNone(player.school)
        self.assertEqual(player.school["year_index"], 9)  # repeated
        self.assertTrue(any("Attendance too low" in msg for msg, _ in sim_state._logs))

    def test_year_end_passes_when_attendance_meets_gate(self):
        player = self.make_agent(age=14)
        player.school = make_school_payload(
            self.school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.school["performance"] = 88
        player.school["attendance_months_total"] = 10
        player.school["attendance_months_present_equiv"] = 8.0  # 80%

        sim_state = make_state_stub(player, self.school_system, month_index=self.school_system.end_month)
        school_logic._handle_school_end(sim_state, player, self.school_system)

        self.assertIsNotNone(player.school)
        self.assertEqual(player.school["year_index"], 10)  # promoted


if __name__ == "__main__":
    unittest.main()
