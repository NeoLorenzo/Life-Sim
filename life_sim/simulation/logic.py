# life_sim/simulation/logic.py
"""
Simulation Logic Module.
Handles the rules for processing turns, events, and state changes.
"""
import logging
import random
from .state import SimState
from . import school
from .. import constants

logger = logging.getLogger(__name__)

def process_turn(sim_state: SimState):
    """
    Advances the simulation by one month.
    Unified loop: Player and NPCs share the same biological/economic rules.
    """
    player = sim_state.player
    
    if not player.is_alive:
        return

    # 1. Advance Global Time
    sim_state.month_index += 1
    if sim_state.month_index > 11:
        sim_state.month_index = 0
        sim_state.year += 1
        sim_state.add_log(f"Happy New Year {sim_state.year}!", constants.COLOR_TEXT_DIM)
    
    # 2. Process Player (The Hero)
    _process_agent_monthly(sim_state, player)
    
    # 3. Process NPCs (The Population)
    for uid, npc in sim_state.npcs.items():
        if not npc.is_alive:
            continue
        
        _process_agent_monthly(sim_state, npc)
        _simulate_npc_routine(npc) # Auto-spend AP for mandatory tasks
        
        # NPC Death Notification
        if not npc.is_alive:
            if uid in player.relationships:
                rel = player.relationships[uid]
                rel["is_alive"] = False
                sim_state.add_log(f"Your {rel['type']}, {npc.first_name}, died at age {npc.age}.", constants.COLOR_DEATH)
                player.happiness = max(0, player.happiness - 30)

    # 4. Global Systems
    school.process_school_turn(sim_state)
    
    logger.info(f"Turn processed: {sim_state.month_index}/{sim_state.year}. Player Age: {player.age}")

def _process_agent_monthly(sim_state, agent):
    """Applies biological and economic updates to a single agent."""
    
    # A. Aging
    agent.age_months += 1
    
    # Birthday Check
    is_birthday = (agent.age_months % 12 == 0)
    if is_birthday:
        if agent.is_player:
            sim_state.start_new_year(agent.age)
            sim_state.add_log("Happy Birthday!", constants.COLOR_ACCENT)
        
        # Annual Biological Updates
        old_cap = agent.max_health
        agent._recalculate_max_health()
        agent._recalculate_hormones()
        
        # Natural Entropy (Wear & Tear for Seniors)
        if agent.age > 50:
            damage = random.randint(0, 3)
            agent.health -= damage

    # B. Monthly Growth (Height)
    if agent.age <= 20 and agent.height_cm < agent.genetic_height_potential:
        # Growth Phase
        if random.random() < 0.2: 
            agent.height_cm = min(agent.genetic_height_potential, agent.height_cm + 1)
    elif agent.age > 60:
        # Shrinkage Phase
        if random.random() < 0.03:
            agent.height_cm -= 1
            
    # C. Physique Update
    agent._recalculate_physique()
    
    # D. Time Management (AP Reset)
    agent.ap_used = 0
    time_conf = sim_state.config.get("time_management", {})
    agent._recalculate_ap_needs(time_conf)
    
    # E. Economics (Salary)
    if agent.job:
        monthly_salary = int(agent.job['salary'] / 12)
        agent.money += monthly_salary
        
        if agent.is_player:
            sim_state.add_log(f"Earned ${monthly_salary} from {agent.job['title']}.", constants.COLOR_LOG_POSITIVE)
        else:
            # Log to debug only to avoid spam
            logger.debug(f"NPC {agent.first_name} earned ${monthly_salary}")

    # F. Mortality Check
    # Enforce biological cap
    if agent.health > agent.max_health:
        agent.health = agent.max_health
        
    if agent.health <= 0:
        agent.is_alive = False
        if agent.is_player:
            sim_state.add_log("You have died.", constants.COLOR_DEATH)
            logger.info(f"Player died at age {agent.age}")

def _simulate_npc_routine(npc):
    """
    Simulates the NPC spending AP on mandatory tasks.
    This ensures their state (AP Used) is valid for future AI logic.
    """
    # 1. Sleep (Maintenance)
    npc.ap_used += npc.ap_sleep
    
    # 2. Work / School (Locked)
    # Future: Calculate actual commute/hours. For now, assume standard 8h if employed.
    if npc.job:
        npc.ap_locked = 8.0
    elif npc.school and npc.school["is_in_session"]:
        npc.ap_locked = 7.0
    else:
        npc.ap_locked = 0.0
        
    npc.ap_used += npc.ap_locked
    
    # 3. Free Time (Abstracted)
    # In the future, AI will spend 'npc.free_ap'.
    # For now, we leave it as 'Free' or assume they spent it on leisure.

def work(sim_state: SimState):
    """Agent performs overtime if employed."""
    player = sim_state.player
    if not player.is_alive:
        return

    if not player.job:
        sim_state.add_log("You are unemployed. Get a job (J) first.", constants.COLOR_LOG_NEGATIVE)
        return

    # Overtime bonus is 1% of salary
    bonus = int(player.job['salary'] * 0.01)
    player.money += bonus
    sim_state.add_log(f"Worked overtime. Earned ${bonus}.", constants.COLOR_LOG_POSITIVE)
    logger.info(f"Action: Overtime. Money: {player.money}")

def find_job(sim_state: SimState):
    """Attempts to find a job."""
    player = sim_state.player
    if not player.is_alive:
        return
        
    jobs = sim_state.config.get("economy", {}).get("jobs", [])
    if not jobs:
        sim_state.add_log("No jobs available.", constants.COLOR_LOG_NEGATIVE)
        return
        
    # Pick a random job to apply for
    target_job = random.choice(jobs)
    
    player.job = target_job
    sim_state.add_log(f"Hired as {target_job['title']}!", constants.COLOR_LOG_POSITIVE)
    logger.info(f"Action: Hired. Job: {target_job['title']}")

def visit_doctor(sim_state: SimState):
    """Agent visits doctor to restore health."""
    player = sim_state.player
    if not player.is_alive:
        return

    cost = 100
    if player.money < cost:
        sim_state.add_log(f"You need ${cost} to visit the doctor.", constants.COLOR_LOG_NEGATIVE)
        return

    player.money -= cost
    recovery = random.randint(10, 20)
    old_health = player.health
    # Clamp to max_health instead of static 100
    player.health = min(player.max_health, player.health + recovery)
    
    sim_state.add_log(f"Dr. Mario treated you. Health +{player.health - old_health}.", constants.COLOR_LOG_POSITIVE)
    logger.info(f"Action: Doctor. Cost: {cost}, Health: {player.health}")