# life_sim/simulation/logic.py
"""
Simulation Logic Module.
Handles the rules for processing turns, events, and state changes.
"""
import logging
import random
from .state import SimState
from . import school, affinity # Import affinity module
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

    # 1. Store current age bracket before processing
    time_conf = sim_state.config.get("time_management", {})
    old_bracket = _get_age_bracket(player.age, time_conf.get("sleep_requirements", {}))

    # 2. Advance Global Time
    sim_state.month_index += 1
    if sim_state.month_index > 11:
        sim_state.month_index = 0
        sim_state.year += 1
        sim_state.add_log(f"Happy New Year {sim_state.year}!", constants.COLOR_TEXT_DIM)
    
    # 3. Process Player (The Hero)
    _process_agent_monthly(sim_state, player)
    
    # 4. Check for Life Stage change and reset schedule if needed
    new_bracket = _get_age_bracket(player.age, time_conf.get("sleep_requirements", {}))
    if old_bracket != new_bracket:
        player.target_sleep_hours = player.ap_sleep
        player.attendance_rate = 1.0
        sim_state.add_log("Life Stage: Schedule reset to defaults.", constants.COLOR_ACCENT)
    
    # 5. Process NPCs (The Population)
    for uid, npc in sim_state.npcs.items():
        if not npc.is_alive:
            continue
        
        _process_agent_monthly(sim_state, npc)
        _simulate_npc_routine(sim_state, npc) # Auto-spend AP with brain policy when enabled
        
        # NPC Death Notification
        if not npc.is_alive:
            if uid in player.relationships:
                rel = player.relationships[uid]
                rel.is_alive = False
                sim_state.add_log(f"Your {rel.rel_type}, {npc.first_name}, died at age {npc.age}.", constants.COLOR_DEATH)
                player.happiness = max(0, player.happiness - 30)

    # 6. Global Systems
    school.process_school_turn(sim_state)
    
    logger.info(f"Turn processed: {sim_state.month_index}/{sim_state.year}. Player Age: {player.age}")

def _get_age_bracket(age, sleep_requirements):
    """Determine the age bracket for a given age based on sleep requirements."""
    if not sleep_requirements:
        return "default"
    
    # Sort by max_age to find the correct bracket
    sorted_reqs = sorted(sleep_requirements.values(), key=lambda x: x["max_age"])
    
    for req in sorted_reqs:
        if age <= req["max_age"]:
            return req.get("max_age", "default")
    
    # Fallback for oldest age
    if sorted_reqs:
        return sorted_reqs[-1].get("max_age", "default")
    
    return "default"

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
        
        # Temperament to Personality Transition (Age 3)
        # Check the new age after birthday
        new_age = agent.age_months // 12
        if new_age == 3 and agent.is_personality_locked == False:
            # Crystallize temperament into permanent personality
            agent.crystallize_personality()
            if agent.is_player:
                sim_state.add_log(f"Your personality has crystallized! You now have permanent traits that will affect your relationships.", constants.COLOR_LOG_POSITIVE)
            
            # Update family relationships to use new personality-based affinity
            sim_state._update_family_relationships_for_personality(agent)
            if agent.is_player:
                sim_state.add_log(f"Your family relationships now reflect your personality compatibility.", constants.COLOR_LOG_POSITIVE)
        
        # Annual Biological Updates
        old_cap = agent.max_health
        agent._recalculate_max_health()
        agent._recalculate_hormones()
        
        # Natural Entropy (Wear & Tear for Seniors)
        if new_age > 50:
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
    
    # D. Plasticity Decay (for young children)
    if agent.age < 3 and agent.age in constants.PLASTICITY_DECAY:
        target_plasticity = constants.PLASTICITY_DECAY[agent.age]
        if agent.plasticity != target_plasticity:
            agent.plasticity = target_plasticity
            if agent.is_player:
                sim_state.add_log(f"Plasticity updated to {target_plasticity}", constants.COLOR_TEXT_DIM)

    # E. Infant brain homeostasis update (phase 5)
    if hasattr(sim_state, "_update_infant_state_monthly"):
        sim_state._update_infant_state_monthly(agent)
    
    # F. Time Management (AP Reset)
    agent.ap_used = 0
    time_conf = sim_state.config.get("time_management", {})
    agent._recalculate_ap_needs(time_conf)
    
    # G. Sleep Penalties
    sleep_deficit = max(0, agent.ap_sleep - agent.target_sleep_hours)
    if sleep_deficit > 0:
        penalties = time_conf.get("penalties", {})
        health_loss = sleep_deficit * penalties.get("health_loss_per_hour_missed", 2)
        happiness_loss = sleep_deficit * penalties.get("happiness_loss_per_hour_missed", 3)
        cognitive_penalty = sleep_deficit * penalties.get("cognitive_penalty_per_hour", 0.05)
        
        agent.health = max(0, agent.health - health_loss)
        agent.happiness = max(0, agent.happiness - happiness_loss)
        agent._temp_cognitive_penalty = cognitive_penalty
        
        if agent.is_player:
            sim_state.add_log(f"Sleep Deprived: Health -{health_loss:.0f}, Cognitive -{cognitive_penalty*100:.0f}%", constants.COLOR_LOG_NEGATIVE)
    else:
        agent._temp_cognitive_penalty = 0.0
    
    # H. Truancy Logic
    skipped_hours = agent.ap_locked * (1.0 - agent.attendance_rate)
    if skipped_hours > 0:
        penalties = time_conf.get("penalties", {})
        risk = skipped_hours * penalties.get("truancy_base_risk", 0.10)
        
        if random.random() < risk:
            # Caught skipping - apply performance penalty
            performance_penalty = penalties.get("truancy_performance_penalty", 10)
            
            if agent.school:
                school.apply_academic_delta(agent, -performance_penalty)
                if agent.is_player:
                    sim_state.add_log("Caught skipping! Grades and performance penalized.", constants.COLOR_LOG_NEGATIVE)
            elif agent.job:
                # Job performance isn't fully tracked yet, so just log it
                if agent.is_player:
                    sim_state.add_log("Caught skipping work! Performance penalized.", constants.COLOR_LOG_NEGATIVE)
                else:
                    logger.debug(f"NPC {agent.first_name} caught skipping work")
        else:
            # Skipped undetected
            logger.debug(f"{agent.first_name} skipped {skipped_hours:.1f}h undetected")
    
    # I. Economics (Salary)
    if agent.job:
        monthly_salary = int(agent.job['salary'] / 12)
        agent.money += monthly_salary
        
        if agent.is_player:
            sim_state.add_log(f"Earned ${monthly_salary} from {agent.job['title']}.", constants.COLOR_LOG_POSITIVE)
        else:
            # Log to debug only to avoid spam
            logger.debug(f"NPC {agent.first_name} earned ${monthly_salary}")

    # J. Mortality Check
    # Enforce biological cap
    if agent.health > agent.max_health:
        agent.health = agent.max_health
        
    if agent.health <= 0:
        agent.is_alive = False
        if agent.is_player:
            sim_state.add_log("You have died.", constants.COLOR_DEATH)
            logger.info(f"Player died at age {agent.age}")

def _simulate_npc_routine_legacy(npc):
    """
    Legacy NPC AP routine.
    """
    # 1. Sleep (Maintenance)
    npc.ap_used += npc.ap_sleep
    
    # 2. Work / School (Locked)
    # Future: Calculate actual commute/hours. For now, assume standard 8h if employed.
    if npc.job:
        npc.ap_locked = 8.0
    elif npc.school and npc.school["is_in_session"]:
        npc.ap_locked = school.get_school_hours_by_age(npc.age)
    else:
        npc.ap_locked = 0.0
        
    npc.ap_used += npc.ap_locked
    
    # 3. Free Time (Abstracted)
    # In the future, AI will spend 'npc.free_ap'.
    # For now, we leave it as 'Free' or assume they spent it on leisure.


def _simulate_npc_routine(sim_state, npc):
    """
    Strict parity mode:
    NPC AP routine mirrors currently implemented player AP behavior and does not
    run internal-only discretionary actions until player discretionary AP exists.
    """
    _simulate_npc_routine_legacy(npc)

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

    cost = constants.DOCTOR_VISIT_COST
    if player.money < cost:
        sim_state.add_log(f"You need ${cost} to visit the doctor.", constants.COLOR_LOG_NEGATIVE)
        return

    player.money -= cost
    recovery = random.randint(constants.DOCTOR_RECOVERY_MIN, constants.DOCTOR_RECOVERY_MAX)
    old_health = player.health
    # Clamp to max_health instead of static 100
    player.health = min(player.max_health, player.health + recovery)
    
    sim_state.add_log(f"Dr. Mario treated you. Health +{player.health - old_health}.", constants.COLOR_LOG_POSITIVE)
    logger.info(f"Action: Doctor. Cost: {cost}, Health: {player.health}")
