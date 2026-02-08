# life_sim/simulation/school.py
"""
School Logic Module.
Handles enrollment, academic years, and graduation.
"""
import logging
import string
import random
from .. import constants

logger = logging.getLogger(__name__)

class School:
    """
    Represents a specific school entity with a defined structure.
    """
    def __init__(self, config):
        self.id = config["active_school_id"]
        data = config["schools"][self.id]
        
        self.name = data["name"]
        self.type = data["type"]
        self.start_month = data["start_month_index"]
        self.end_month = data["end_month_index"]
        
        # Structure
        self.forms_per_year = data["structure"]["forms_per_year"]
        self.class_capacity = data["structure"]["class_capacity"]
        
        # Track form assignments
        self.student_forms = {}  # student_id -> form_letter
        
        # Flatten hierarchy for linear progression logic
        self.grades = []
        for stage in data["stages"]:
            for g in stage["grades"]:
                self.grades.append({
                    "name": g["name"],
                    "min_age": g["min_age"],
                    "stage": stage["name"]
                })

    def get_grade_info(self, index):
        if 0 <= index < len(self.grades):
            return self.grades[index]
        return None

    def get_random_form_label(self):
        """Returns a random form label (A, B, C...) based on forms_per_year."""
        return string.ascii_uppercase[random.randint(0, self.forms_per_year - 1)]
    
    def enroll_student(self, student_id, form=None):
        """Enrolls a student in a specific form. If form is None, assigns randomly."""
        if form is None:
            form = self.get_random_form_label()
        
        self.student_forms[student_id] = form
        return form
    
    def get_form_students(self, form_letter):
        """Returns a list of student IDs for a given form."""
        return [student_id for student_id, form in self.student_forms.items() if form == form_letter]

def process_school_turn(sim_state):
    """
    Called every month to handle school logic for ALL agents.
    """
    school_sys = sim_state.school_system
    if not school_sys:
        return

    # Process Player
    if sim_state.player.is_alive:
        _process_single_agent_school(sim_state, sim_state.player, school_sys)
        
    # Process NPCs
    for npc in sim_state.npcs.values():
        if npc.is_alive:
            _process_single_agent_school(sim_state, npc, school_sys)

def _process_single_agent_school(sim_state, agent, school_sys):
    current_month = sim_state.month_index
    
    # 1. Start of School Year (Enrollment / Advancement)
    if current_month == school_sys.start_month:
        _handle_school_start(sim_state, agent, school_sys)

    # 2. End of School Year (Results / Graduation)
    elif current_month == school_sys.end_month:
        _handle_school_end(sim_state, agent, school_sys)

    # 3. Monthly Update (if in session)
    if agent.school and agent.school["is_in_session"]:
        # Update each subject individually based on natural aptitude only
        for subject_name, subject_data in agent.subjects.items():
            # Base drift influenced by natural aptitude only (no randomness)
            aptitude_influence = (subject_data["natural_aptitude"] - 50) * 0.02  # -1 to +1 based on aptitude
            
            # Store previous grade for change tracking
            previous_grade = subject_data["current_grade"]
            
            # Apply change and clamp to 0-100
            subject_data["current_grade"] += aptitude_influence
            subject_data["current_grade"] = max(0, min(100, subject_data["current_grade"]))
            
            # Track monthly change for tooltips
            subject_data["monthly_change"] = round(subject_data["current_grade"] - previous_grade, 1)
        
        # Update overall performance for compatibility (average of all subjects)
        overall_performance = sum(s["current_grade"] for s in agent.subjects.values()) / len(agent.subjects)
        agent.school["performance"] = int(overall_performance)

def _handle_school_start(sim_state, agent, school_sys):
    """Starts the school year, enrolling or advancing grades."""
    
    # Case A: Already in school -> Start Session
    if agent.school:
        agent.school["is_in_session"] = True
        
        # Set AP locked time for school session (7 hours per day)
        agent.ap_locked = 7.0
        
        # Update display labels
        grade_info = school_sys.get_grade_info(agent.school["year_index"])
        if grade_info:
            agent.school["year_label"] = grade_info["name"]
            agent.school["stage"] = grade_info["stage"]
        
        if agent.is_player:
            sim_state.add_log(f"Started school year: {agent.school['year_label']} (Form {agent.school['form_label']})", constants.COLOR_ACCENT)
            # CHECK POPULATION HERE TOO (In case we loaded a save or logic changed)
            sim_state.populate_classmates()
            
        return

    # Case B: Not in school -> Check for Enrollment
    eligible_idx = -1
    
    for i, grade in enumerate(school_sys.grades):
        if agent.age == grade["min_age"]:
            eligible_idx = i
            break
            
    if eligible_idx != -1:
        grade_data = school_sys.grades[eligible_idx]
        form_label = school_sys.get_random_form_label()
        
        agent.school = {
            "school_id": school_sys.id,
            "school_name": school_sys.name,
            "stage": grade_data["stage"],
            "year_index": eligible_idx,
            "year_label": grade_data["name"],
            "form_label": form_label,
            "performance": 50,
            "is_in_session": True
        }
        
        # Set AP locked time for school (7 hours per day)
        agent.ap_locked = 7.0
        
        if agent.is_player:
            sim_state.add_log(f"Enrolled in {grade_data['name']} at {school_sys.name}.", constants.COLOR_LOG_POSITIVE)
            # TRIGGER POPULATION HERE
            sim_state.populate_classmates()
        
        logger.info(f"Agent {agent.first_name} enrolled in {grade_data['name']} Form {form_label}")

def _handle_school_end(sim_state, agent, school_sys):
    """Ends the school year, handles passing/failing/graduation."""
    if not agent.school or not agent.school["is_in_session"]:
        return

    agent.school["is_in_session"] = False
    current_idx = agent.school["year_index"]
    current_grade_name = agent.school["year_label"]
    
    # Pass/Fail Logic
    passed = agent.school["performance"] > 20
    
    if passed:
        if agent.is_player:
            sim_state.add_log(f"Finished {current_grade_name}. Performance: {agent.school['performance']}/100.", constants.COLOR_TEXT)
        
        # Check for Graduation
        if current_idx >= len(school_sys.grades) - 1:
            if agent.is_player:
                sim_state.add_log(f"Graduated from {school_sys.name}!", constants.COLOR_LOG_POSITIVE)
            
            agent.school = None # Left school
            agent.ap_locked = 0.0 # Reset locked time after graduation
            agent.happiness = min(100, agent.happiness + 20)
        else:
            # Advance to next grade for next year
            # IMPORTANT: Keep the same form_label!
            agent.school["year_index"] += 1
            
            # Update labels for next year immediately or wait for start?
            # Let's update index now, labels update on start.
            
            if agent.is_player:
                sim_state.add_log("Enjoy your summer break!", constants.COLOR_TEXT_DIM)
    else:
        if agent.is_player:
            sim_state.add_log(f"Failed {current_grade_name}. You must repeat the year.", constants.COLOR_LOG_NEGATIVE)
        
        agent.happiness = max(0, agent.happiness - 20)
        # Do not increment year_index, keep same form