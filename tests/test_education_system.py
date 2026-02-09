import json
import random
import unittest
from pathlib import Path
from types import SimpleNamespace

from life_sim.simulation.events import EventManager
from life_sim.simulation.school import School, apply_academic_delta
from life_sim.simulation.state import Agent
from life_sim.simulation import school as school_logic


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
    log_messages = []
    return SimpleNamespace(
        player=player,
        school_system=school_system,
        event_history=[],
        pending_event=None,
        npcs={},
        month_index=1,  # January; avoids start/end transitions
        add_log=lambda message, color=None: log_messages.append((message, color)),
        _logs=log_messages,
    )


class EducationSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def setUp(self):
        random.seed(1234)
        self.school_system = School(self.config["education"])
        self.agent_conf = self.config["agent"]

    def make_agent(self, age=14):
        return Agent(self.agent_conf, is_player=True, age=age, time_config=self.config.get("time_management", {}))

    def test_school_loads_stage_curriculum_from_config(self):
        ks3 = self.school_system.get_stage_subjects("Key Stage 3")
        self.assertIn("Mathematics", ks3)
        self.assertIn("Computing", ks3)
        self.assertEqual(len(ks3), len(set(ks3)))

    def test_stage_transition_preserves_overlap_and_retires_old_subjects(self):
        agent = self.make_agent(age=10)
        agent.school = make_school_payload(self.school_system, stage="Key Stage 1", year_label="Year 2", year_index=3)
        self.assertTrue(agent.sync_subjects_with_school(self.school_system, preserve_existing=True))
        self.assertIn("Phonics", agent.subjects)
        self.assertIn("Mathematics", agent.subjects)

        # Set a known carry-over grade for overlap validation.
        agent.subjects["Mathematics"]["current_grade"] = 77.0

        agent.school["stage"] = "Key Stage 2"
        agent.school["year_label"] = "Year 3"
        agent.school["year_index"] = 4
        self.assertTrue(agent.sync_subjects_with_school(self.school_system, preserve_existing=True, reset_monthly_change=True))

        self.assertNotIn("Phonics", agent.subjects)
        self.assertIn("Computing", agent.subjects)
        self.assertAlmostEqual(agent.subjects["Mathematics"]["current_grade"], 77.0, places=6)

    def test_igcse_selection_validation_enforces_science_track_and_core(self):
        manager = EventManager(self.config)
        igcse_event = next(e for e in manager.events if e.id == "EVT_IGCSE_SUBJECTS")
        player = self.make_agent(age=14)
        player.school = make_school_payload(self.school_system, stage="Key Stage 4 (IGCSE)", year_label="Year 10", year_index=9)
        sim_state = make_sim_state_stub(player, self.school_system)
        runtime_event = manager._build_igcse_event(igcse_event, sim_state)

        # Invalid: no science track selected.
        invalid_choices = [c for c in runtime_event.choices if c.get("category") == "core"]
        ok, message, _ = manager._validate_igcse_selection(sim_state, runtime_event, invalid_choices)
        self.assertFalse(ok)
        self.assertIn("science track", message.lower())

        core = [c for c in runtime_event.choices if c.get("category") == "core"]
        science = [c for c in runtime_event.choices if c.get("category") == "science_track"][:1]
        electives = [c for c in runtime_event.choices if c.get("category") == "elective"][:2]
        valid_choices = core + science + electives
        ok, _, finalized = manager._validate_igcse_selection(sim_state, runtime_event, valid_choices)
        self.assertTrue(ok)
        self.assertEqual(len(finalized), len(valid_choices))

    def test_igcse_resolution_updates_canonical_subject_set(self):
        manager = EventManager(self.config)
        igcse_event = next(e for e in manager.events if e.id == "EVT_IGCSE_SUBJECTS")
        player = self.make_agent(age=14)
        player.school = make_school_payload(self.school_system, stage="Key Stage 4 (IGCSE)", year_label="Year 10", year_index=9)
        sim_state = make_sim_state_stub(player, self.school_system)
        runtime_event = manager._build_igcse_event(igcse_event, sim_state)
        sim_state.pending_event = runtime_event

        core_idx = [i for i, c in enumerate(runtime_event.choices) if c.get("category") == "core"]
        science_idx = [i for i, c in enumerate(runtime_event.choices) if c.get("category") == "science_track"][:1]
        elective_idx = [i for i, c in enumerate(runtime_event.choices) if c.get("category") == "elective"][:2]
        selected_indices = core_idx + science_idx + elective_idx

        manager.apply_resolution(sim_state, runtime_event, selected_indices)

        selected_subjects = [runtime_event.choices[i]["text"] for i in selected_indices]
        self.assertEqual(player.school.get("igcse_subjects"), selected_subjects)
        self.assertEqual(list(player.subjects.keys()), selected_subjects)
        self.assertIn(runtime_event.id, sim_state.event_history)
        self.assertIsNone(sim_state.pending_event)

    def test_apply_academic_delta_keeps_subjects_and_performance_in_sync(self):
        agent = self.make_agent(age=12)
        agent.school = make_school_payload(self.school_system, stage="Key Stage 3", year_label="Year 8", year_index=7)
        self.assertTrue(agent.sync_subjects_with_school(self.school_system, preserve_existing=False))

        baseline = {k: v["current_grade"] for k, v in agent.subjects.items()}
        self.assertTrue(apply_academic_delta(agent, -10))

        self.assertLess(agent.subjects["Mathematics"]["current_grade"], baseline["Mathematics"])
        self.assertIsInstance(agent.school["performance"], int)
        expected_perf = int(sum(v["current_grade"] for v in agent.subjects.values()) / len(agent.subjects))
        self.assertEqual(agent.school["performance"], expected_perf)

    def test_monthly_school_processing_uses_subject_progression_profile(self):
        # This test validates legacy v1 deterministic progression behavior.
        self.school_system.academic_policy["v2_enabled"] = False
        player = self.make_agent(age=15)
        player.school = make_school_payload(self.school_system, stage="Key Stage 4 (IGCSE)", year_label="Year 11", year_index=10)
        player.sync_subjects_with_school(self.school_system, preserve_existing=False, reset_monthly_change=True)
        # Force a known subject state for deterministic check.
        player.subjects = {
            "Mathematics": {
                "current_grade": 50.0,
                "natural_aptitude": 80.0,
                "monthly_change": 0.0,
                "category": "stem",
                "progression_rate": 0.02,
            }
        }
        player.attendance_rate = 1.0
        player._temp_cognitive_penalty = 0.0

        sim_state = make_sim_state_stub(player, self.school_system)
        school_logic.process_school_turn(sim_state)

        self.assertAlmostEqual(player.subjects["Mathematics"]["current_grade"], 50.6, places=6)
        self.assertAlmostEqual(player.subjects["Mathematics"]["monthly_change"], 0.6, places=6)
        self.assertEqual(player.school["performance"], 50)

    def test_year_end_logs_report_card_into_history(self):
        player = self.make_agent(age=14)
        player.school = make_school_payload(self.school_system, stage="Key Stage 4 (IGCSE)", year_label="Year 10", year_index=9)
        player.subjects = {
            "Mathematics": {"current_grade": 88.0, "natural_aptitude": 70.0, "monthly_change": 0.0, "category": "stem", "progression_rate": 0.02},
            "English Language": {"current_grade": 74.0, "natural_aptitude": 68.0, "monthly_change": 0.0, "category": "language", "progression_rate": 0.02},
        }
        player.school["performance"] = 81

        sim_state = make_sim_state_stub(player, self.school_system)
        school_logic._handle_school_end(sim_state, player, self.school_system)

        log_texts = [msg for msg, _ in sim_state._logs]
        self.assertTrue(any("Report Card: Year 10A" in msg for msg in log_texts))
        self.assertTrue(any("Mathematics: 88/100" in msg for msg in log_texts))
        self.assertTrue(any("English Language: 74/100" in msg for msg in log_texts))
        self.assertTrue(any("Overall Performance:" in msg for msg in log_texts))

    def test_british_grade_scale_labels_on_report_card(self):
        player = self.make_agent(age=15)
        player.school = make_school_payload(self.school_system, stage="Key Stage 4 (IGCSE)", year_label="Year 11", year_index=10)
        player.subjects = {
            "Mathematics": {"current_grade": 86.0, "natural_aptitude": 70.0, "monthly_change": 0.0, "category": "stem", "progression_rate": 0.02}
        }
        player.school["performance"] = 86

        sim_state = make_sim_state_stub(player, self.school_system)
        school_logic._handle_school_end(sim_state, player, self.school_system)
        log_texts = [msg for msg, _ in sim_state._logs]

        # 86 maps to GCSE grade 8 in the British 9-1 scale.
        self.assertTrue(any("Mathematics: 86/100 (8)" in msg for msg in log_texts))
        self.assertTrue(any("Overall Performance: 86/100 (8)" in msg for msg in log_texts))


if __name__ == "__main__":
    unittest.main()
