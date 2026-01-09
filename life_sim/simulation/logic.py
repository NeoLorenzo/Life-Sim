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
    
    # 1b. Process Salary
    if agent.job:
        salary = agent.job['salary']
        agent.money += salary
        sim_state.add_log(f"Earned ${salary} from {agent.job['title']}.")
    
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

def work(sim_state: SimState):
    """Agent performs overtime if employed."""
    agent = sim_state.agent
    if not agent.is_alive:
        return

    if not agent.job:
        sim_state.add_log("You are unemployed. Get a job (J) first.")
        return

    # Overtime bonus is 1% of salary
    bonus = int(agent.job['salary'] * 0.01)
    agent.money += bonus
    sim_state.add_log(f"Worked overtime. Earned ${bonus}.")
    logger.info(f"Action: Overtime. Money: {agent.money}")

def find_job(sim_state: SimState):
    """Assigns a random job from config."""
    agent = sim_state.agent
    if not agent.is_alive:
        return
        
    jobs = sim_state.config.get("economy", {}).get("jobs", [])
    if not jobs:
        sim_state.add_log("No jobs available in economy.")
        return
        
    new_job = random.choice(jobs)
    agent.job = new_job
    sim_state.add_log(f"You were hired as a {new_job['title']}!")
    logger.info(f"Action: Hired. Job: {new_job['title']}, Salary: {new_job['salary']}")

def visit_doctor(sim_state: SimState):
    """Agent visits doctor to restore health."""
    agent = sim_state.agent
    if not agent.is_alive:
        return

    cost = 100
    if agent.money < cost:
        sim_state.add_log(f"You need ${cost} to visit the doctor.")
        return

    agent.money -= cost
    recovery = random.randint(10, 20)
    old_health = agent.health
    agent.health = min(100, agent.health + recovery)
    
    sim_state.add_log(f"Dr. Mario treated you. Health +{agent.health - old_health}.")
    logger.info(f"Action: Doctor. Cost: {cost}, Health: {agent.health}")