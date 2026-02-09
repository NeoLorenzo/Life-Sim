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


class Phase2CalendarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def setUp(self):
        random.seed(2202)
        self.school_system = School(self.config["education"])
        self.agent_conf = self.config["agent"]
        self.time_conf = self.config.get("time_management", {})

    def make_agent(self, age=14):
        return Agent(self.agent_conf, is_player=True, age=age, time_config=self.time_conf)

    def test_school_end_releases_ap_lock_for_non_graduate(self):
        player = self.make_agent(age=14)
        player.school = make_school_payload(
            self.school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.ap_locked = 7.0
        player.school["performance"] = 85  # passing

        sim_state = make_state_stub(player, self.school_system, month_index=self.school_system.end_month)
        school_logic._handle_school_end(sim_state, player, self.school_system)

        self.assertIsNotNone(player.school)  # no graduation
        self.assertFalse(player.school["is_in_session"])
        self.assertEqual(player.ap_locked, 0.0)

    def test_school_start_restores_ap_lock_for_returning_student(self):
        player = self.make_agent(age=14)
        player.school = make_school_payload(
            self.school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.school["is_in_session"] = False
        player.ap_locked = 0.0
        player.sync_subjects_with_school(self.school_system, preserve_existing=True)

        sim_state = make_state_stub(player, self.school_system, month_index=self.school_system.start_month)
        school_logic._handle_school_start(sim_state, player, self.school_system)

        self.assertTrue(player.school["is_in_session"])
        self.assertEqual(player.ap_locked, 7.0)


if __name__ == "__main__":
    unittest.main()
