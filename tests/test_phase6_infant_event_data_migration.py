import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Phase6InfantEventDataMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / "events.json", "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_all_infant_choices_have_infant_appraisal(self):
        definitions = self.data.get("definitions", [])
        infant_events = [e for e in definitions if str(e.get("id", "")).startswith("EVT_INFANT_")]
        self.assertGreater(len(infant_events), 0)

        missing = []
        for event in infant_events:
            for i, choice in enumerate(event.get("choices", []) or []):
                effects = choice.get("effects", {}) or {}
                if not isinstance(effects.get("infant_appraisal"), dict):
                    missing.append((event.get("id"), i))
        self.assertEqual(missing, [])

    def test_infant_appraisal_values_are_bounded_and_complete(self):
        required = {
            "comfort_value",
            "energy_cost",
            "safety_risk",
            "novelty_load",
            "familiarity",
            "social_soothing",
        }
        definitions = self.data.get("definitions", [])
        for event in definitions:
            if not str(event.get("id", "")).startswith("EVT_INFANT_"):
                continue
            for choice in event.get("choices", []) or []:
                appraisal = (choice.get("effects", {}) or {}).get("infant_appraisal", {}) or {}
                self.assertEqual(set(appraisal.keys()), required)
                for key, value in appraisal.items():
                    self.assertGreaterEqual(float(value), 0.0, msg=f"{event.get('id')}:{key}")
                    self.assertLessEqual(float(value), 1.0, msg=f"{event.get('id')}:{key}")

    def test_migration_preserves_temperament_effects(self):
        definitions = self.data.get("definitions", [])
        with_temp = 0
        for event in definitions:
            if not str(event.get("id", "")).startswith("EVT_INFANT_"):
                continue
            for choice in event.get("choices", []) or []:
                temperament = (choice.get("effects", {}) or {}).get("temperament")
                self.assertIsInstance(temperament, dict)
                self.assertGreater(len(temperament), 0)
                with_temp += 1
        self.assertGreater(with_temp, 0)


if __name__ == "__main__":
    unittest.main()
