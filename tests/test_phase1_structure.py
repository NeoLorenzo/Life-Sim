import json
import random
import unittest
from pathlib import Path

from life_sim.simulation.school import School
from life_sim.simulation.state import Agent, SimState


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


class Phase1StructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.agent_conf = cls.config["agent"]
        cls.time_conf = cls.config.get("time_management", {})

    def make_agent(self, age=14, is_player=False):
        return Agent(self.agent_conf, is_player=is_player, age=age, time_config=self.time_conf)

    def test_assign_form_uses_configured_label_cycle(self):
        sim = SimState.__new__(SimState)
        school_system = School(self.config["education"])
        school_system.form_labels = ["Red", "Blue", "Green"]
        sim.school_system = school_system

        self.assertEqual(sim._assign_form_to_student(None, 0), "Red")
        self.assertEqual(sim._assign_form_to_student(None, 1), "Blue")
        self.assertEqual(sim._assign_form_to_student(None, 2), "Green")
        self.assertEqual(sim._assign_form_to_student(None, 3), "Red")

    def test_populate_classmates_uses_configured_capacity_and_form_labels(self):
        random.seed(2026)
        school_system = School(self.config["education"])
        school_system.forms_per_year = 3
        school_system.students_per_form = 2
        school_system.form_labels = ["L1", "L2", "L3"]

        player = self.make_agent(age=14, is_player=True)
        player.school = make_school_payload(
            school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.sync_subjects_with_school(school_system, preserve_existing=True)

        sim = SimState.__new__(SimState)
        sim.school_system = school_system
        sim.player = player
        sim.npcs = {}
        sim._link_agents = lambda *args, **kwargs: None

        generated = []

        def stub_generate_lineage_structure(*args, **kwargs):
            classmate = self.make_agent(age=player.age, is_player=False)
            generated.append(classmate)
            return classmate

        sim._generate_lineage_structure = stub_generate_lineage_structure
        sim.populate_classmates()

        self.assertEqual(len(generated), 5)  # 3 forms * 2 students = 6 total - player
        assigned_forms = [player.form] + [npc.form for npc in generated]
        self.assertEqual(assigned_forms, ["L1", "L2", "L3", "L1", "L2", "L3"])

    def test_random_form_label_draws_from_configured_labels(self):
        random.seed(77)
        school_system = School(self.config["education"])
        school_system.form_labels = ["X", "Y"]

        draws = [school_system.get_random_form_label() for _ in range(20)]
        self.assertTrue(all(label in {"X", "Y"} for label in draws))
        self.assertTrue({"X", "Y"}.issubset(set(draws)))

    def test_populate_classmates_does_not_grow_cohort_after_year_change(self):
        random.seed(3030)
        school_system = School(self.config["education"])
        school_system.forms_per_year = 2
        school_system.students_per_form = 3  # total cohort size = 6 (player + 5 classmates)
        school_system.form_labels = ["F1", "F2"]

        player = self.make_agent(age=14, is_player=True)
        player.school = make_school_payload(
            school_system,
            stage="Key Stage 4 (IGCSE)",
            year_label="Year 10",
            year_index=9,
        )
        player.sync_subjects_with_school(school_system, preserve_existing=True)

        sim = SimState.__new__(SimState)
        sim.school_system = school_system
        sim.player = player
        sim.npcs = {}
        sim._link_agents = lambda *args, **kwargs: None

        generated = []

        def stub_generate_lineage_structure(*args, **kwargs):
            classmate = self.make_agent(age=player.age, is_player=False)
            generated.append(classmate)
            sim.npcs[classmate.uid] = classmate
            return classmate

        sim._generate_lineage_structure = stub_generate_lineage_structure
        sim.populate_classmates()
        first_gen_count = len(generated)
        self.assertEqual(first_gen_count, 5)
        self.assertEqual(len(player.school.get("cohort_member_uids", [])), 5)

        # Advance player to next year and repopulate. Cohort should be reused, not expanded.
        player.school["year_index"] = 10
        player.school["year_label"] = "Year 11"
        player.school["stage"] = "Key Stage 4 (IGCSE)"
        sim.populate_classmates()

        self.assertEqual(len(generated), first_gen_count)
        self.assertEqual(len(player.school.get("cohort_member_uids", [])), 5)
        self.assertTrue(all(npc.school["year_index"] == 10 for npc in generated))


if __name__ == "__main__":
    unittest.main()
