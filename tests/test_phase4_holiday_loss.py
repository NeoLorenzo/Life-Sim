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
        "is_in_session": False,
        "attendance_months_total": 0,
        "attendance_months_present_equiv": 0.0,
    }


def make_state_stub(player, school_system, month_index):
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


class Phase4HolidayLossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def setUp(self):
        random.seed(4404)
        self.school_system = School(self.config["education"])
        self.agent_conf = self.config["agent"]
        self.time_conf = self.config.get("time_management", {})

    def make_agent(self, age=14):
        return Agent(self.agent_conf, is_player=True, age=age, time_config=self.time_conf)

    def test_holiday_loss_applies_during_break_month(self):
        player = self.make_agent(age=14)
        player.school = make_school_payload(
            self.school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.subjects = {
            "Mathematics": {
                "current_grade": 80.0,
                "natural_aptitude": 70.0,
                "monthly_change": 0.0,
                "category": "stem",
                "progression_rate": 0.02,
            }
        }
        sim_state = make_state_stub(player, self.school_system, month_index=6)  # July
        school_logic.process_school_turn(sim_state)

        self.assertLess(player.subjects["Mathematics"]["current_grade"], 80.0)
        self.assertLess(player.subjects["Mathematics"]["monthly_change"], 0.0)

    def test_holiday_loss_not_applied_in_end_month_transition(self):
        player = self.make_agent(age=14)
        player.school = make_school_payload(
            self.school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.school["is_in_session"] = True
        player.school["performance"] = 90
        player.subjects = {
            "Mathematics": {
                "current_grade": 82.0,
                "natural_aptitude": 70.0,
                "monthly_change": 0.0,
                "category": "stem",
                "progression_rate": 0.02,
            }
        }

        sim_state = make_state_stub(player, self.school_system, month_index=self.school_system.end_month)
        school_logic.process_school_turn(sim_state)

        # End-month performs year-end transition only; no immediate holiday drift in same tick.
        self.assertAlmostEqual(player.subjects["Mathematics"]["current_grade"], 82.0, places=6)
        self.assertFalse(player.school["is_in_session"])

    def test_high_conscientiousness_reduces_holiday_loss(self):
        low = self.make_agent(age=14)
        high = self.make_agent(age=14)

        # Force deterministic conscientiousness extremes.
        for agent, competence in ((low, 2), (high, 20)):
            agent.personality["Conscientiousness"]["Competence"] = competence
            agent.personality["Conscientiousness"]["Order"] = competence
            agent.personality["Conscientiousness"]["Self-Discipline"] = competence
            agent.personality["Conscientiousness"]["Deliberation"] = competence
            agent.personality["Conscientiousness"]["Dutifulness"] = competence
            agent.personality["Conscientiousness"]["Achievement"] = competence

            agent.school = make_school_payload(
                self.school_system,
                stage="Key Stage 4 (IGCSE)",
                year_label="Year 10",
                year_index=9,
            )
            agent.subjects = {
                "Mathematics": {
                    "current_grade": 80.0,
                    "natural_aptitude": 70.0,
                    "monthly_change": 0.0,
                    "category": "stem",
                    "progression_rate": 0.02,
                }
            }

        sim_low = make_state_stub(low, self.school_system, month_index=6)
        sim_high = make_state_stub(high, self.school_system, month_index=6)
        school_logic.process_school_turn(sim_low)
        school_logic.process_school_turn(sim_high)

        low_loss = 80.0 - low.subjects["Mathematics"]["current_grade"]
        high_loss = 80.0 - high.subjects["Mathematics"]["current_grade"]
        self.assertGreater(low_loss, high_loss)


if __name__ == "__main__":
    unittest.main()
