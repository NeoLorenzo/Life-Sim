"""
Social Simulation Module.
Defines data structures for Relationships and Modifiers.
"""
from dataclasses import dataclass
from typing import List

@dataclass
class Modifier:
    """
    Represents a temporary or permanent factor affecting a relationship.
    """
    name: str
    value: float
    duration: int = -1  # -1 = Permanent, >0 = Months remaining
    decay: float = 0.0  # Amount value decreases per month

class Relationship:
    """
    Represents a social connection between two agents.
    Score = Base Affinity + Sum(Modifiers).
    """
    def __init__(self, owner_uid, target_uid, rel_type, base_affinity, target_name, is_alive=True):
        self.owner_uid = owner_uid
        self.target_uid = target_uid
        self.rel_type = rel_type
        self.target_name = target_name
        self.is_alive = is_alive
        
        self.base_affinity = base_affinity
        self.modifiers: List[Modifier] = []
        self.cached_score = 0
        
        self.recalculate()

    def add_modifier(self, name, value, duration=-1, decay=0.0):
        """Adds a modifier and updates the score."""
        # Check if modifier exists (overwrite if so)
        for mod in self.modifiers:
            if mod.name == name:
                mod.value = value
                mod.duration = duration
                mod.decay = decay
                self.recalculate()
                return
        
        self.modifiers.append(Modifier(name, value, duration, decay))
        self.recalculate()

    def recalculate(self):
        """Sum affinity and modifiers, clamping result."""
        total = self.base_affinity
        for mod in self.modifiers:
            total += mod.value
            
        # Clamp between -100 and 100
        self.cached_score = max(-100, min(100, int(round(total))))

    @property
    def total_score(self):
        return self.cached_score
        
    # --- Compatibility Helpers for Legacy Code (Temporary) ---
    def __getitem__(self, key):
        if key == "value": return self.cached_score
        if key == "type": return self.rel_type
        if key == "name": return self.target_name
        if key == "is_alive": return self.is_alive
        raise KeyError(f"Relationship object has no key '{key}'")

    def __setitem__(self, key, value):
        if key == "is_alive": self.is_alive = value
        elif key == "type": self.rel_type = value
        # Value cannot be set directly anymore