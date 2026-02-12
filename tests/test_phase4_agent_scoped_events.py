import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from life_sim.simulation.events import EventManager
from life_sim.simulation.school import School
from life_sim.simulation.state import Agent


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


class Phase4AgentScopedEventsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.manager = EventManager(cls.config)
        cls.school_system = School(cls.config["education"])

    def _make_agent(self, age=1, is_player=False):
        return Agent(
            self.config["agent"],
            is_player=is_player,
            age=age,
            time_config=self.config.get("time_management", {}),
        )

    def test_once_per_lifetime_is_isolated_per_agent(self):
        a1 = self._make_agent(age=1, is_player=False)
        a2 = self._make_agent(age=1, is_player=False)
        a1.age_months = 19
        a2.age_months = 19
        sim_state = SimpleNamespace(
            school_system=self.school_system,
            event_history=[],
            pending_event=None,
            agent_event_history={a1.uid: [], a2.uid: []},
        )

        e1 = self.manager.evaluate_month_for_agent(sim_state, a1)
        e2 = self.manager.evaluate_month_for_agent(sim_state, a2)
        self.assertIsNotNone(e1)
        self.assertIsNotNone(e2)
        self.assertEqual(e1.id, e2.id)

        # Mark first agent's event as completed; second should remain eligible.
        sim_state.agent_event_history[a1.uid].append(e1.id)
        blocked = self.manager.evaluate_month_for_agent(sim_state, a1)
        open_for_a2 = self.manager.evaluate_month_for_agent(sim_state, a2)
        self.assertIsNone(blocked)
        self.assertIsNotNone(open_for_a2)

    def test_apply_resolution_targets_passed_agent_not_player(self):
        player = self._make_agent(age=1, is_player=True)
        npc = self._make_agent(age=1, is_player=False)
        event = next(e for e in self.manager.events if e.id == "EVT_INFANT_NEW_FOOD_01")

        tracker = {"count": 0}
        sim_state = SimpleNamespace(
            player=player,
            school_system=self.school_system,
            event_history=[],
            pending_event="active",
            agent_event_history={player.uid: [], npc.uid: []},
            add_log=lambda message, color=None: None,
            _update_player_style_tracker=lambda features: tracker.__setitem__("count", tracker["count"] + 1),
        )

        before_player = dict(player.temperament)
        before_npc = dict(npc.temperament)

        self.manager.apply_resolution_to_agent(sim_state, npc, event, [0])

        self.assertNotEqual(before_npc, npc.temperament)
        self.assertEqual(before_player, player.temperament)
        self.assertIn(event.id, sim_state.agent_event_history[npc.uid])
        # NPC resolutions should not clear player modal state.
        self.assertEqual(sim_state.pending_event, "active")
        # Player style tracker should only update for player events.
        self.assertEqual(tracker["count"], 0)

    def test_player_wrapper_keeps_backward_compatibility(self):
        player = self._make_agent(age=1, is_player=True)
        event = next(e for e in self.manager.events if e.id == "EVT_INFANT_NEW_FOOD_01")
        sim_state = SimpleNamespace(
            player=player,
            school_system=self.school_system,
            event_history=[],
            pending_event=event,
            add_log=lambda message, color=None: None,
        )

        self.manager.apply_resolution(sim_state, event, [0])
        self.assertIn(event.id, sim_state.event_history)
        self.assertIsNone(sim_state.pending_event)


if __name__ == "__main__":
    unittest.main()
