import copy
import io
import json
import random
import statistics
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np

from life_sim import constants
from life_sim.simulation import logic
from life_sim.simulation.events import EventManager
from life_sim.simulation.state import SimState


ROOT = Path(__file__).resolve().parents[1]
BASELINE_FILE = ROOT / "tests" / "baselines" / "phase0_npc_brain_snapshot.json"
HARNESS_SEED = 20260212
MONTHS_TO_SIMULATE = 48


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def all_agents(sim_state):
    yield sim_state.player
    for npc in sim_state.npcs.values():
        yield npc


def mean_temperament_variance(sim_state):
    infants = [a for a in all_agents(sim_state) if a.is_alive and isinstance(a.temperament, dict)]
    if len(infants) < 2:
        return 0.0

    trait_variances = []
    for trait_name in constants.TEMPERAMENT_TRAITS:
        vals = [float(a.temperament.get(trait_name, constants.TEMPERAMENT_DEFAULT_VALUE)) for a in infants]
        if len(vals) >= 2:
            trait_variances.append(statistics.pvariance(vals))
    if not trait_variances:
        return 0.0
    return round(float(statistics.mean(trait_variances)), 6)


def choose_indices_for_event(event):
    if not event.choices:
        return []

    if event.id == "EVT_IGCSE_SUBJECTS":
        min_total = int((event.ui_config or {}).get("min_selections", 1))
        core = []
        science = []
        electives = []
        for idx, choice in enumerate(event.choices):
            category = choice.get("category")
            if category == "core":
                core.append(idx)
            elif category == "science_track":
                science.append(idx)
            elif category == "elective":
                electives.append(idx)

        selected = list(core)
        if science:
            selected.append(science[0])
        mandatory_count = len(selected)
        electives_needed = max(0, min_total - mandatory_count)
        selected.extend(electives[:electives_needed])
        return selected

    if event.ui_type == "multi_select":
        min_selections = int((event.ui_config or {}).get("min_selections", 1))
        return list(range(min(min_selections, len(event.choices))))

    return [0]


def generate_phase0_npc_brain_snapshot(config):
    cfg = copy.deepcopy(config)
    cfg["seed"] = HARNESS_SEED

    random.seed(HARNESS_SEED)
    np.random.seed(HARNESS_SEED)

    sim_state = SimState(cfg)
    event_manager = EventManager(cfg)

    event_resolutions_total = 0
    temperament_variance_at_36m = None
    turn_times_ms = []
    monthly_snapshots = []

    for month_step in range(MONTHS_TO_SIMULATE):
        t0 = time.perf_counter()
        logic.process_turn(sim_state)

        triggered_event_id = None
        if sim_state.player.is_alive and not cfg.get("development", {}).get("disable_events", False):
            event = event_manager.evaluate_month(sim_state)
            if event:
                triggered_event_id = event.id
                sim_state.pending_event = event
                selected_indices = choose_indices_for_event(event)
                with redirect_stdout(io.StringIO()):
                    event_manager.apply_resolution(sim_state, event, selected_indices)
                event_resolutions_total += 1

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        turn_times_ms.append(elapsed_ms)

        if month_step == 35:
            temperament_variance_at_36m = mean_temperament_variance(sim_state)

        monthly_snapshots.append(
            {
                "step": month_step + 1,
                "year": int(sim_state.year),
                "month_index": int(sim_state.month_index),
                "player_age_months": int(sim_state.player.age_months),
                "player_age_years": int(sim_state.player.age),
                "player_health": float(sim_state.player.health),
                "player_happiness": float(sim_state.player.happiness),
                "npc_count": int(len(sim_state.npcs)),
                "event_triggered": triggered_event_id,
                "event_resolutions_total": int(event_resolutions_total),
            }
        )

    if temperament_variance_at_36m is None:
        temperament_variance_at_36m = mean_temperament_variance(sim_state)

    sorted_turn_times = sorted(turn_times_ms)
    p95_idx = int(0.95 * (len(sorted_turn_times) - 1))
    perf_metrics = {
        "mean": round(float(statistics.mean(turn_times_ms)), 6),
        "p95": round(float(sorted_turn_times[p95_idx]), 6),
        "max": round(float(max(turn_times_ms)), 6),
    }

    return {
        "harness_seed": HARNESS_SEED,
        "months_simulated": MONTHS_TO_SIMULATE,
        "metrics": {
            "mean_temperament_variance_at_36m": temperament_variance_at_36m,
            "event_resolutions_total": int(event_resolutions_total),
            "monthly_turn_time_ms": perf_metrics,
        },
        "monthly_snapshots": monthly_snapshots,
    }


def strip_perf_metrics(snapshot):
    data = copy.deepcopy(snapshot)
    data["metrics"].pop("monthly_turn_time_ms", None)
    return data


class Phase0NpcBrainBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def test_npc_brain_phase0_flags_exist_and_default_off(self):
        npc_brain_cfg = self.config.get("npc_brain")
        self.assertIsInstance(npc_brain_cfg, dict)
        self.assertFalse(bool(npc_brain_cfg.get("enabled", True)))
        self.assertFalse(bool(npc_brain_cfg.get("events_enabled", True)))
        self.assertFalse(bool(npc_brain_cfg.get("ap_enabled", True)))
        self.assertFalse(bool(npc_brain_cfg.get("player_mimic_enabled", True)))
        self.assertFalse(bool(npc_brain_cfg.get("debug_logging", True)))

    def test_phase0_npc_brain_snapshot_matches_baseline(self):
        with open(BASELINE_FILE, "r", encoding="utf-8") as f:
            expected = json.load(f)
        current = generate_phase0_npc_brain_snapshot(self.config)
        self.assertEqual(strip_perf_metrics(current), strip_perf_metrics(expected))

    def test_phase0_npc_brain_turn_time_metrics_are_recorded(self):
        snapshot = generate_phase0_npc_brain_snapshot(self.config)
        perf = snapshot["metrics"]["monthly_turn_time_ms"]
        self.assertGreater(perf["mean"], 0.0)
        self.assertGreater(perf["p95"], 0.0)
        self.assertGreaterEqual(perf["max"], perf["mean"])
        self.assertGreaterEqual(perf["max"], perf["p95"])
        # Guardrail only; exact timing is machine-dependent.
        self.assertLess(perf["max"], 60000.0)


if __name__ == "__main__":
    unittest.main()
