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

        # Curriculum configuration (Phase 1 foundation for config-driven subjects)
        self.subjects_by_stage = data.get("subjects_by_stage", {})
        self.igcse_configuration = data.get("igcse_configuration", {})
        self.ib_groups = list(data.get("ib_groups", []))

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

        # Preserve stage order from config for consistent curriculum lookups.
        self.stage_order = [stage["name"] for stage in data.get("stages", [])]

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

    def get_stage_subjects(self, stage_name):
        """Returns configured subjects for a given stage name."""
        subjects = self.subjects_by_stage.get(stage_name, [])
        # De-duplicate while preserving config order.
        return list(dict.fromkeys(subjects))

    def get_igcse_subject_options(self):
        """Returns IGCSE configuration buckets from config."""
        core = self.igcse_configuration.get("core_subjects", [])
        electives = self.igcse_configuration.get("elective_pool", [])
        science_tracks = self.igcse_configuration.get("science_tracks", [])

        return {
            "core_subjects": list(dict.fromkeys(core)),
            "elective_pool": list(dict.fromkeys(electives)),
            "science_tracks": list(dict.fromkeys(science_tracks))
        }

    def get_ib_default_subject_set(self, stage_name=None):
        """
        Returns a default IB subject portfolio:
        one subject per configured IB group plus Theory of Knowledge when present.
        """
        subjects = list(dict.fromkeys(self.ib_groups))

        if stage_name:
            stage_subjects = self.get_stage_subjects(stage_name)
            if "Theory of Knowledge" in stage_subjects and "Theory of Knowledge" not in subjects:
                subjects.append("Theory of Knowledge")

        return subjects

    def ensure_ib_subjects_for_agent(self, agent):
        """
        Ensures KS5 agents have a persistent IB subject set.
        Current model: one slot per IB group (+ Theory of Knowledge).
        """
        if not agent or not agent.school:
            return []

        stage_name = agent.school.get("stage", "")
        if "Key Stage 5" not in stage_name and "IB" not in stage_name:
            return []

        existing = agent.school.get("ib_subjects")
        if existing:
            return list(dict.fromkeys(existing))

        assigned = self.get_ib_default_subject_set(stage_name=stage_name)
        if assigned:
            agent.school["ib_subjects"] = assigned
        return assigned

    def get_active_subjects_for_agent(self, agent):
        """
        Returns the canonical active subject list for the agent's current stage.
        This is the Phase 1 source-of-truth helper used by later refactors.
        """
        if not agent or not agent.school:
            return []

        stage_name = agent.school.get("stage")
        if not stage_name:
            return []

        if "IGCSE" in stage_name:
            selected_igcse = agent.school.get("igcse_subjects") or agent.school.get("subjects")
            if selected_igcse:
                return list(dict.fromkeys(selected_igcse))

        if "Key Stage 5" in stage_name or "IB" in stage_name:
            assigned_ib = self.ensure_ib_subjects_for_agent(agent)
            if assigned_ib:
                return assigned_ib

        stage_subjects = self.get_stage_subjects(stage_name)
        if stage_subjects:
            return stage_subjects

        # Fallbacks if a stage exists without explicit subjects_by_stage entry.
        if "IGCSE" in stage_name:
            igcse = self.get_igcse_subject_options()
            return igcse["core_subjects"] + igcse["elective_pool"]

        if "Key Stage 5" in stage_name or "IB" in stage_name:
            return self.get_ib_default_subject_set(stage_name=stage_name)

        return []

def recalculate_school_performance(agent):
    """
    Recomputes and stores overall school performance from active subjects.
    Returns the computed integer performance or None if not applicable.
    """
    if not agent or not agent.school:
        return None

    if agent.subjects:
        overall = sum(s["current_grade"] for s in agent.subjects.values()) / len(agent.subjects)
        agent.school["performance"] = int(overall)
        return agent.school["performance"]

    if "performance" in agent.school:
        agent.school["performance"] = int(max(0, min(100, agent.school["performance"])))
        return agent.school["performance"]

    return None

def apply_academic_delta(agent, delta_points, target_subjects=None):
    """
    Applies an academic delta across subjects (or specific targets) and
    keeps overall performance synchronized.
    """
    if not agent or not agent.school:
        return False

    delta_points = float(delta_points)
    if abs(delta_points) < 1e-9:
        return False

    if not agent.subjects:
        current = float(agent.school.get("performance", 50))
        agent.school["performance"] = int(max(0, min(100, current + delta_points)))
        return True

    if target_subjects:
        targets = [subject for subject in target_subjects if subject in agent.subjects]
    else:
        targets = list(agent.subjects.keys())

    if not targets:
        return False

    per_subject_delta = delta_points / len(targets)
    for subject in targets:
        data = agent.subjects[subject]
        prev = float(data["current_grade"])
        updated = max(0, min(100, prev + per_subject_delta))
        data["current_grade"] = updated
        data["monthly_change"] = round(float(data.get("monthly_change", 0.0)) + (updated - prev), 1)

    recalculate_school_performance(agent)
    return True

def _gcse_9_to_1(score):
    """Maps 0-100 to UK GCSE 9-1 band (with U for ungraded)."""
    if score >= 90:
        return "9"
    if score >= 80:
        return "8"
    if score >= 70:
        return "7"
    if score >= 60:
        return "6"
    if score >= 50:
        return "5"
    if score >= 40:
        return "4"
    if score >= 30:
        return "3"
    if score >= 20:
        return "2"
    if score >= 10:
        return "1"
    return "U"

def _ib_7_to_1(score):
    """Maps 0-100 to IB 7-1 scale."""
    if score >= 85:
        return "7"
    if score >= 75:
        return "6"
    if score >= 65:
        return "5"
    if score >= 55:
        return "4"
    if score >= 45:
        return "3"
    if score >= 35:
        return "2"
    return "1"

def _key_stage_attainment(score):
    """Simple UK-style attainment band for KS1-KS3/EYFS."""
    if score >= 75:
        return "Greater Depth"
    if score >= 50:
        return "Expected"
    return "Working Towards"

def _british_grade_label(score, stage_name):
    """Returns stage-appropriate British/international grade label."""
    stage = (stage_name or "").lower()
    if "igcse" in stage or "key stage 4" in stage:
        return _gcse_9_to_1(score)
    if "ib" in stage or "key stage 5" in stage or "sixth form" in stage:
        return _ib_7_to_1(score)
    return _key_stage_attainment(score)

def _is_passing_grade(score, stage_name):
    """Stage-aware pass threshold aligned to British/international grade bands."""
    stage = (stage_name or "").lower()
    if "igcse" in stage or "key stage 4" in stage:
        # GCSE standard pass is grade 4+
        return score >= 40
    if "ib" in stage or "key stage 5" in stage or "sixth form" in stage:
        # IB-style pass threshold: 4+
        return score >= 55
    # Earlier key stages use Expected as passing threshold.
    return score >= 50

def _log_year_end_report_card(sim_state, agent):
    """Writes a year-end report card to the history log for the player."""
    if not agent.is_player or not agent.school:
        return

    recalculate_school_performance(agent)

    year_label = agent.school.get("year_label", "Unknown Year")
    form_label = agent.school.get("form_label", "")
    stage_name = agent.school.get("stage", "")
    class_label = f"{year_label}{form_label}"
    overall = int(agent.school.get("performance", 0))
    overall_band = _british_grade_label(overall, stage_name)

    sim_state.add_log(f"Report Card: {class_label}", constants.COLOR_LOG_HEADER)
    sim_state.add_log(f"Curriculum Scale: {stage_name}", constants.COLOR_TEXT_DIM)

    if not agent.subjects:
        sim_state.add_log("No subject grades recorded.", constants.COLOR_TEXT_DIM)
    else:
        for subject_name in sorted(agent.subjects.keys()):
            score = int(agent.subjects[subject_name]["current_grade"])
            band = _british_grade_label(score, stage_name)
            if _is_passing_grade(score, stage_name):
                color = constants.COLOR_LOG_POSITIVE
            else:
                color = constants.COLOR_LOG_NEGATIVE
            sim_state.add_log(f"{subject_name}: {score}/100 ({band})", color)

    sim_state.add_log(
        f"Overall Performance: {overall}/100 ({overall_band})",
        constants.COLOR_ACCENT
    )

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

def _sync_agent_subjects_for_current_stage(sim_state, agent, school_sys, preserve_existing=True):
    """
    Synchronizes an agent subject portfolio to current stage curriculum and
    returns a transition summary for callers that need year-boundary behavior.
    """
    previous_subjects = set(agent.subjects.keys()) if isinstance(agent.subjects, dict) else set()

    synced = agent.sync_subjects_with_school(
        school_sys,
        preserve_existing=preserve_existing,
        reset_monthly_change=True
    )
    if not synced:
        return {"synced": False, "carried": [], "added": [], "retired": []}

    current_subjects = set(agent.subjects.keys())
    carried = sorted(previous_subjects & current_subjects)
    added = sorted(current_subjects - previous_subjects)
    retired = sorted(previous_subjects - current_subjects)

    recalculate_school_performance(agent)

    return {"synced": True, "carried": carried, "added": added, "retired": retired}

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
        if not agent.subjects:
            agent.sync_subjects_with_school(school_sys, preserve_existing=True)

        if not agent.subjects:
            return

        # Update each subject individually based on natural aptitude only
        for subject_name, subject_data in agent.subjects.items():
            # Category/profile-based drift with deterministic modifiers.
            progression_rate = float(subject_data.get("progression_rate", 0.02))
            aptitude_influence = (subject_data["natural_aptitude"] - 50) * progression_rate
            cognitive_penalty = max(0.0, min(0.8, float(getattr(agent, "_temp_cognitive_penalty", 0.0))))
            attendance_modifier = 0.6 + (0.4 * float(agent.attendance_rate))
            aptitude_influence *= (1.0 - cognitive_penalty) * attendance_modifier
            
            # Store previous grade for change tracking
            previous_grade = subject_data["current_grade"]
            
            # Apply change and clamp to 0-100
            subject_data["current_grade"] += aptitude_influence
            subject_data["current_grade"] = max(0, min(100, subject_data["current_grade"]))
            
            # Track monthly change for tooltips
            subject_data["monthly_change"] = round(subject_data["current_grade"] - previous_grade, 1)
        
        # Update overall performance for compatibility (average of all subjects)
        recalculate_school_performance(agent)

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

        transition = _sync_agent_subjects_for_current_stage(
            sim_state,
            agent,
            school_sys,
            preserve_existing=True
        )
        
        if agent.is_player:
            sim_state.add_log(f"Started school year: {agent.school['year_label']} (Form {agent.school['form_label']})", constants.COLOR_ACCENT)
            if transition["added"]:
                sim_state.add_log(
                    f"New subjects this year: {', '.join(transition['added'])}.",
                    constants.COLOR_TEXT_DIM
                )
            if transition["retired"]:
                sim_state.add_log(
                    f"Completed subjects: {', '.join(transition['retired'])}.",
                    constants.COLOR_TEXT_DIM
                )
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
        _sync_agent_subjects_for_current_stage(sim_state, agent, school_sys, preserve_existing=False)
        
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
    current_stage_name = agent.school.get("stage", "")
    _log_year_end_report_card(sim_state, agent)
    
    # Pass/Fail Logic
    passed = _is_passing_grade(agent.school["performance"], current_stage_name)
    
    if passed:
        if agent.is_player:
            perf = int(agent.school["performance"])
            label = _british_grade_label(perf, current_stage_name)
            sim_state.add_log(
                f"Finished {current_grade_name}. Performance: {perf}/100 ({label}).",
                constants.COLOR_TEXT
            )
        
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
