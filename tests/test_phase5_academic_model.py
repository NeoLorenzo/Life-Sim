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


class Phase5AcademicModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()

    def make_agent(self, cfg, age=14):
        return Agent(cfg["agent"], is_player=True, age=age, time_config=cfg.get("time_management", {}))

    def make_v2_config(self, noise_cap=0.0):
        cfg = copy.deepcopy(self.base_config)
        school_cfg = cfg["education"]["schools"][cfg["education"]["active_school_id"]]
        school_cfg.setdefault("academic_model", {})
        school_cfg["academic_model"].update(
            {
                "version": "v2",
                "v2_enabled": True,
                "noise_cap": float(noise_cap),
                "convergence_rate": 0.08,
                "readiness_weight": 0.2,
                "effort_weight": 0.15,
                "recovery_boost": 0.1,
                "max_monthly_delta": 3.0,
                "stage_difficulty": {"default": 1.0},
                "category_difficulty": {"default": 1.0, "stem": 1.0},
                "year_difficulty": {"default": 1.0},
            }
        )
        return cfg

    def _run_single_month(self, cfg, attendance_rate, starting_grade, aptitude=78.0, seed=1):
        random.seed(seed)
        school_system = School(cfg["education"])
        player = self.make_agent(cfg, age=14)
        player.school = make_school_payload(
            school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.attendance_rate = attendance_rate
        player._temp_cognitive_penalty = 0.0
        player.subjects = {
            "Mathematics": {
                "current_grade": float(starting_grade),
                "natural_aptitude": float(aptitude),
                "monthly_change": 0.0,
                "category": "stem",
                "progression_rate": 0.02,
            }
        }
        sim_state = make_state_stub(player, school_system, month_index=1)
        school_logic.process_school_turn(sim_state)
        return float(player.subjects["Mathematics"]["current_grade"]), float(player.subjects["Mathematics"]["monthly_change"])

    def test_v2_model_is_deterministic_with_seeded_noise(self):
        cfg = self.make_v2_config(noise_cap=0.2)
        g1, c1 = self._run_single_month(cfg, attendance_rate=0.9, starting_grade=55.0, seed=912)
        g2, c2 = self._run_single_month(cfg, attendance_rate=0.9, starting_grade=55.0, seed=912)
        self.assertAlmostEqual(g1, g2, places=9)
        self.assertAlmostEqual(c1, c2, places=9)

    def test_v2_monotonic_with_attendance(self):
        cfg = self.make_v2_config(noise_cap=0.0)
        high_att_grade, _ = self._run_single_month(cfg, attendance_rate=1.0, starting_grade=55.0, seed=17)
        low_att_grade, _ = self._run_single_month(cfg, attendance_rate=0.4, starting_grade=55.0, seed=17)
        self.assertGreater(high_att_grade, low_att_grade)

    def test_v2_recovery_and_plateau_dynamics(self):
        cfg = self.make_v2_config(noise_cap=0.0)
        recovered_grade, recovered_delta = self._run_single_month(cfg, attendance_rate=1.0, starting_grade=20.0, aptitude=70.0, seed=42)
        plateau_grade, plateau_delta = self._run_single_month(cfg, attendance_rate=1.0, starting_grade=68.0, aptitude=70.0, seed=42)

        self.assertGreater(recovered_delta, 0.0)
        self.assertGreater(recovered_delta, abs(plateau_delta))
        self.assertLessEqual(abs(recovered_delta), 3.0)
        self.assertLessEqual(abs(plateau_delta), 3.0)
        self.assertGreater(recovered_grade, 20.0)


if __name__ == "__main__":
    unittest.main()
