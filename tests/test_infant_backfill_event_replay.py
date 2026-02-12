import copy
import json
import random
import unittest
from pathlib import Path

from life_sim.simulation.state import SimState


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


class InfantBackfillEventReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = load_config()

    def _make_config(self, enabled):
        cfg = copy.deepcopy(self.base_config)
        cfg["npc_brain"]["enabled"] = bool(enabled)
        cfg["npc_brain"]["events_enabled"] = bool(enabled)
        cfg["npc_brain"]["infant_event_backfill_enabled"] = bool(enabled)
        cfg["npc_brain"]["infant_event_backfill_debug_logging"] = False
        return cfg

    def test_npc_backfill_replays_infant_events_when_enabled(self):
        cfg = self._make_config(enabled=True)
        sim = SimState(cfg)

        npc = sim._create_npc(age=8, first_name="Replay", last_name="Enabled")
        history = sim.agent_event_history.get(npc.uid, [])

        self.assertGreater(len(history), 0)
        infant_events = [evt for evt in history if str(evt).startswith("EVT_INFANT_")]
        self.assertEqual(len(history), len(infant_events))
        self.assertIn("EVT_INFANT_NEW_FOOD_01", history)
        self.assertIn("EVT_INFANT_PUZZLE_GATE_35", history)

    def test_npc_backfill_infant_replay_is_deterministic(self):
        cfg = self._make_config(enabled=True)

        random.seed(19731)
        sim1 = SimState(copy.deepcopy(cfg))
        random.seed(19731)
        sim2 = SimState(copy.deepcopy(cfg))

        random.seed(92754)
        npc1 = sim1._create_npc(age=8, first_name="Det", last_name="NPC")
        random.seed(92754)
        npc2 = sim2._create_npc(age=8, first_name="Det", last_name="NPC")

        self.assertEqual(sim1.agent_event_history[npc1.uid], sim2.agent_event_history[npc2.uid])
        self.assertEqual(npc1.personality, npc2.personality)

    def test_npc_backfill_replay_disabled_keeps_event_history_empty(self):
        cfg = self._make_config(enabled=False)
        sim = SimState(cfg)

        npc = sim._create_npc(age=8, first_name="Replay", last_name="Disabled")
        history = sim.agent_event_history.get(npc.uid, [])

        self.assertEqual(history, [])


if __name__ == "__main__":
    unittest.main()
