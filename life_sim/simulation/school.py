# life_sim/simulation/school.py
"""
School Logic Module.
Handles enrollment, academic years, and graduation.
"""
import logging
from .. import constants
import random

logger = logging.getLogger(__name__)

def process_school_turn(sim_state):
    """
    Called every month to handle school logic for ALL agents.
    """
    edu_config = sim_state.config.get("education", {})
    sys_name = edu_config.get("default_system", "British_International")
    system = edu_config.get("systems", {}).get(sys_name)
    
    if not system:
        return

    # Process Player
    if sim_state.player.is_alive:
        _process_single_agent_school(sim_state, sim_state.player, system, sys_name)
        
    # Process NPCs
    for npc in sim_state.npcs.values():
        if npc.is_alive:
            _process_single_agent_school(sim_state, npc, system, sys_name)

def _process_single_agent_school(sim_state, agent, system, sys_name):
    current_month = sim_state.month_index
    start_month = system["start_month_index"] # 8 = Sept
    end_month = system["end_month_index"]     # 5 = June

    # 1. Start of School Year (Enrollment / Advancement)
    if current_month == start_month:
        _handle_school_start(sim_state, agent, system, sys_name)

    # 2. End of School Year (Results / Graduation)
    elif current_month == end_month:
        _handle_school_end(sim_state, agent, system)

    # 3. Monthly Update (if in session)
    if agent.school and agent.school["is_in_session"]:
        # Random performance drift
        drift = random.randint(-2, 2)
        agent.school["performance"] += drift
        # Clamp
        agent.school["performance"] = max(0, min(100, agent.school["performance"]))

def _handle_school_start(sim_state, agent, system, sys_name):
    """Starts the school year, enrolling or advancing grades."""
    grades = system["grades"]
    
    # Case A: Already in school -> Start Session
    if agent.school:
        agent.school["is_in_session"] = True
        grade_idx = agent.school["grade_index"]
        grade_name = grades[grade_idx]["name"]
        
        if agent.is_player:
            sim_state.add_log(f"Started school year: {grade_name}", constants.COLOR_ACCENT)
        return

    # Case B: Not in school -> Check for Enrollment
    # Find the appropriate grade for current age
    eligible_grade_idx = -1
    
    for i, grade in enumerate(grades):
        if agent.age == grade["min_age"]:
            eligible_grade_idx = i
            break
            
    if eligible_grade_idx != -1:
        grade_data = grades[eligible_grade_idx]
        agent.school = {
            "system": sys_name,
            "grade_index": eligible_grade_idx,
            "performance": 50, # Start average
            "is_in_session": True
        }
        
        if agent.is_player:
            sim_state.add_log(f"Enrolled in {grade_data['name']} at {agent.school['system']}.", constants.COLOR_LOG_POSITIVE)
        
        logger.info(f"Agent {agent.first_name} enrolled in {grade_data['name']}")

def _handle_school_end(sim_state, agent, system):
    """Ends the school year, handles passing/failing/graduation."""
    if not agent.school or not agent.school["is_in_session"]:
        return

    agent.school["is_in_session"] = False
    grades = system["grades"]
    current_idx = agent.school["grade_index"]
    current_grade_name = grades[current_idx]["name"]
    
    # Pass/Fail Logic (Simple for MVP)
    # If performance < 20, fail and repeat? 
    # For MVP, let's assume they pass if smarts > 10.
    passed = agent.school["performance"] > 20
    
    if passed:
        if agent.is_player:
            sim_state.add_log(f"Finished {current_grade_name}. Performance: {agent.school['performance']}/100.", constants.COLOR_TEXT)
        
        # Check for Graduation
        if current_idx >= len(grades) - 1:
            if agent.is_player:
                sim_state.add_log(f"Graduated from {agent.school['system']}!", constants.COLOR_LOG_POSITIVE)
            
            agent.school = None # Left school
            # Boost smarts/happiness
            agent.happiness = min(100, agent.happiness + 20)
        else:
            # Advance to next grade for next year
            agent.school["grade_index"] += 1
            if agent.is_player:
                sim_state.add_log("Enjoy your summer break!", constants.COLOR_TEXT_DIM)
    else:
        if agent.is_player:
            sim_state.add_log(f"Failed {current_grade_name}. You must repeat the year.", constants.COLOR_LOG_NEGATIVE)
        
        agent.happiness = max(0, agent.happiness - 20)
        # Do not increment grade_index