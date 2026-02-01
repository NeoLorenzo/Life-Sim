# life_sim/simulation/events.py
"""
Event Management Module.
Handles event evaluation, triggering, and resolution for the simulation.
"""
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

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
        
        # Special handler for IGCSE Subject Selection
        if event.id == "EVT_IGCSE_SUBJECTS":
            selected_subjects = [choice.get("text", "Unknown Subject") for choice in selected_choices]
            if sim_state.player.school:
                sim_state.player.school['subjects'] = selected_subjects
                logger.info(f"Player's IGCSE subjects updated: {selected_subjects}")
                print(f"School Subjects: {', '.join(selected_subjects)}")
            else:
                logger.warning("Player has no school data to update subjects")
        
        # Add event to history
        sim_state.event_history.append(event.id)
        
        # Clear the pending event to close the modal
        sim_state.pending_event = None
        
        # TODO: Implement flags, relationship changes, and other effects based on choices
        # This will be expanded as the event system grows
