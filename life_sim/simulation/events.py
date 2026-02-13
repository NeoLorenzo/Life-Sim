# life_sim/simulation/events.py
"""
Event Management Module.
Handles event evaluation, triggering, and resolution for the simulation.
"""
import logging
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .. import constants
from . import school as school_logic
from .brain import event_choice_to_features
from .brain import (
    NPCBrain,
    InfantBrain,
    make_decision_rng,
    choice_to_infant_appraisal,
    temperament_to_infant_params,
)

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """
    Represents a single game event with its configuration and metadata.
    """
    id: str
    title: str
    description: str
    trigger: Dict[str, Any]  # Contains min/max age in years or months.
    ui_type: str  # single_select, multi_select, etc.
    choices: List[Dict[str, Any]]  # List of choice dictionaries with text and effects
    once_per_lifetime: bool = False  # Whether event can only trigger once per game
    ui_config: Dict[str, Any] = None  # UI configuration like min/max selections
    npc_auto: bool = True  # Whether NPC auto-resolver is allowed to process this event
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'Event':
        """
        Create an Event instance from configuration dictionary.
        
        Args:
            config: Event configuration dictionary.
            
        Returns:
            Event instance.
        """
        return cls(
            id=config["id"],
            title=config["title"],
            description=config["description"],
            trigger=config["trigger"],
            ui_type=config["ui_type"],
            choices=config["choices"],
            once_per_lifetime=config.get("once_per_lifetime", False),
            ui_config=config.get("ui_config", {}),
            npc_auto=config.get("npc_auto", True),
        )

class EventManager:
    """
    Manages the lifecycle of game events including evaluation, triggering, and resolution.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the EventManager with configuration data.
        
        Args:
            config (dict): The loaded configuration dictionary (for development settings only).
        """
        self.config = config
        
        # Load events from separate events.json file
        events_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "events.json"))
        try:
            with open(events_file_path, 'r', encoding='utf-8') as f:
                events_data = json.load(f)
                raw_definitions = events_data.get("definitions", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load events from {events_file_path}: {e}")
            raw_definitions = []
        
        # Parse raw config into Event objects
        self.events: List[Event] = []
        for event_config in raw_definitions:
            try:
                event = Event.from_config(event_config)
                self.events.append(event)
            except (KeyError, TypeError) as e:
                logger.warning(f"Failed to parse event config: {event_config}. Error: {e}")
        
        logger.info(f"EventManager initialized with {len(self.events)} parsed event definitions")

    def _build_igcse_event(self, event: Event, sim_state) -> Event:
        """
        Builds a runtime IGCSE event using school curriculum config as source of truth.
        """
        school_sys = getattr(sim_state, "school_system", None)
        if not school_sys:
            return event

        igcse_cfg = school_sys.get_igcse_subject_options()
        core_subjects = list(igcse_cfg.get("core_subjects", []))
        elective_pool = list(igcse_cfg.get("elective_pool", []))
        science_tracks = list(igcse_cfg.get("science_tracks", []))

        # Reuse effects from any existing configured choices when labels match.
        existing_effects = {}
        for choice in event.choices:
            if isinstance(choice, dict):
                text = choice.get("text")
                if text:
                    existing_effects[text] = choice.get("effects", {})

        choices = []

        # Science is modeled as an explicit track selection in IGCSE.
        science_core_terms = ("science", "sciences")
        non_science_core = [
            s for s in core_subjects
            if not any(term in s.lower() for term in science_core_terms)
        ]

        for subject in non_science_core:
            choices.append({
                "text": subject,
                "effects": existing_effects.get(subject, {"stats": {"happiness": -1}}),
                "category": "core"
            })

        for track in science_tracks:
            choices.append({
                "text": track,
                "effects": existing_effects.get(track, {"stats": {"happiness": -2}}),
                "category": "science_track"
            })

        for subject in elective_pool:
            choices.append({
                "text": subject,
                "effects": existing_effects.get(subject, {"stats": {"happiness": 0}}),
                "category": "elective"
            })

        if not choices:
            return event

        return Event(
            id=event.id,
            title=event.title,
            description=event.description,
            trigger=event.trigger,
            ui_type=event.ui_type,
            choices=choices,
            once_per_lifetime=event.once_per_lifetime,
            ui_config=event.ui_config or {},
            npc_auto=getattr(event, "npc_auto", True),
        )

    def _validate_igcse_selection(self, sim_state, event: Event, selected_choices: List[Dict[str, Any]]):
        """
        Enforces core inclusion, elective min/max, and science-track consistency.
        Returns (is_valid, error_message, finalized_subject_list).
        """
        school_sys = getattr(sim_state, "school_system", None)
        if not school_sys:
            return False, "School system unavailable for IGCSE validation.", []

        igcse_cfg = school_sys.get_igcse_subject_options()
        core_subjects = list(igcse_cfg.get("core_subjects", []))
        science_tracks = list(igcse_cfg.get("science_tracks", []))

        selected_subjects = [choice.get("text", "Unknown Subject") for choice in selected_choices]
        selected_categories = [choice.get("category") for choice in selected_choices if isinstance(choice, dict)]

        # Require exactly one science track when tracks are configured.
        science_selected = [s for s in selected_subjects if s in science_tracks]
        if science_tracks and len(science_selected) != 1:
            return False, "Select exactly one science track.", []

        # Require all non-science core subjects explicitly.
        science_terms = ("science", "sciences")
        non_science_core = [
            s for s in core_subjects
            if not any(term in s.lower() for term in science_terms)
        ]
        missing_core = [subject for subject in non_science_core if subject not in selected_subjects]
        if missing_core:
            return False, f"Missing core subjects: {', '.join(missing_core)}.", []

        # Enforce elective min/max based on total min/max after mandatory subjects.
        min_total = event.ui_config.get("min_selections", 1) if event.ui_config else 1
        max_total = event.ui_config.get("max_selections", 1) if event.ui_config else 1
        mandatory_count = len(non_science_core) + (1 if science_tracks else 0)
        min_electives = max(0, min_total - mandatory_count)
        max_electives = max(0, max_total - mandatory_count)

        elective_count = sum(1 for c in selected_categories if c == "elective")
        if elective_count < min_electives or elective_count > max_electives:
            return (
                False,
                f"Choose {min_electives}-{max_electives} electives with the required core subjects.",
                []
            )

        return True, "", list(dict.fromkeys(selected_subjects))

    def _resolve_history_store(self, sim_state, agent, history_store=None):
        """
        Returns mutable per-agent history store for once-per-lifetime checks.
        Compatible with legacy stubs that only expose sim_state.event_history.
        """
        if history_store is not None:
            return history_store

        agent_uid = getattr(agent, "uid", "unknown-agent")
        if hasattr(sim_state, "agent_event_history") and isinstance(sim_state.agent_event_history, dict):
            return sim_state.agent_event_history.setdefault(agent_uid, [])

        # Backward-compatible fallback (legacy player-only event history).
        if getattr(agent, "is_player", False):
            if not hasattr(sim_state, "event_history") or not isinstance(sim_state.event_history, list):
                sim_state.event_history = []
            return sim_state.event_history

        # Generic fallback for non-player stubs.
        if not hasattr(sim_state, "_agent_event_history_fallback") or not isinstance(sim_state._agent_event_history_fallback, dict):
            sim_state._agent_event_history_fallback = {}
        return sim_state._agent_event_history_fallback.setdefault(agent_uid, [])

    def _history_contains(self, history_store, event_id):
        if isinstance(history_store, set):
            return event_id in history_store
        if isinstance(history_store, list):
            return event_id in history_store
        return False

    def _history_add(self, history_store, event_id):
        if isinstance(history_store, set):
            history_store.add(event_id)
        elif isinstance(history_store, list):
            history_store.append(event_id)

    def _is_infant_event(self, event):
        event_id = str(getattr(event, "id", "") or "")
        if event_id.startswith("EVT_INFANT_"):
            return True
        trigger = getattr(event, "trigger", {}) or {}
        max_age_months = trigger.get("max_age_months")
        if max_age_months is not None:
            try:
                return int(max_age_months) <= 35
            except (TypeError, ValueError):
                return False
        max_age = trigger.get("max_age")
        if max_age is not None:
            try:
                return int(max_age) <= 2
            except (TypeError, ValueError):
                return False
        return False

    def _is_infant_brain_v2_active(self, sim_state, agent, event, age_months):
        cfg = (getattr(sim_state, "config", {}) or {}).get("npc_brain", {}) or {}
        if not bool(cfg.get("infant_brain_v2_enabled", False)):
            return False
        if int(age_months) > 35:
            return False
        if not self._is_infant_event(event):
            return False
        temperament = getattr(agent, "temperament", None)
        return isinstance(temperament, dict) and len(temperament) > 0

    def _build_infant_brain_context(self, sim_state, agent):
        cfg = (getattr(sim_state, "config", {}) or {}).get("npc_brain", {}) or {}
        infant_cfg = cfg.get("infant_brain_v2", {}) or {}
        brain_profile = getattr(agent, "brain", {}) or {}

        # Temperament is the primary source of infant decision parameters.
        infant_params = dict(temperament_to_infant_params(getattr(agent, "temperament", {}) or {}))
        if isinstance(brain_profile, dict):
            brain_profile["infant_params"] = dict(infant_params)

        infant_state = {
            "energy_level": 0.65,
            "satiety_level": 0.60,
            "security_level": 0.70,
            "stimulation_load": 0.25,
            "last_event_novelty": 0.20,
        }
        state_from_brain = (brain_profile.get("infant_state", {}) or {})
        for key in infant_state.keys():
            if key in state_from_brain:
                try:
                    infant_state[key] = max(0.0, min(1.0, float(state_from_brain.get(key))))
                except (TypeError, ValueError):
                    pass

        weights_cfg = (infant_cfg.get("weights", {}) or {})
        penalties_cfg = (infant_cfg.get("penalties", {}) or {})
        return {
            "infant_params": infant_params,
            "infant_state": infant_state,
            "weights": dict(weights_cfg),
            "penalties": dict(penalties_cfg),
            "debug_logging": bool(cfg.get("infant_brain_v2_debug_logging", False)),
        }

    def _choose_indices_with_brain(
        self,
        sim_state,
        agent,
        event,
        domain="event_choice",
        age_months_override=None,
    ):
        if not event.choices:
            return []

        decision_key = str(getattr(event, "id", "event"))
        decision_age_months = int(
            age_months_override
            if age_months_override is not None
            else getattr(agent, "age_months", 0)
        )
        rng = make_decision_rng(
            getattr(sim_state, "world_seed", 0),
            getattr(agent, "uid", "npc"),
            decision_age_months,
            domain,
            decision_key,
        )

        if self._is_infant_brain_v2_active(sim_state, agent, event, decision_age_months):
            decision_style = (getattr(agent, "brain", {}) or {}).get("decision_style", {}) or {}
            temperature = float(decision_style.get("temperature", 1.0))
            ctx = self._build_infant_brain_context(sim_state, agent)
            infant_brain = InfantBrain(
                weights=ctx.get("weights"),
                penalties=ctx.get("penalties"),
                temperature=temperature,
            )
            options = []
            scored_rows = []
            context = {
                "event_id": decision_key,
                "infant_params": ctx.get("infant_params", {}),
                "infant_state": ctx.get("infant_state", {}),
            }
            for idx, choice in enumerate(event.choices):
                appraisal = choice_to_infant_appraisal(choice)
                option = {"id": choice.get("text", str(idx)), "appraisal": appraisal}
                options.append(option)
                score, _trace = infant_brain.score_option(option, context=context)
                scored_rows.append((idx, score, choice))

            if str(getattr(event, "ui_type", "")) == "multi_select":
                ui_cfg = event.ui_config or {}
                min_sel = max(1, int(ui_cfg.get("min_selections", 1)))
                ranked = sorted(scored_rows, key=lambda r: (-r[1], r[0]))
                return [int(idx) for idx, _, _ in ranked[:min_sel]]

            choice_out = infant_brain.choose(options, context=context, rng=rng)
            selected = [int(choice_out["chosen_index"])]

            if bool(ctx.get("debug_logging", False)):
                logger.debug(
                    "InfantBrain v2 decision: uid=%s event=%s selected=%s age_months=%s",
                    getattr(agent, "uid", "unknown"),
                    decision_key,
                    selected,
                    decision_age_months,
                )
            return selected

        relationship_type = None
        if hasattr(sim_state, "player") and hasattr(sim_state.player, "relationships"):
            rel = sim_state.player.relationships.get(agent.uid)
            relationship_type = getattr(rel, "rel_type", None) if rel else None

        effective_weights = {}
        if hasattr(sim_state, "get_effective_brain_weights"):
            effective_weights = sim_state.get_effective_brain_weights(agent, relationship_type=relationship_type)
        elif isinstance(getattr(agent, "brain", None), dict):
            effective_weights = dict(agent.brain.get("base_weights", {}) or {})

        decision_style = (getattr(agent, "brain", {}) or {}).get("decision_style", {}) or {}
        temperature = float(decision_style.get("temperature", 1.0))
        brain = NPCBrain(base_weights=effective_weights, temperature=temperature)

        options = []
        scored_rows = []
        for idx, choice in enumerate(event.choices):
            features = event_choice_to_features(choice)
            option = {"id": choice.get("text", str(idx)), "features": features}
            options.append(option)
            score, _ = brain.score_option(option)
            scored_rows.append((idx, score, choice))

        # Multi-select policy
        if str(getattr(event, "ui_type", "")) == "multi_select":
            ui_cfg = event.ui_config or {}
            min_sel = max(1, int(ui_cfg.get("min_selections", 1)))
            max_sel = max(min_sel, int(ui_cfg.get("max_selections", min_sel)))

            # Special-case IGCSE to satisfy constraints.
            if event.id == "EVT_IGCSE_SUBJECTS":
                core = [row for row in scored_rows if (row[2].get("category") == "core")]
                science = [row for row in scored_rows if (row[2].get("category") == "science_track")]
                elective = [row for row in scored_rows if (row[2].get("category") == "elective")]

                selected = [idx for idx, _, _ in core]
                if science:
                    best_science = sorted(science, key=lambda r: (-r[1], r[0]))[0]
                    selected.append(int(best_science[0]))

                target_total = max(min_sel, len(selected))
                target_total = min(target_total, max_sel)
                needed_electives = max(0, target_total - len(selected))
                ranked_elective = sorted(elective, key=lambda r: (-r[1], r[0]))
                selected.extend([int(idx) for idx, _, _ in ranked_elective[:needed_electives]])

                selected_choices = [event.choices[i] for i in selected if 0 <= i < len(event.choices)]
                ok, _, _ = self._validate_igcse_selection(sim_state, event, selected_choices)
                if not ok:
                    # Fallback: deterministic first valid pattern.
                    core_idx = [i for i, c in enumerate(event.choices) if c.get("category") == "core"]
                    science_idx = [i for i, c in enumerate(event.choices) if c.get("category") == "science_track"]
                    elective_idx = [i for i, c in enumerate(event.choices) if c.get("category") == "elective"]
                    fallback = list(core_idx)
                    if science_idx:
                        fallback.append(science_idx[0])
                    mandatory = len(fallback)
                    need = max(0, min_sel - mandatory)
                    fallback.extend(elective_idx[:need])
                    selected = fallback
                return selected

            # Generic multi-select: choose top-scoring min selections.
            ranked = sorted(scored_rows, key=lambda r: (-r[1], r[0]))
            return [int(idx) for idx, _, _ in ranked[:min_sel]]

        # Single-select policy
        choice_out = brain.choose(options, context={"event_id": decision_key}, rng=rng)
        return [int(choice_out["chosen_index"])]

    def auto_resolve_npc_events(self, sim_state, infant_only=False):
        """
        Auto-resolve NPC events using NPCBrain (no modal).
        Returns number of resolved NPC events this month.
        """
        cfg = (getattr(sim_state, "config", {}) or {}).get("npc_brain", {}) or {}
        if not bool(cfg.get("enabled", False)):
            return 0
        if not bool(cfg.get("events_enabled", False)):
            return 0

        resolved = 0
        npcs = getattr(sim_state, "npcs", {}) or {}
        debug_logging = bool(cfg.get("debug_logging", False))
        for uid in sorted(npcs.keys()):
            agent = npcs.get(uid)
            if not agent or not getattr(agent, "is_alive", False):
                continue
            age_months = int(getattr(agent, "age_months", 0))
            if age_months < 1:
                continue
            if infant_only and (age_months > 35 or getattr(agent, "temperament", None) is None):
                continue

            history_store = self._resolve_history_store(sim_state, agent)
            event = self.evaluate_month_for_agent(sim_state, agent, history_store=history_store)
            if event is None:
                continue
            if infant_only and not self._is_infant_event(event):
                continue
            if not bool(getattr(event, "npc_auto", True)):
                continue

            try:
                selected = self._choose_indices_with_brain(sim_state, agent, event)
                self.apply_resolution_to_agent(
                    sim_state,
                    agent,
                    event,
                    selected,
                    history_store=history_store,
                    emit_output=False,
                )
                if debug_logging:
                    logger.debug(
                        "NPC event auto-resolved: uid=%s event=%s selected=%s age_months=%s",
                        agent.uid,
                        event.id,
                        selected,
                        age_months,
                    )
                resolved += 1
            except Exception as e:
                logger.warning(
                    "NPC event auto-resolve failed for uid=%s event=%s: %s",
                    getattr(agent, "uid", "unknown"),
                    getattr(event, "id", "unknown"),
                    e,
                )
        return resolved

    def auto_resolve_npc_infant_events(self, sim_state):
        """
        Backward-compatible phase-5 wrapper.
        """
        return self.auto_resolve_npc_events(sim_state, infant_only=True)

    def _apply_subject_effects(self, sim_state, agent, subject_effects: Dict[str, Any]):
        """
        Applies subject-level effects with a consistent academic state update path.
        Supported keys:
        - "ALL" / "all" / "overall" / "performance": distributed to all active subjects
        - Exact subject names: applied to matching subjects only
        """
        if not agent.school:
            return

        if not isinstance(subject_effects, dict):
            return

        for subject_key, delta in subject_effects.items():
            try:
                delta_value = float(delta)
            except (TypeError, ValueError):
                logger.warning(f"Invalid subject effect delta: {subject_key}={delta}")
                continue

            normalized = str(subject_key).strip().lower()
            if normalized in ("all", "overall", "performance"):
                school_logic.apply_academic_delta(agent, delta_value)
            else:
                school_logic.apply_academic_delta(agent, delta_value, target_subjects=[subject_key])

    def evaluate_month_for_agent(
        self,
        sim_state,
        agent,
        history_store=None,
        age_months_override=None,
        infant_only=False,
    ):
        """
        Evaluate and potentially trigger events for a specific agent this month.
        
        Args:
            sim_state: The current simulation state.
            agent: Target agent to evaluate.
            history_store: Optional per-agent history collection.
            
        Returns:
            Event object if an event should be triggered, None otherwise.
        """
        if agent is None:
            return None

        base_age_months = int(getattr(agent, "age_months", int(getattr(agent, "age", 0)) * 12))
        age_months = int(base_age_months if age_months_override is None else age_months_override)
        age_year = age_months // 12
        history_store = self._resolve_history_store(sim_state, agent, history_store=history_store)
        
        # Check each event for age-based triggers
        for event in self.events:
            if infant_only and not self._is_infant_event(event):
                continue
            # Skip events that have already occurred if they're once-per-lifetime
            if hasattr(event, 'once_per_lifetime') and event.once_per_lifetime:
                if self._history_contains(history_store, event.id):
                    continue
            
            trigger = event.trigger or {}
            min_age = int(trigger.get("min_age", 0))
            max_age = int(trigger.get("max_age", 999))
            min_age_months = int(trigger.get("min_age_months", min_age * 12))
            # Year-based max_age used player.age integer before; preserve equivalent month range.
            max_age_months = int(trigger.get("max_age_months", ((max_age + 1) * 12) - 1))

            # Check if player age in months falls within event's age window.
            # Keep year value available for logs and compatibility.
            if min_age_months <= age_months <= max_age_months:
                if event.id == "EVT_IGCSE_SUBJECTS":
                    return self._build_igcse_event(event, sim_state)
                logger.info(
                    f"Event '{event.id}' triggered for agent {getattr(agent, 'uid', 'unknown')} "
                    f"age {age_year} ({age_months} months)"
                )
                return event
        
        # No matching events found
        return None

    def evaluate_infant_event_for_agent_at_month(self, sim_state, agent, age_months, history_store=None):
        """
        Evaluate infant-only event eligibility using an explicit age-month cursor.
        """
        month_cursor = int(age_months)
        if month_cursor < 1 or month_cursor > 35:
            return None
        return self.evaluate_month_for_agent(
            sim_state,
            agent,
            history_store=history_store,
            age_months_override=month_cursor,
            infant_only=True,
        )

    def resolve_infant_event_for_agent_at_month(self, sim_state, agent, age_months, history_store=None):
        """
        Resolve one infant-only event at explicit month cursor for NPC backfill replay.
        Returns True when an event was resolved, else False.
        """
        cfg = (getattr(sim_state, "config", {}) or {}).get("npc_brain", {}) or {}
        if not bool(cfg.get("enabled", False)):
            return False
        if not bool(cfg.get("events_enabled", False)):
            return False

        history_store = self._resolve_history_store(sim_state, agent, history_store=history_store)
        event = self.evaluate_infant_event_for_agent_at_month(
            sim_state,
            agent,
            age_months,
            history_store=history_store,
        )
        if event is None:
            return False
        if not bool(getattr(event, "npc_auto", True)):
            return False

        month_cursor = int(age_months)
        selected = self._choose_indices_with_brain(
            sim_state,
            agent,
            event,
            domain="event_choice_backfill",
            age_months_override=month_cursor,
        )
        self.apply_resolution_to_agent(
            sim_state,
            agent,
            event,
            selected,
            history_store=history_store,
            emit_output=False,
        )

        debug_logging = bool(
            cfg.get("infant_event_backfill_debug_logging", cfg.get("debug_logging", False))
        )
        if debug_logging:
            logger.debug(
                "NPC infant backfill replay resolved: uid=%s event=%s selected=%s replay_month=%s",
                getattr(agent, "uid", "unknown"),
                getattr(event, "id", "unknown"),
                selected,
                month_cursor,
            )
        return True

    def replay_infant_events_for_agent(self, sim_state, agent, target_age_months, history_store=None):
        """
        Replay infant-only events from month 1 to min(target_age_months, 35).
        Returns total resolved event count.
        """
        resolved = 0
        max_month = min(35, max(0, int(target_age_months)))
        history_store = self._resolve_history_store(sim_state, agent, history_store=history_store)
        for month_cursor in range(1, max_month + 1):
            if self.resolve_infant_event_for_agent_at_month(
                sim_state,
                agent,
                month_cursor,
                history_store=history_store,
            ):
                resolved += 1
        return resolved

    def evaluate_month(self, sim_state):
        """
        Backward-compatible player wrapper.
        """
        player = getattr(sim_state, "player", None)
        if player is None:
            return None
        history_store = self._resolve_history_store(sim_state, player)
        return self.evaluate_month_for_agent(sim_state, player, history_store=history_store)

    def apply_resolution_to_agent(self, sim_state, agent, event, selected_choice_indices, history_store=None, emit_output=True):
        """
        Apply the effects of an event resolution to a target agent.
        
        Args:
            sim_state: The current simulation state.
            agent: Target agent receiving event effects.
            event: The Event object being resolved.
            selected_choice_indices: List of selected choice indices.
            history_store: Optional per-agent history collection.
        """
        if event is None or agent is None:
            return
        history_store = self._resolve_history_store(sim_state, agent, history_store=history_store)

        # Get the selected choice data
        selected_choices = []
        for choice_index in selected_choice_indices:
            if 0 <= choice_index < len(event.choices):
                selected_choices.append(event.choices[choice_index])
            else:
                logger.warning(f"Invalid choice index {choice_index} for event {event.id}")
        
        # Log the resolution
        choice_texts = [choice.get("text", "Unknown Choice") for choice in selected_choices]
        logger.info(f"Event '{event.id}' resolved with choices: {choice_texts}")
        if emit_output:
            print(f"Event Resolution: {event.title} -> {', '.join(choice_texts)}")
        
        # Apply effects for all selected choices
        for selected_choice in selected_choices:
            effects = selected_choice.get("effects", {})
            stats_effects = effects.get("stats", {})
            temperament_effects = effects.get("temperament", {})
            subject_effects = effects.get("subjects", {})
            
            # Apply temperament effects (for infants)
            if temperament_effects and agent.temperament:
                plasticity = agent.plasticity
                
                for trait_name, trait_change in temperament_effects.items():
                    if trait_name in agent.temperament:
                        current_value = agent.temperament[trait_name]
                        # Apply plasticity multiplier and clamp to 0-100 range
                        new_value = current_value + (trait_change * plasticity)
                        new_value = max(0, min(100, new_value))
                        
                        agent.temperament[trait_name] = round(new_value, 1)
                        logger.info(f"Agent temperament {trait_name}: {current_value} -> {new_value} (change: {trait_change * plasticity:+.1f})")
                        if emit_output:
                            print(f"Temperament Change: {trait_name} {trait_change * plasticity:+.1f}")
                    else:
                        logger.warning(f"Unknown temperament trait: {trait_name}")
            
            # Apply regular stats effects
            if stats_effects:
                for stat_name, stat_change in stats_effects.items():
                    if hasattr(agent, stat_name):
                        current_value = getattr(agent, stat_name)
                        new_value = current_value + stat_change
                        
                        # Clamp to 0-100 range for stats
                        if stat_name in ["health", "happiness"]:
                            new_value = max(0, min(100, new_value))
                        
                        setattr(agent, stat_name, new_value)
                        logger.info(f"Agent {stat_name}: {current_value} -> {new_value} (change: {stat_change:+d})")
                        if emit_output:
                            print(f"Stat Change: {stat_name.capitalize()} {stat_change:+d}")
                    else:
                        logger.warning(f"Unknown stat: {stat_name}")

            # Apply subject-level academic effects (if provided by event config)
            if subject_effects:
                self._apply_subject_effects(sim_state, agent, subject_effects)

            # Phase 3: Track player style from chosen event options (player only).
            if getattr(agent, "is_player", False) and hasattr(sim_state, "_update_player_style_tracker"):
                observed = event_choice_to_features(selected_choice)
                sim_state._update_player_style_tracker(observed)

            # Phase 5: Infant v2 post-choice state transition (when enabled).
            if hasattr(sim_state, "_update_infant_state_after_choice"):
                sim_state._update_infant_state_after_choice(agent, selected_choice)
        
        # Special handler for IGCSE Subject Selection
        if event.id == "EVT_IGCSE_SUBJECTS":
            is_valid, error_message, finalized_subjects = self._validate_igcse_selection(
                sim_state,
                event,
                selected_choices
            )
            if not is_valid:
                if hasattr(sim_state, "add_log"):
                    sim_state.add_log(error_message, constants.COLOR_LOG_NEGATIVE)
                logger.warning(f"Invalid IGCSE selection: {error_message}")
                return

            if agent.school:
                agent.school["igcse_subjects"] = finalized_subjects
                agent.sync_subjects_with_school(
                    sim_state.school_system,
                    preserve_existing=True,
                    reset_monthly_change=True
                )
                school_logic.recalculate_school_performance(agent)
                logger.info(f"Agent's IGCSE subjects updated: {finalized_subjects}")
                if emit_output:
                    print(f"School Subjects: {', '.join(finalized_subjects)}")
            else:
                logger.warning("Agent has no school data to update subjects")
        
        # Add event to per-agent history
        self._history_add(history_store, event.id)

        # Backward compatibility: keep player history mirror in sim_state.event_history.
        if getattr(agent, "is_player", False) and hasattr(sim_state, "event_history") and isinstance(sim_state.event_history, list):
            if history_store is not sim_state.event_history:
                sim_state.event_history.append(event.id)
        
        # Clear pending modal only for player flow.
        if getattr(agent, "is_player", False) and hasattr(sim_state, "pending_event"):
            sim_state.pending_event = None
        
        # TODO: Implement flags, relationship changes, and other effects based on choices
        # This will be expanded as the event system grows

    def apply_resolution(self, sim_state, event, selected_choice_indices):
        """
        Backward-compatible player wrapper.
        """
        player = getattr(sim_state, "player", None)
        if player is None:
            return
        history_store = self._resolve_history_store(sim_state, player)
        self.apply_resolution_to_agent(
            sim_state,
            player,
            event,
            selected_choice_indices,
            history_store=history_store,
            emit_output=True,
        )
