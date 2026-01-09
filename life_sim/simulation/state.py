# life_sim/simulation/state.py
"""
Simulation State Module.
Holds the core data model for the simulation.
"""
import logging

class Agent:
    """
    Represents the primary agent (Player).
    
    Data Contract:
        Inputs: config dictionary (agent section)
        State: age (int), health (int), happiness (int), smarts (int), looks (int)
    """
    def __init__(self, agent_config: dict):
        self.logger = logging.getLogger(__name__)
        
        self.age = agent_config.get("initial_age", 0)
        self.health = agent_config.get("initial_health", 50)
        self.happiness = agent_config.get("initial_happiness", 50)
        self.smarts = agent_config.get("initial_smarts", 50)
        self.looks = agent_config.get("initial_looks", 50)
        self.money = agent_config.get("initial_money", 0)
        self.is_alive = True
        
        self.logger.info(f"Agent initialized. Age: {self.age}, Health: {self.health}, Money: {self.money}")

class SimState:
    """
    Container for the entire simulation world.
    """
    def __init__(self, config: dict):
        self.config = config
        self.agent = Agent(config["agent"])
        self.event_log = ["Simulation started."]

    def add_log(self, message: str):
        """Adds a message to the in-game event log."""
        self.event_log.append(message)