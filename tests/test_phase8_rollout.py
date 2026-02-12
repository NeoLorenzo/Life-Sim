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

from life_sim.simulation import logic
from life_sim.simulation.events import EventManager
from life_sim.simulation.state import SimState


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def run_rollout_snapshot(seed=8088, months=36):
    cfg = load_config()
    cfg = copy.deepcopy(cfg)
    cfg["seed"] = seed
    cfg["npc_brain"]["enabled"] = True
    cfg["npc_brain"]["events_enabled"] = True
    cfg["npc_brain"]["ap_enabled"] = True
    cfg["npc_brain"]["player_mimic_enabled"] = True
    cfg["npc_brain"]["debug_logging"] = False

    random.seed(seed)
    np.random.seed(seed)
    sim = SimState(cfg)
    manager = EventManager(cfg)

    turn_times = []
    for _ in range(months):
        t0 = time.perf_counter()
        logic.process_turn(sim)
        manager.auto_resolve_npc_events(sim)
        if sim.player.is_alive and not cfg.get("development", {}).get("disable_events", False):
            event = manager.evaluate_month(sim)
            if event:
                sim.pending_event = event
                with redirect_stdout(io.StringIO()):
                    manager.apply_resolution(sim, event, [0])
        turn_times.append((time.perf_counter() - t0) * 1000.0)

    npc_hist_counts = [len(v) for k, v in (sim.agent_event_history or {}).items() if k != sim.player.uid]
    npc_hist_total = sum(npc_hist_counts)
    npc_hist_mean = (statistics.mean(npc_hist_counts) if npc_hist_counts else 0.0)

    return {
        "seed": seed,
        "months": months,
        "world_seed": sim.world_seed,
        "player_age_months": sim.player.age_months,
        "player_health": round(float(sim.player.health), 4),
        "player_happiness": round(float(sim.player.happiness), 4),
        "player_event_history_count": len(sim.event_history),
        "player_style_observations": int((sim.player_style_tracker or {}).get("observations", 0)),
        "npc_count": len(sim.npcs),
        "npc_event_history_total": int(npc_hist_total),
        "npc_event_history_mean": round(float(npc_hist_mean), 6),
        "turn_time_ms": {
            "mean": round(float(statistics.mean(turn_times)), 6),
            "p95": round(float(sorted(turn_times)[int(0.95 * (len(turn_times) - 1))]), 6),
            "max": round(float(max(turn_times)), 6),
        },
    }


class Phase8RolloutTests(unittest.TestCase):
    def test_rollout_reproducibility_same_seed(self):
        s1 = run_rollout_snapshot(seed=8181, months=24)
        s2 = run_rollout_snapshot(seed=8181, months=24)
        # Timing differs by machine jitter; compare functional fields only.
        s1f = dict(s1)
        s2f = dict(s2)
        s1f.pop("turn_time_ms", None)
        s2f.pop("turn_time_ms", None)
        self.assertEqual(s1f, s2f)

    def test_rollout_turn_time_is_recorded(self):
        snap = run_rollout_snapshot(seed=8282, months=24)
        perf = snap["turn_time_ms"]
        self.assertGreater(perf["mean"], 0.0)
        self.assertGreater(perf["p95"], 0.0)
        self.assertGreaterEqual(perf["max"], perf["p95"])
        self.assertLess(perf["max"], 60000.0)

    def test_rollout_generates_npc_event_histories(self):
        snap = run_rollout_snapshot(seed=8383, months=24)
        self.assertGreaterEqual(snap["npc_count"], 1)
        self.assertGreaterEqual(snap["npc_event_history_total"], 1)
        self.assertGreaterEqual(snap["player_style_observations"], 1)


if __name__ == "__main__":
    unittest.main()
