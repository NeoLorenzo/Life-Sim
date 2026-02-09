# life_sim/simulation/events.py
"""
Event Management Module.
Handles event evaluation, triggering, and resolution for the simulation.
"""
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .. import constants
from . import school as school_logic

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """
    Represents a single game event with its configuration and metadata.
    """
    id: str
    title: str
    description: str
    trigger: Dict[str, Any]  # Contains min_age, max_age, etc.
    ui_type: str  # single_select, multi_select, etc.
    choices: List[Dict[str, Any]]  # List of choice dictionaries with text and effects
    once_per_lifetime: bool = False  # Whether event can only trigger once per game
    ui_config: Dict[str, Any] = None  # UI configuration like min/max selections
    
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
            ui_config=config.get("ui_config", {})
        )

class EventManager:
    """
    Manages the lifecycle of game events including evaluation, triggering, and resolution.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the EventManager with configuration data.
        
        Args:
            config (dict): The loaded configuration dictionary containing event definitions.
        """
        self.config = config
        raw_definitions = config.get("events", {}).get("definitions", [])
        
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
            ui_config=event.ui_config or {}
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

    def _apply_subject_effects(self, sim_state, subject_effects: Dict[str, Any]):
        """
        Applies subject-level effects with a consistent academic state update path.
        Supported keys:
        - "ALL" / "all" / "overall" / "performance": distributed to all active subjects
        - Exact subject names: applied to matching subjects only
        """
        player = sim_state.player
        if not player.school:
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
                school_logic.apply_academic_delta(player, delta_value)
            else:
                school_logic.apply_academic_delta(player, delta_value, target_subjects=[subject_key])
    
    def evaluate_month(self, sim_state):
        """
        Evaluate and potentially trigger events for the current month.
        
        Args:
            sim_state: The current simulation state.
            
        Returns:
            Event object if an event should be triggered, None otherwise.
        """
        player_age = sim_state.player.age
        
        # Check each event for age-based triggers
        for event in self.events:
            # Skip events that have already occurred if they're once-per-lifetime
            if hasattr(event, 'once_per_lifetime') and event.once_per_lifetime:
                if event.id in sim_state.event_history:
                    continue
            
            trigger = event.trigger
            min_age = trigger.get("min_age", 0)
            max_age = trigger.get("max_age", 999)
            
            # Check if player age falls within event's age range
            if min_age <= player_age <= max_age:
                if event.id == "EVT_IGCSE_SUBJECTS":
                    return self._build_igcse_event(event, sim_state)
                logger.info(f"Event '{event.id}' triggered for player age {player_age}")
                return event
        
        # No matching events found
        return None
    
    def apply_resolution(self, sim_state, event, selected_choice_indices):
        """
        Apply the effects of an event resolution.
        
        Args:
            sim_state: The current simulation state.
            event: The Event object being resolved.
            selected_choice_indices: List of selected choice indices.
        """
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
        print(f"Event Resolution: {event.title} -> {', '.join(choice_texts)}")
        
        # Apply effects for all selected choices
        for selected_choice in selected_choices:
            effects = selected_choice.get("effects", {})
            stats_effects = effects.get("stats", {})
            temperament_effects = effects.get("temperament", {})
            subject_effects = effects.get("subjects", {})
            
            # Apply temperament effects (for infants)
            if temperament_effects and sim_state.player.temperament:
                player = sim_state.player
                plasticity = player.plasticity
                
                for trait_name, trait_change in temperament_effects.items():
                    if trait_name in player.temperament:
                        current_value = player.temperament[trait_name]
                        # Apply plasticity multiplier and clamp to 0-100 range
                        new_value = current_value + (trait_change * plasticity)
                        new_value = max(0, min(100, new_value))
                        
                        player.temperament[trait_name] = round(new_value, 1)
                        logger.info(f"Player temperament {trait_name}: {current_value} -> {new_value} (change: {trait_change * plasticity:+.1f})")
                        print(f"Temperament Change: {trait_name} {trait_change * plasticity:+.1f}")
                    else:
                        logger.warning(f"Unknown temperament trait: {trait_name}")
            
            # Apply regular stats effects
            if stats_effects:
                player = sim_state.player
                for stat_name, stat_change in stats_effects.items():
                    if hasattr(player, stat_name):
                        current_value = getattr(player, stat_name)
                        new_value = current_value + stat_change
                        
                        # Clamp to 0-100 range for stats
                        if stat_name in ["health", "happiness"]:
                            new_value = max(0, min(100, new_value))
                        
                        setattr(player, stat_name, new_value)
                        logger.info(f"Player {stat_name}: {current_value} -> {new_value} (change: {stat_change:+d})")
                        print(f"Stat Change: {stat_name.capitalize()} {stat_change:+d}")
                    else:
                        logger.warning(f"Unknown stat: {stat_name}")

            # Apply subject-level academic effects (if provided by event config)
            if subject_effects:
                self._apply_subject_effects(sim_state, subject_effects)
        
        # Special handler for IGCSE Subject Selection
        if event.id == "EVT_IGCSE_SUBJECTS":
            is_valid, error_message, finalized_subjects = self._validate_igcse_selection(
                sim_state,
                event,
                selected_choices
            )
            if not is_valid:
                sim_state.add_log(error_message, constants.COLOR_LOG_NEGATIVE)
                logger.warning(f"Invalid IGCSE selection: {error_message}")
                return

            if sim_state.player.school:
                sim_state.player.school["igcse_subjects"] = finalized_subjects
                sim_state.player.sync_subjects_with_school(
                    sim_state.school_system,
                    preserve_existing=True,
                    reset_monthly_change=True
                )
                school_logic.recalculate_school_performance(sim_state.player)
                logger.info(f"Player's IGCSE subjects updated: {finalized_subjects}")
                print(f"School Subjects: {', '.join(finalized_subjects)}")
            else:
                logger.warning("Player has no school data to update subjects")
        
        # Add event to history
        sim_state.event_history.append(event.id)
        
        # Clear the pending event to close the modal
        sim_state.pending_event = None
        
        # TODO: Implement flags, relationship changes, and other effects based on choices
        # This will be expanded as the event system grows
