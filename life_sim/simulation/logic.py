# life_sim/simulation/logic.py
"""
Simulation Logic Module.
Handles the rules for processing turns, events, and state changes.
"""
import logging
import random
from .state import SimState

logger = logging.getLogger(__name__)

def process_turn(sim_state: SimState):
    """
    Advances the simulation by one year.
    
    1. Check if alive.
    2. Increment Age.
    3. Apply Stat Decay.
    4. Check for Death.
    5. Log results.
    """
    agent = sim_state.agent
    
    if not agent.is_alive:
        return

    # 1. Age Up
    agent.age += 1
    
    # 2. Stat Decay (Random 0-5 health loss per year)
    # Rule 12: Uses global random which was seeded in main.py
    decay = random.randint(0, 5)
    agent.health = max(0, agent.health - decay)
    
    # 3. Generate Event Log
    sim_state.add_log(f"--- Age {agent.age} ---")
    if decay > 0:
        sim_state.add_log(f"Health declined by {decay}.")
    else:
        sim_state.add_log("You felt great this year.")

    # 4. Death Check
    if agent.health <= 0:
        agent.is_alive = False
        sim_state.add_log("You have died.")
        logger.info(f"Agent died at age {agent.age}")
    
    logger.info(f"Turn processed: Age {agent.age}, Health {agent.health}, Alive: {agent.is_alive}")