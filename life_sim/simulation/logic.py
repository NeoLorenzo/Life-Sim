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
    Advances the simulation by one month.
    
    1. Check if alive.
    2. Increment Date & Age.
    3. Apply Monthly Economics.
    4. Check for Death.
    5. Process NPCs (Truman Show).
    6. Log results.
    """
    player = sim_state.player
    
    if not player.is_alive:
        return

    # 1. Advance Time
    sim_state.month_index += 1
    if sim_state.month_index > 11:
        sim_state.month_index = 0
        sim_state.year += 1
        # Calendar Year changed - just add a log note, don't start new block
        sim_state.add_log(f"Happy New Year {sim_state.year}!", constants.COLOR_TEXT_DIM)
    
    # 2. Age Up Player
    player.age_months += 1
    
    # Check for Birthday (Start new Log Block)
    if sim_state.month_index == sim_state.birth_month_index:
        sim_state.start_new_year(player.age)
        sim_state.add_log("Happy Birthday!", constants.COLOR_ACCENT)

    # 2a. Recalculate Health Cap (Frailty) - Only check on birthday
    if sim_state.month_index == sim_state.birth_month_index:
        old_cap = player.max_health
        player._recalculate_max_health()
        if player.max_health < old_cap:
            pass

    # 2b. Process Growth / Aging (Height)
    # Distribute growth over the year
    if player.age <= 20 and player.height_cm < player.genetic_height_potential:
        # Growth Phase: Close the gap to potential
        gap = player.genetic_height_potential - player.height_cm
        months_left = (21 * 12) - player.age_months
        if months_left > 0:
            # Small chance to grow this month
            if random.random() < 0.2: 
                player.height_cm = min(player.genetic_height_potential, player.height_cm + 1)
    elif player.age > 60:
        # Seniority Phase: Shrinkage (Rarely)
        if random.random() < 0.03: # ~36% chance per year
            player.height_cm -= 1

    # 2c. Update Physique (Weight/BMI)
    player._recalculate_physique()

    # 2d. Process Monthly Salary
    if player.job:
        monthly_salary = int(player.job['salary'] / 12)
        player.money += monthly_salary
        sim_state.add_log(f"Earned ${monthly_salary} from {player.job['title']}.", constants.COLOR_LOG_POSITIVE)
    
    # 3. Death Check (Player)
    if player.health <= 0:
        player.is_alive = False
        sim_state.add_log("You have died.", constants.COLOR_DEATH)
        logger.info(f"Player died at age {player.age}")
        return

    # 4. Process NPCs (Truman Show Optimization)
    for uid, npc in sim_state.npcs.items():
        if not npc.is_alive:
            continue
            
        npc.age_months += 1
        
        # Only process NPC health decay once a year (on their "birthday" equivalent)
        # Simplified: Process when month_index matches player's birth month (Annual cycle)
        if sim_state.month_index == sim_state.birth_month_index:
            npc._recalculate_max_health()
            
            # Apply Natural Entropy (Wear & Tear)
            if npc.age > 50:
                damage = random.randint(0, 3)
                npc.health -= damage

            # Enforce the biological cap
            if npc.health > npc.max_health:
                npc.health = npc.max_health

        # Enforce the biological cap
        # If max_health drops below current health, current health is crushed down.
        if npc.health > npc.max_health:
            npc.health = npc.max_health
        
        # Standard Death Check
        if npc.health <= 0:
            npc.is_alive = False
            # Notify Player if related
            if uid in player.relationships:
                rel = player.relationships[uid]
                rel["is_alive"] = False
                sim_state.add_log(f"Your {rel['type']}, {npc.first_name}, died at age {npc.age}.", constants.COLOR_DEATH)
                # Apply sadness
                player.happiness = max(0, player.happiness - 30)

    logger.info(f"Turn processed: Age {player.age}, Health {player.health}, Alive: {player.is_alive}")

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

def study(sim_state: SimState):
    """Agent studies to increase smarts."""
    player = sim_state.player
    if not player.is_alive:
        return
        
    gain = random.randint(2, 5)
    player.smarts = min(100, player.smarts + gain)
    
    # Studying costs a little health (stress/sedentary)
    player.health = max(0, player.health - 1)
    
    sim_state.add_log(f"You studied hard. Smarts +{gain}.", constants.COLOR_LOG_POSITIVE)
    logger.info(f"Action: Study. Smarts: {player.smarts}")

def find_job(sim_state: SimState):
    """Attempts to find a job based on qualifications."""
    player = sim_state.player
    if not player.is_alive:
        return
        
    jobs = sim_state.config.get("economy", {}).get("jobs", [])
    if not jobs:
        sim_state.add_log("No jobs available.", constants.COLOR_LOG_NEGATIVE)
        return
        
    # Pick a random job to apply for
    target_job = random.choice(jobs)
    required_smarts = target_job.get("min_smarts", 0)
    
    if player.smarts >= required_smarts:
        player.job = target_job
        sim_state.add_log(f"Hired as {target_job['title']}!", constants.COLOR_LOG_POSITIVE)
        logger.info(f"Action: Hired. Job: {target_job['title']}")
    else:
        sim_state.add_log(f"Rejected from {target_job['title']}.", constants.COLOR_LOG_NEGATIVE)
        sim_state.add_log(f"Need {required_smarts} Smarts (Have {player.smarts}).")
        logger.info(f"Action: Rejected. Job: {target_job['title']}, Req: {required_smarts}, Has: {player.smarts}")

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