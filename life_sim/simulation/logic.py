# life_sim/simulation/logic.py
"""
Simulation Logic Module.
Handles the rules for processing turns, events, and state changes.
"""
import logging
import random
from .state import SimState
from .. import constants

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
        sim_state.add_log(f"Earned ${salary} from {agent.job['title']}.", constants.COLOR_LOG_POSITIVE)
    
    # 2. Stat Decay (Random 0-5 health loss per year)
    # Rule 12: Uses global random which was seeded in main.py
    decay = random.randint(0, 5)
    agent.health = max(0, agent.health - decay)
    
    # 3. Generate Event Log
    sim_state.add_log(f"--- Age {agent.age} ---", constants.COLOR_LOG_HEADER)
    if decay > 0:
        sim_state.add_log(f"Health declined by {decay}.", constants.COLOR_LOG_NEGATIVE)
    else:
        sim_state.add_log("You felt great this year.", constants.COLOR_LOG_POSITIVE)

    # 4. Death Check
    if agent.health <= 0:
        agent.is_alive = False
        sim_state.add_log("You have died.", constants.COLOR_DEATH)
        logger.info(f"Agent died at age {agent.age}")
    
    logger.info(f"Turn processed: Age {agent.age}, Health {agent.health}, Alive: {agent.is_alive}")

def work(sim_state: SimState):
    """Agent performs overtime if employed."""
    agent = sim_state.agent
    if not agent.is_alive:
        return

    if not agent.job:
        sim_state.add_log("You are unemployed. Get a job (J) first.", constants.COLOR_LOG_NEGATIVE)
        return

    # Overtime bonus is 1% of salary
    bonus = int(agent.job['salary'] * 0.01)
    agent.money += bonus
    sim_state.add_log(f"Worked overtime. Earned ${bonus}.", constants.COLOR_LOG_POSITIVE)
    logger.info(f"Action: Overtime. Money: {agent.money}")

def study(sim_state: SimState):
    """Agent studies to increase smarts."""
    agent = sim_state.agent
    if not agent.is_alive:
        return
        
    gain = random.randint(2, 5)
    agent.smarts = min(100, agent.smarts + gain)
    
    # Studying costs a little health (stress/sedentary)
    agent.health = max(0, agent.health - 1)
    
    sim_state.add_log(f"You studied hard. Smarts +{gain}.", constants.COLOR_LOG_POSITIVE)
    logger.info(f"Action: Study. Smarts: {agent.smarts}")

def find_job(sim_state: SimState):
    """Attempts to find a job based on qualifications."""
    agent = sim_state.agent
    if not agent.is_alive:
        return
        
    jobs = sim_state.config.get("economy", {}).get("jobs", [])
    if not jobs:
        sim_state.add_log("No jobs available.", constants.COLOR_LOG_NEGATIVE)
        return
        
    # Pick a random job to apply for
    target_job = random.choice(jobs)
    required_smarts = target_job.get("min_smarts", 0)
    
    if agent.smarts >= required_smarts:
        agent.job = target_job
        sim_state.add_log(f"Hired as {target_job['title']}!", constants.COLOR_LOG_POSITIVE)
        logger.info(f"Action: Hired. Job: {target_job['title']}")
    else:
        sim_state.add_log(f"Rejected from {target_job['title']}.", constants.COLOR_LOG_NEGATIVE)
        sim_state.add_log(f"Need {required_smarts} Smarts (Have {agent.smarts}).")
        logger.info(f"Action: Rejected. Job: {target_job['title']}, Req: {required_smarts}, Has: {agent.smarts}")

def visit_doctor(sim_state: SimState):
    """Agent visits doctor to restore health."""
    agent = sim_state.agent
    if not agent.is_alive:
        return

    cost = 100
    if agent.money < cost:
        sim_state.add_log(f"You need ${cost} to visit the doctor.", constants.COLOR_LOG_NEGATIVE)
        return

    agent.money -= cost
    recovery = random.randint(10, 20)
    old_health = agent.health
    agent.health = min(100, agent.health + recovery)
    
    sim_state.add_log(f"Dr. Mario treated you. Health +{agent.health - old_health}.", constants.COLOR_LOG_POSITIVE)
    logger.info(f"Action: Doctor. Cost: {cost}, Health: {agent.health}")