import copy
import json
import math
import random
import statistics
import unittest
from pathlib import Path

from life_sim import constants
from life_sim.simulation.agent import Agent
from life_sim.simulation.events import EventManager
from life_sim.simulation.state import SimState


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


class Phase9InfantTemperamentCohortRealismTests(unittest.TestCase):
    """
    Rigorous infant temperament cohort analysis at:
    - Spawn: 0 months
    - Late infancy: 35 months
    """

    COHORT_SIZE = 1000
    PARENT_POOL_SIZE = 120
    BASE_SEED = 4242

    @classmethod
    def setUpClass(cls):
        cfg = copy.deepcopy(load_config())
        cfg["npc_brain"]["enabled"] = True
        cfg["npc_brain"]["events_enabled"] = True
        cfg["npc_brain"]["infant_brain_v2_enabled"] = True
        cfg["npc_brain"]["infant_event_backfill_enabled"] = True
        cfg["npc_brain"]["infant_brain_v2_debug_logging"] = False

        random.seed(cls.BASE_SEED)
        cls.cfg = cfg
        cls.sim = SimState(cfg)
        cls.manager = EventManager(cfg)
        cls.parent_pool = cls._build_parent_pool()
        cls.birth_rows, cls.age35_rows = cls._sample_paired_cohort()
        cls.report = cls._build_report(cls.birth_rows, cls.age35_rows)

    @classmethod
    def _build_parent_pool(cls):
        pool = []
        for i in range(cls.PARENT_POOL_SIZE):
            father = Agent(
                cls.cfg["agent"],
                is_player=True,
                age=30,
                gender="Male",
                uid=f"phase9-father-{i}",
            )
            mother = Agent(
                cls.cfg["agent"],
                is_player=True,
                age=28,
                gender="Female",
                uid=f"phase9-mother-{i}",
            )
            pool.append((father, mother))
        return pool

    @classmethod
    def _sample_paired_cohort(cls):
        birth_rows = []
        age35_rows = []
        for i in range(cls.COHORT_SIZE):
            father, mother = cls.parent_pool[i % len(cls.parent_pool)]
            infant = Agent(
                cls.cfg["agent"],
                is_player=True,
                age=0,
                parents=(father, mother),
                uid=f"phase9-infant-{i}",
            )
            birth_rows.append(dict(infant.temperament))

            history_store = []

            def infant_callback(agent_ref, age_month_cursor, history=history_store):
                cls.manager.resolve_infant_event_for_agent_at_month(
                    cls.sim,
                    agent_ref,
                    int(age_month_cursor),
                    history_store=history,
                )

            infant.backfill_to_age_months(
                35,
                world_seed=cls.sim.world_seed,
                infant_month_callback=infant_callback,
            )
            age35_rows.append(dict(infant.temperament))
        return birth_rows, age35_rows

    @staticmethod
    def _q(values, q):
        ordered = sorted(values)
        if not ordered:
            return 0.0
        if len(ordered) == 1:
            return float(ordered[0])
        pos = max(0.0, min(1.0, float(q))) * (len(ordered) - 1)
        lo = int(math.floor(pos))
        hi = min(len(ordered) - 1, lo + 1)
        w = pos - lo
        return (ordered[lo] * (1.0 - w)) + (ordered[hi] * w)

    @staticmethod
    def _pearson(xs, ys):
        if len(xs) != len(ys) or not xs:
            return 0.0
        mx = statistics.mean(xs)
        my = statistics.mean(ys)
        vx = sum((x - mx) ** 2 for x in xs)
        vy = sum((y - my) ** 2 for y in ys)
        if vx <= 1e-12 or vy <= 1e-12:
            return 0.0
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        return cov / math.sqrt(vx * vy)

    @classmethod
    def _summarize_trait(cls, rows, trait):
        vals = [float(r[trait]) for r in rows]
        mean_v = statistics.mean(vals)
        sd_v = statistics.pstdev(vals)
        if sd_v > 1e-12:
            centered = [(v - mean_v) / sd_v for v in vals]
            skew = statistics.mean(z ** 3 for z in centered)
            kurt = statistics.mean(z ** 4 for z in centered) - 3.0
            tail_low = sum(1 for z in centered if z <= -2.0) / len(centered)
            tail_high = sum(1 for z in centered if z >= 2.0) / len(centered)
        else:
            skew = 0.0
            kurt = 0.0
            tail_low = 0.0
            tail_high = 0.0

        return {
            "mean": mean_v,
            "sd": sd_v,
            "p01": cls._q(vals, 0.01),
            "p05": cls._q(vals, 0.05),
            "p50": cls._q(vals, 0.50),
            "p95": cls._q(vals, 0.95),
            "p99": cls._q(vals, 0.99),
            "min": min(vals),
            "max": max(vals),
            "skew": skew,
            "kurtosis_excess": kurt,
            "tail_low_2sigma": tail_low,
            "tail_high_2sigma": tail_high,
        }

    @classmethod
    def _within_agent_summary(cls, rows):
        profile_sds = []
        profile_spans = []
        contradiction_count = 0
        self_regulation = []
        emotional_reactivity = []

        for row in rows:
            profile = [float(row[t]) for t in constants.TEMPERAMENT_TRAITS]
            profile_sds.append(statistics.pstdev(profile))
            profile_spans.append(max(profile) - min(profile))

            contradictions = 0
            if row["Regularity"] >= 70 and row["Distractibility"] >= 70:
                contradictions += 1
            if row["Persistence"] >= 70 and row["Distractibility"] >= 70:
                contradictions += 1
            if row["Adaptability"] >= 75 and row["Approach_Withdrawal"] <= 25:
                contradictions += 1
            if row["Mood"] >= 75 and row["Threshold"] <= 25:
                contradictions += 1
            if contradictions > 0:
                contradiction_count += 1

            self_regulation.append(
                (
                    float(row["Regularity"])
                    + float(row["Persistence"])
                    + (100.0 - float(row["Distractibility"]))
                )
                / 3.0
            )
            emotional_reactivity.append(
                (float(row["Intensity"]) + (100.0 - float(row["Threshold"]))) / 2.0
            )

        return {
            "profile_sd_mean": statistics.mean(profile_sds),
            "profile_sd_p95": cls._q(profile_sds, 0.95),
            "profile_span_mean": statistics.mean(profile_spans),
            "profile_span_p95": cls._q(profile_spans, 0.95),
            "contradiction_rate": contradiction_count / len(rows),
            "self_reg_vs_reactivity_corr": cls._pearson(self_regulation, emotional_reactivity),
        }

    @classmethod
    def _build_report(cls, birth_rows, age35_rows):
        birth_trait = {
            t: cls._summarize_trait(birth_rows, t) for t in constants.TEMPERAMENT_TRAITS
        }
        age35_trait = {
            t: cls._summarize_trait(age35_rows, t) for t in constants.TEMPERAMENT_TRAITS
        }

        paired_delta = {}
        for t in constants.TEMPERAMENT_TRAITS:
            deltas = [
                float(age35_rows[i][t]) - float(birth_rows[i][t])
                for i in range(len(birth_rows))
            ]
            paired_delta[t] = {
                "mean_delta": statistics.mean(deltas),
                "sd_delta": statistics.pstdev(deltas),
                "pct_increase": sum(1 for d in deltas if d > 0.0) / len(deltas),
            }

        expected_pairs = [
            ("Regularity", "Distractibility"),
            ("Regularity", "Persistence"),
            ("Mood", "Threshold"),
            ("Approach_Withdrawal", "Adaptability"),
        ]
        pair_corr_birth = {}
        pair_corr_age35 = {}
        for a, b in expected_pairs:
            pair_corr_birth[f"{a}__{b}"] = cls._pearson(
                [row[a] for row in birth_rows], [row[b] for row in birth_rows]
            )
            pair_corr_age35[f"{a}__{b}"] = cls._pearson(
                [row[a] for row in age35_rows], [row[b] for row in age35_rows]
            )

        return {
            "sample_sizes": {"birth": len(birth_rows), "age_35m": len(age35_rows)},
            "trait_birth": birth_trait,
            "trait_35m": age35_trait,
            "within_birth": cls._within_agent_summary(birth_rows),
            "within_35m": cls._within_agent_summary(age35_rows),
            "pair_corr_birth": pair_corr_birth,
            "pair_corr_35m": pair_corr_age35,
            "paired_delta": paired_delta,
            "mean_abs_delta_all_traits": statistics.mean(
                abs(v["mean_delta"]) for v in paired_delta.values()
            ),
        }

    def _report_json(self):
        return json.dumps(self.report, indent=2, sort_keys=True)

    def test_distribution_and_outlier_coverage_is_realistic(self):
        report = self.report
        for trait in constants.TEMPERAMENT_TRAITS:
            b = report["trait_birth"][trait]
            m35 = report["trait_35m"][trait]

            self.assertGreaterEqual(
                b["mean"],
                42.0,
                f"Birth cohort mean too low for {trait}\n{self._report_json()}",
            )
            self.assertLessEqual(
                b["mean"],
                58.0,
                f"Birth cohort mean too high for {trait}\n{self._report_json()}",
            )
            self.assertGreaterEqual(
                b["sd"],
                5.0,
                f"Birth cohort variance too narrow for {trait}\n{self._report_json()}",
            )
            self.assertLessEqual(
                b["sd"],
                16.0,
                f"Birth cohort variance too wide for {trait}\n{self._report_json()}",
            )

            self.assertGreaterEqual(
                m35["mean"],
                35.0,
                f"35-month cohort mean too low for {trait}\n{self._report_json()}",
            )
            self.assertLessEqual(
                m35["mean"],
                75.0,
                f"35-month cohort mean too high for {trait}\n{self._report_json()}",
            )
            self.assertGreaterEqual(
                m35["sd"],
                6.0,
                f"35-month cohort variance too narrow for {trait}\n{self._report_json()}",
            )
            self.assertLessEqual(
                m35["sd"],
                18.0,
                f"35-month cohort variance too wide for {trait}\n{self._report_json()}",
            )

            birth_tail = b["tail_low_2sigma"] + b["tail_high_2sigma"]
            month35_tail = m35["tail_low_2sigma"] + m35["tail_high_2sigma"]
            self.assertGreaterEqual(
                birth_tail,
                0.02,
                f"Birth tails too thin for {trait}\n{self._report_json()}",
            )
            self.assertLessEqual(
                birth_tail,
                0.09,
                f"Birth tails too heavy for {trait}\n{self._report_json()}",
            )
            self.assertGreaterEqual(
                month35_tail,
                0.02,
                f"35-month tails too thin for {trait}\n{self._report_json()}",
            )
            self.assertLessEqual(
                month35_tail,
                0.09,
                f"35-month tails too heavy for {trait}\n{self._report_json()}",
            )

            self.assertLessEqual(
                abs(b["skew"]),
                1.0,
                f"Birth skew too extreme for {trait}\n{self._report_json()}",
            )
            self.assertLessEqual(
                abs(m35["skew"]),
                1.0,
                f"35-month skew too extreme for {trait}\n{self._report_json()}",
            )

        any_extreme_high = any(
            report["trait_35m"][t]["p99"] >= 70.0 for t in constants.TEMPERAMENT_TRAITS
        )
        any_extreme_low = any(
            report["trait_35m"][t]["p01"] <= 32.0 for t in constants.TEMPERAMENT_TRAITS
        )
        self.assertTrue(
            any_extreme_high,
            f"Expected at least one high-end outlier trait by 35 months\n{self._report_json()}",
        )
        self.assertTrue(
            any_extreme_low,
            f"Expected at least one low-end outlier trait by 35 months\n{self._report_json()}",
        )

    def test_within_agent_profile_coherence_and_developmental_drift(self):
        report = self.report
        wb = report["within_birth"]
        w35 = report["within_35m"]

        self.assertGreaterEqual(
            wb["profile_sd_mean"],
            6.0,
            f"Birth within-agent profiles too flat\n{self._report_json()}",
        )
        self.assertLessEqual(
            wb["profile_sd_mean"],
            11.0,
            f"Birth within-agent profiles too fragmented\n{self._report_json()}",
        )
        self.assertGreaterEqual(
            w35["profile_sd_mean"],
            7.0,
            f"35-month within-agent profiles too flat\n{self._report_json()}",
        )
        self.assertLessEqual(
            w35["profile_sd_mean"],
            14.0,
            f"35-month within-agent profiles too fragmented\n{self._report_json()}",
        )

        self.assertGreaterEqual(
            wb["profile_span_mean"],
            18.0,
            f"Birth trait span too narrow\n{self._report_json()}",
        )
        self.assertLessEqual(
            wb["profile_span_mean"],
            35.0,
            f"Birth trait span too wide\n{self._report_json()}",
        )
        self.assertGreaterEqual(
            w35["profile_span_mean"],
            22.0,
            f"35-month trait span too narrow\n{self._report_json()}",
        )
        self.assertLessEqual(
            w35["profile_span_mean"],
            45.0,
            f"35-month trait span too wide\n{self._report_json()}",
        )

        self.assertLessEqual(
            wb["contradiction_rate"],
            0.02,
            f"Birth cohort has too many contradictory profiles\n{self._report_json()}",
        )
        self.assertLessEqual(
            w35["contradiction_rate"],
            0.02,
            f"35-month cohort has too many contradictory profiles\n{self._report_json()}",
        )

        self.assertLessEqual(
            wb["self_reg_vs_reactivity_corr"],
            -0.05,
            f"Birth self-regulation/reactivity relationship is not realistic\n{self._report_json()}",
        )
        self.assertLessEqual(
            w35["self_reg_vs_reactivity_corr"],
            -0.05,
            f"35-month self-regulation/reactivity relationship is not realistic\n{self._report_json()}",
        )

        c0 = report["pair_corr_birth"]
        c35 = report["pair_corr_35m"]
        self.assertLessEqual(
            c0["Regularity__Distractibility"],
            -0.20,
            f"Birth Regularity vs Distractibility should be clearly negative\n{self._report_json()}",
        )
        self.assertGreaterEqual(
            c0["Regularity__Persistence"],
            0.10,
            f"Birth Regularity vs Persistence should be positive\n{self._report_json()}",
        )
        self.assertGreaterEqual(
            c0["Mood__Threshold"],
            0.20,
            f"Birth Mood vs Threshold should be positive\n{self._report_json()}",
        )
        self.assertGreaterEqual(
            c0["Approach_Withdrawal__Adaptability"],
            -0.05,
            f"Birth Approach_Withdrawal vs Adaptability should not invert strongly negative\n{self._report_json()}",
        )

        self.assertLessEqual(
            c35["Regularity__Distractibility"],
            -0.08,
            f"35-month Regularity vs Distractibility should stay negative\n{self._report_json()}",
        )
        self.assertGreaterEqual(
            c35["Regularity__Persistence"],
            0.03,
            f"35-month Regularity vs Persistence should remain positive\n{self._report_json()}",
        )
        self.assertGreaterEqual(
            c35["Mood__Threshold"],
            0.08,
            f"35-month Mood vs Threshold should remain positive\n{self._report_json()}",
        )
        self.assertGreaterEqual(
            c35["Approach_Withdrawal__Adaptability"],
            -0.05,
            f"35-month Approach_Withdrawal vs Adaptability should not invert strongly negative\n{self._report_json()}",
        )

        self.assertGreaterEqual(
            report["mean_abs_delta_all_traits"],
            2.5,
            f"Temperament drift from birth to 35 months is too weak\n{self._report_json()}",
        )
        self.assertLessEqual(
            report["mean_abs_delta_all_traits"],
            20.0,
            f"Temperament drift from birth to 35 months is too strong\n{self._report_json()}",
        )

        for trait in constants.TEMPERAMENT_TRAITS:
            d = report["paired_delta"][trait]
            self.assertGreaterEqual(
                d["sd_delta"],
                4.0,
                f"Change variance too narrow for {trait}\n{self._report_json()}",
            )


if __name__ == "__main__":
    unittest.main()
