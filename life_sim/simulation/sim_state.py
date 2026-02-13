# life_sim/simulation/sim_state.py
"""
Simulation State Module.
Holds the core data model for the simulation.
"""
import logging
import random
import uuid
from .. import constants
from . import school, affinity
from .social import Relationship # Import new class
from .agent import Agent
from .brain import (
    CANONICAL_FEATURE_KEYS,
    DEFAULT_BASE_WEIGHTS,
    default_player_style_tracker,
    update_player_style_tracker,
    blend_weights,
    choice_to_infant_appraisal,
    temperament_to_infant_params,
)

class SimState:
    """
    Container for the entire simulation world.
    """
    def __init__(self, config: dict):
        self.config = config
        self.npcs = {} # uid -> Agent
        
        # Initialize School System
        self.school_system = school.School(config["education"])
        
        # Time Tracking
        # Start at a random month in the start year
        self.month_index = random.randint(0, 11) # 0 = Jan, 11 = Dec
        self.birth_month_index = self.month_index # Store birth month for age calculation
        self.year = constants.START_YEAR
        self.world_seed = random.randint(0, 2_000_000_000)
        self._uid_counter = 0
        self.player_style_tracker = self._init_player_style_tracker()
        self._event_manager_backfill = None
        self.agent_event_history = {}
        
        # Generate Family & Player (Order matters for genetics)
        self.player = self._setup_family_and_player()
        
        # Generate Classmates (if player is in school)
        if self.player.school:
            self.populate_classmates()
        
        self.history = []
        
        # Event System
        self.pending_event = None  # Active event instance
        self.event_history = []     # IDs of past events
        self.agent_event_history.setdefault(self.player.uid, [])
        for npc_uid in self.npcs.keys():
            self.agent_event_history.setdefault(npc_uid, [])
        self.flags = set()          # String flags for conditional logic
        
        # --- Narrative Generation (Restored) ---
        # Generate Narrative Birth Message
        birth_month_name = constants.MONTHS[self.month_index]
        birth_day = random.randint(1, 28)
        
        pronoun = "He" if self.player.gender == "Male" else "She"
        possessive = "His" if self.player.gender == "Male" else "Her"
        obj_pronoun = "him" if self.player.gender == "Male" else "her"

        # 1. Appearance Reaction
        if self.player.looks > 85:
            looks_txt = f"The doctor pauses. \"This might be the most beautiful baby I've ever seen.\""
        elif self.player.looks > 60:
            looks_txt = f"The nurses are cooing over {possessive} {self.player.eye_color.lower()} eyes."
        elif self.player.looks < 30:
            looks_txt = f"The mother hesitates before holding {obj_pronoun}. \"{pronoun} has... character.\""
        else:
            looks_txt = f"{pronoun} has {possessive} mother's {self.player.eye_color.lower()} eyes and {self.player.hair_color.lower()} hair."

        # 2. Physical/Strength Reaction
        if self.player.maximal_strength > 80:
            phys_txt = f"{pronoun} is gripping the nurse's finger tightly. Surprisingly strong!"
        elif self.player.health < 40:
            phys_txt = f"{pronoun} is breathing shallowly and looks quite frail."
        else:
            phys_txt = f"{pronoun} is a healthy size, weighing {self.player.weight_kg}kg."

        # 3. Personality/Behavior Reaction
        # Handle young children with temperament vs older children with personality
        if self.player.age < 3 and self.player.temperament:
            # Use temperament for babies
            if self.player.temperament.get("Intensity", 50) > 75:
                pers_txt = f"{pronoun} is screaming uncontrollably and thrashing around!"
            elif self.player.temperament.get("Regularity", 50) > 75:
                pers_txt = f"{pronoun} is unusually calm, observing the room silently."
            else:
                pers_txt = f"{pronoun} is crying softly, looking for warmth."
        elif self.player.personality:
            # Use personality for older children
            if self.player.personality['Neuroticism']['Angry Hostility'] > 15:
                pers_txt = f"{pronoun} is screaming uncontrollably and thrashing around!"
            elif self.player.personality['Conscientiousness']['Self-Discipline'] > 15:
                pers_txt = f"{pronoun} is unusually calm, observing the room silently."
            elif self.player.iq > 120:
                pers_txt = f"{pronoun} seems to be focusing intensely on the doctor's face. Very alert."
            else:
                pers_txt = f"{pronoun} is crying softly, looking for warmth."
        else:
            # Fallback
            pers_txt = f"{pronoun} is crying softly, looking for warmth."

        # 4. Family Flavor
        parents_txt = "You are an orphan."
        father_id = next((uid for uid, rel in self.player.relationships.items() if rel["type"] == "Father"), None)
        mother_id = next((uid for uid, rel in self.player.relationships.items() if rel["type"] == "Mother"), None)
        
        if father_id and mother_id:
            f = self.npcs[father_id]
            m = self.npcs[mother_id]
            
            # Check if parents know each other (they should, but safety check)
            marital_happiness = 50
            if m.uid in f.relationships:
                marital_happiness = f.relationships[m.uid].total_score
                
            household_wealth = m.money + f.money
            
            # 1. The Setting (Season + City)
            # Use same season logic as background system
            if self.month_index in [11, 0, 1]:
                season = "a quiet, snowy morning"
            elif self.month_index in [2, 3, 4]:
                season = "a quiet, spring morning"
            elif self.month_index in [5, 6, 7]:
                season = "a quiet, summer morning"
            else:  # [8, 9, 10]
                season = "a quiet, autumn morning"
            intro = f"You enter the world in {self.player.city} during {season}."
            
            # 2. The Room Atmosphere (Wealth x Love Matrix)
            if household_wealth < 1000:
                if marital_happiness > 80:
                    vibe = "The hospital room is cramped and shared with two other families, but your parents don't seem to notice the noise. They are huddled together over your crib, whispering promises they intend to keep."
                else:
                    vibe = "The fluorescent lights hum loudly in the small, shared room. Your parents are arguing in hushed, sharp tones about the cost of the parking meter outside."
            elif household_wealth > 100000:
                if marital_happiness > 80:
                    vibe = "You are resting in a private suite filled with fresh orchids. Your parents are toasting with sparkling cider, looking exhausted but utterly triumphant."
                else:
                    vibe = "The private suite is spacious and smells of expensive lilies, but the air is frigid. Your parents sit on opposite sides of the room, scrolling through their phones in silence."
            else:
                # Middle Class
                if marital_happiness < 40:
                    vibe = "The room is standard, smelling of antiseptic and floor wax. There is a palpable tension between your parents, who are carefully avoiding eye contact."
                else:
                    vibe = "It's a standard hospital room, cluttered with plastic cups and blankets. The atmosphere is tired but warm, filled with the quiet relief that you arrived safely."

            # 3. The Mother's Moment
            if m.age < constants.MOTHER_YOUNG_AGE:
                mom_txt = f"Your mother, {m.first_name} ({m.age}), looks terrified, clutching the bedsheets like she wants to run away."
            elif m.personality and m.personality.get('Openness', {}).get('Fantasy', 0) > 18 and m.personality.get('Neuroticism', {}).get('Anxiety', 0) > 15:
                mom_txt = f"Your mother, {m.first_name}, is currently screaming at a nurse for trying to vaccinate you, insisting on a 'natural immunity' ritual instead."
            elif m.health < 40:
                mom_txt = f"Your mother, {m.first_name}, is pale and trembling, too weak to hold you for more than a moment."
            elif m.cardiovascular_endurance > 80:
                mom_txt = f"Your mother, {m.first_name}, looks annoyingly fresh, as if she just finished a light pilates session rather than childbirth."
            else:
                mom_txt = f"Your mother, {m.first_name} ({m.age}), brushes a strand of hair from her face, looking at you with a mixture of exhaustion and wonder."

            # 4. The Father's Action
            if f.age > m.age + 20:
                dad_txt = f"Your father, {f.first_name} ({f.age}), is leaning on his cane, looking proud but winded. A nurse mistakenly asks if he's the grandfather."
            elif f.personality and f.personality.get('Neuroticism', {}).get('Anxiety', 0) > 18 and f.personality.get('Openness', {}).get('Ideas', 0) > 15:
                dad_txt = f"Your father, {f.first_name}, is inspecting your fingers and toes, muttering about government tracking chips."
            elif f.personality and f.personality.get('Neuroticism', {}).get('Vulnerability', 0) > 18:
                dad_txt = f"Your father, {f.first_name}, is currently unconscious on the floor after fainting at the sight of the umbilical cord."
            elif f.job and f.job['title'] == "Software Engineer":
                dad_txt = f"Your father, {f.first_name}, is already typing your birth weight into a spreadsheet on his laptop."
            elif f.personality and f.personality.get('Agreeableness', {}).get('Altruism', 0) > 18:
                dad_txt = f"Your father, {f.first_name}, has somehow managed to order pizza for the entire maternity ward."
            else:
                dad_txt = f"Your father, {f.first_name} ({f.age}), stands awkwardly by the bedside, afraid he might break you if he touches you."

            parents_txt = f"{intro} {vibe} {mom_txt} {dad_txt}"

        # 6. Grandparent Flavor
        gp_txt = ""
        if self.player.parents:
            father, mother = self.player.parents
            
            # Helper to check GP presence
            def check_gp(gp, child, in_law):
                if not gp.is_alive: return None
                
                # Check relationship with their own child
                rel_child_obj = gp.relationships.get(child.uid)
                rel_child = rel_child_obj.total_score if rel_child_obj else 0
                
                # Check relationship with the in-law (spouse of child)
                rel_inlaw_obj = gp.relationships.get(in_law.uid)
                rel_inlaw = rel_inlaw_obj.total_score if rel_inlaw_obj else 0
                
                if rel_child > 50 and rel_inlaw > 20:
                    return "happy"
                elif rel_child < 0:
                    return "absent" # Estranged from own child
                elif rel_inlaw < -20:
                    return "tense" # Hates the spouse
                return "neutral"

            # Paternal GPs
            if father.parents:
                p_gpa, p_gma = father.parents
                status = check_gp(p_gma, father, mother)
                
                if status == "happy":
                    gp_txt += f" Your paternal grandmother, {p_gma.first_name}, is weeping with joy in the corner."
                elif status == "tense":
                    gp_txt += f" Your paternal grandmother, {p_gma.first_name}, is present but refuses to look at your mother."
                elif status == "absent":
                    gp_txt += " Your father's parents are notably absent."

            # Maternal GPs
            if mother.parents:
                m_gpa, m_gma = mother.parents
                status = check_gp(m_gpa, mother, father)
                
                if status == "happy":
                    gp_txt += f" Your maternal grandfather, {m_gpa.first_name}, is handing out cigars to the nurses."
                elif status == "tense":
                    gp_txt += f" Your maternal grandfather, {m_gpa.first_name}, is watching your father like a hawk."

        self.current_year_data = {
            "header": ("--- Life Begins ---", constants.COLOR_LOG_HEADER),
            "events": [
                (f"Name: {self.player.first_name} {self.player.last_name}", constants.COLOR_ACCENT),
                (f"Born: {birth_month_name} {birth_day}, {self.year} in {self.player.city}, {self.player.country}", constants.COLOR_TEXT),
                (parents_txt, constants.COLOR_TEXT),
                (gp_txt, constants.COLOR_TEXT),
                (f"Nurse: \"It's a {self.player.gender}!\"", constants.COLOR_LOG_POSITIVE),
                (looks_txt, constants.COLOR_TEXT),
                (phys_txt, constants.COLOR_TEXT),
                (pers_txt, constants.COLOR_TEXT)
            ],
            "expanded": True
        }

    def _assign_form_to_student(self, student, index):
        """
        Returns a configured form label based on student position.
        Index 0 gets the first configured label, then cycles through the label set.
        """
        forms = getattr(self.school_system, "form_labels", None) or ["A", "B", "C", "D"]
        return forms[index % len(forms)]

    def populate_classmates(self):
        """
        Generates the player's cohort once and keeps it stable across years.
        Public method called by school.py upon enrollment/year start.
        """
        school_data = self.player.school
        if not school_data: return
        
        # 1. Set total cohort capacity from school config.
        forms_per_year = int(getattr(self.school_system, "forms_per_year", 4))
        students_per_form = int(getattr(self.school_system, "students_per_form", 20))
        total_capacity = max(1, forms_per_year * students_per_form)
            
        # 2. Resolve persistent cohort membership.
        cohort = [self.player]
        persistent_ids = school_data.get("cohort_member_uids")
        has_persistent_cohort = isinstance(persistent_ids, list)

        if has_persistent_cohort:
            # Rebuild cohort from persisted IDs and keep order stable.
            for uid in persistent_ids:
                npc = self.npcs.get(uid)
                if npc:
                    cohort.append(npc)
        else:
            # Backfill for pre-existing saves: discover current-year classmates once.
            for npc in self.npcs.values():
                if not npc.school:
                    continue
                if (npc.school["school_id"] == school_data["school_id"] and
                    npc.school["year_index"] == school_data["year_index"] and
                    npc.school["form_label"] == school_data["form_label"]):
                    cohort.append(npc)

        existing_count = len(cohort)
        needed = max(0, total_capacity - existing_count)

        # 3. Generate classmates only once (initial population).
        if not has_persistent_cohort and needed > 0:
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Populating Class: Generating {needed} students for {school_data['year_label']} {school_data['form_label']}...")
            
            for _ in range(needed):
                classmate = self._generate_lineage_structure(
                    target_age=self.player.age,
                    is_player=False,
                    fixed_city=self.player.city,
                    fixed_country=self.player.country
                )
                
                # Force Enrollment
                classmate.school = {
                    "school_id": school_data["school_id"],
                    "school_name": school_data["school_name"],
                    "stage": school_data["stage"],
                    "year_index": school_data["year_index"],
                    "year_label": school_data["year_label"],
                    "form_label": school_data["form_label"],
                    "performance": random.randint(20, 90),
                    "is_in_session": school_data["is_in_session"],
                    "attendance_months_total": 0,
                    "attendance_months_present_equiv": 0.0
                }
                classmate.sync_subjects_with_school(self.school_system, preserve_existing=True)
                
                cohort.append(classmate)

        # Persist cohort membership so future years reuse the same students.
        school_data["cohort_member_uids"] = [student.uid for student in cohort if not student.is_player]

        # 4. Align cohort school payload with current player year/session and sync curriculum.
        for student in cohort:
            if student.is_player:
                student.sync_subjects_with_school(self.school_system, preserve_existing=True)
                continue

            previous_school = student.school if isinstance(student.school, dict) else {}
            student.school = {
                "school_id": school_data["school_id"],
                "school_name": school_data["school_name"],
                "stage": school_data["stage"],
                "year_index": school_data["year_index"],
                "year_label": school_data["year_label"],
                "form_label": school_data["form_label"],
                "performance": previous_school.get("performance", random.randint(20, 90)),
                "is_in_session": school_data["is_in_session"],
                "attendance_months_total": previous_school.get("attendance_months_total", 0),
                "attendance_months_present_equiv": previous_school.get("attendance_months_present_equiv", 0.0)
            }
            student.sync_subjects_with_school(self.school_system, preserve_existing=True)
        
        # 5. Assign social forms to the stable cohort.
        for i, student in enumerate(cohort):
            student.form = self._assign_form_to_student(student, i)

        # 6. Wire Relationships (The Mesh)
        # We link every student in the cohort to every other student
        # This ensures Classmate A knows Classmate B, not just the Player.
        
        for i in range(len(cohort)):
            for j in range(i + 1, len(cohort)):
                agent_a = cohort[i]
                agent_b = cohort[j]
                
                # Skip if already linked
                if agent_b.uid in agent_a.relationships:
                    continue
                    
                # Calculate Affinity
                aff_score = affinity.calculate_affinity(agent_a, agent_b)
                
                # Determine Type
                rel_type = "Classmate"
                if aff_score > 20: rel_type = "Acquaintance"
                elif aff_score < -20: rel_type = "Rival"
                
                # Link
                # Check if students are in the same form and add modifier if needed
                if agent_a.form == agent_b.form:
                    # Form modifier acts as a magnifier: +10 for positive affinity, -10 for negative affinity
                    form_modifier = 10 if aff_score > 0 else -10
                    self._link_agents(agent_a, agent_b, rel_type, rel_type, "Same Form", form_modifier)
                else:
                    # Link without modifier for students in different forms
                    self._link_agents(agent_a, agent_b, rel_type, rel_type)

    def _wire_classmate_relationship(self, classmate):
        """
        Establishes the initial relationship between Player and Classmate.
        """
        # 1. Calculate Affinity
        aff_score = affinity.calculate_affinity(self.player, classmate)
        
        # 2. Determine Relationship Type based on Affinity
        # High Affinity -> Potential Friend
        # Low Affinity -> Rival
        # Neutral -> Classmate
        rel_type = "Classmate"
        
        if aff_score > 20:
            rel_type = "Acquaintance"
        elif aff_score < -20:
            rel_type = "Rival"
            
        # 3. Link Agents
        # Note: We don't add a structural modifier (like "Bond") yet.
        # The relationship is purely affinity-driven at start.
        self._link_agents(self.player, classmate, rel_type, rel_type)

    @property
    def agent(self):
        """Backward compatibility for logic/renderer until refactor is complete."""
        return self.player

    def _next_uid(self, prefix="agent"):
        """Deterministic monotonic ID to keep seeded simulations reproducible."""
        self._uid_counter += 1
        return f"{prefix}-{self._uid_counter:08d}"

    def _get_reproductive_gap(self, repro_conf):
        """Calculates a realistic generation gap using Gaussian distribution."""
        min_rep = repro_conf.get("min_reproductive_age", 16)
        max_rep = repro_conf.get("max_reproductive_age", 45)
        mu = repro_conf.get("avg_reproductive_age", 28)
        sigma = repro_conf.get("reproductive_age_sd", 6)
        
        gap = int(random.gauss(mu, sigma))
        return max(min_rep, min(max_rep, gap))

    def _build_brain_profile(self, uid, is_player=False):
        """
        Builds a deterministic brain profile scaffold for an agent.
        Phase 2 wires data only; decision usage lands in later phases.
        """
        cfg = self.config.get("npc_brain", {}) or {}
        rng = random.Random(f"{self.world_seed}|{uid}|brain-profile-v1")

        def clamp01(v):
            return max(0.0, min(1.0, float(v)))

        def draw_drive(mu=0.5, sigma=0.16):
            return round(clamp01(rng.gauss(mu, sigma)), 4)

        mimic_cfg = cfg.get("player_mimic", {}) or {}
        infant_v2_cfg = cfg.get("infant_brain_v2", {}) or {}
        alpha_default_npc = float(mimic_cfg.get("alpha_default_npc", 0.10))
        alpha_default_player = float(mimic_cfg.get("alpha_default_player", 0.0))
        alpha_default = alpha_default_player if is_player else alpha_default_npc
        if not bool(cfg.get("player_mimic_enabled", False)):
            alpha_default = 0.0

        return {
            "version": "phase2_scaffold_v1",
            "enabled": bool(cfg.get("enabled", False)),
            "events_enabled": bool(cfg.get("events_enabled", False)),
            "ap_enabled": bool(cfg.get("ap_enabled", False)),
            "player_mimic_enabled": bool(cfg.get("player_mimic_enabled", False)),
            "drives": {
                "comfort": draw_drive(),
                "achievement": draw_drive(),
                "social": draw_drive(),
                "risk_avoidance": draw_drive(),
                "novelty": draw_drive(),
                "discipline": draw_drive(),
            },
            "decision_style": {
                "temperature": round(max(0.05, rng.uniform(0.7, 1.3)), 4),
                "inertia": round(clamp01(rng.uniform(0.25, 0.75)), 4),
                "noise": round(clamp01(rng.uniform(0.02, 0.2)), 4),
            },
            "player_mimic": {
                "alpha": round(clamp01(alpha_default), 4),
                "alpha_by_relation": dict(mimic_cfg.get("alpha_by_relation", {}) or {}),
            },
            "base_weights": dict(DEFAULT_BASE_WEIGHTS),
            "player_style_weights": {k: 0.0 for k in CANONICAL_FEATURE_KEYS},
            "history": {
                "event_decisions": 0,
                "ap_decisions": 0,
            },
            # Phase 2 infant-v2 scaffold: non-breaking data contract only.
            "infant_brain_version": str(infant_v2_cfg.get("version", "v2_spec_2026_02")),
            "infant_brain_v2_enabled": bool(cfg.get("infant_brain_v2_enabled", False)),
            "infant_params": {
                "novelty_tolerance": 0.5,
                "threat_sensitivity": 0.5,
                "energy_budget": 0.5,
                "self_regulation": 0.5,
                "comfort_bias": 0.5,
            },
            "infant_state": {
                "energy_level": 0.65,
                "satiety_level": 0.60,
                "security_level": 0.70,
                "stimulation_load": 0.25,
                "last_event_novelty": 0.20,
            },
        }

    def _clamp01(self, value):
        return max(0.0, min(1.0, float(value)))

    def _is_infant_brain_v2_active_for_agent(self, agent):
        cfg = self.config.get("npc_brain", {}) or {}
        if not bool(cfg.get("infant_brain_v2_enabled", False)):
            return False
        if agent is None:
            return False
        if int(getattr(agent, "age_months", 0)) > 35:
            return False
        temperament = getattr(agent, "temperament", None)
        return isinstance(temperament, dict) and len(temperament) > 0

    def _ensure_infant_brain_state(self, agent):
        if agent is None:
            return None
        if not isinstance(getattr(agent, "brain", None), dict):
            agent.brain = {}
        agent.brain.setdefault("infant_state", {})

        derived = temperament_to_infant_params(getattr(agent, "temperament", {}) or {})
        params = {key: self._clamp01(val) for key, val in derived.items()}
        agent.brain["infant_params"] = params

        state = agent.brain.get("infant_state", {}) or {}
        state.setdefault("energy_level", 0.65)
        state.setdefault("satiety_level", 0.60)
        state.setdefault("security_level", 0.70)
        state.setdefault("stimulation_load", 0.25)
        state.setdefault("last_event_novelty", 0.20)
        for key in ("energy_level", "satiety_level", "security_level", "stimulation_load", "last_event_novelty"):
            state[key] = self._clamp01(state.get(key, 0.0))
        agent.brain["infant_state"] = state
        return state

    def _update_infant_state_monthly(self, agent):
        """
        Deterministic monthly infant homeostasis update.
        Applies only while infant v2 is enabled and agent is in infancy.
        """
        if not self._is_infant_brain_v2_active_for_agent(agent):
            return
        state = self._ensure_infant_brain_state(agent)
        params = (agent.brain.get("infant_params", {}) or {})
        self_reg = self._clamp01(params.get("self_regulation", 0.5))
        novelty_tol = self._clamp01(params.get("novelty_tolerance", 0.5))
        comfort_bias = self._clamp01(params.get("comfort_bias", 0.5))

        state["energy_level"] = self._clamp01(
            (state["energy_level"] * 0.88)
            + (0.10 * comfort_bias)
            + (0.04 * self_reg)
            - (0.05 * state["stimulation_load"])
        )
        state["satiety_level"] = self._clamp01((state["satiety_level"] * 0.90) + 0.05)
        state["security_level"] = self._clamp01(
            (state["security_level"] * 0.90)
            + (0.06 * comfort_bias)
            - (0.03 * state["stimulation_load"])
        )
        state["stimulation_load"] = self._clamp01(
            (state["stimulation_load"] * 0.76)
            + (0.08 * state["last_event_novelty"])
            + (0.05 * (1.0 - self_reg))
            + (0.04 * max(0.0, novelty_tol - 0.5))
        )
        state["last_event_novelty"] = self._clamp01(state["last_event_novelty"] * 0.70)

        agent.brain["infant_state"] = state

    def _update_infant_state_after_choice(self, agent, choice):
        """
        Deterministic post-choice infant state transition.
        Uses infant appraisal and current derived infant parameters.
        """
        if not self._is_infant_brain_v2_active_for_agent(agent):
            return
        state = self._ensure_infant_brain_state(agent)
        params = (agent.brain.get("infant_params", {}) or {})
        appraisal = choice_to_infant_appraisal(choice)

        self_reg = self._clamp01(params.get("self_regulation", 0.5))
        threat = self._clamp01(params.get("threat_sensitivity", 0.5))
        energy_budget = self._clamp01(params.get("energy_budget", 0.5))

        energy_drop = appraisal["energy_cost"] * (0.45 + (0.40 * (1.0 - energy_budget)))
        energy_recover = appraisal["comfort_value"] * 0.08
        state["energy_level"] = self._clamp01(state["energy_level"] - energy_drop + energy_recover)

        satiety_delta = (0.06 * appraisal["comfort_value"]) + (0.02 * appraisal["social_soothing"]) - (0.04 * appraisal["energy_cost"])
        state["satiety_level"] = self._clamp01(state["satiety_level"] + satiety_delta)

        security_delta = (
            (0.16 * appraisal["comfort_value"])
            + (0.16 * appraisal["social_soothing"])
            + (0.10 * appraisal["familiarity"])
            - (0.28 * appraisal["safety_risk"] * (0.8 + (0.4 * threat)))
        )
        state["security_level"] = self._clamp01(state["security_level"] + security_delta)

        novelty_pressure = appraisal["novelty_load"] * (1.0 + (0.60 * (1.0 - self_reg)))
        soothe_buffer = (0.18 * appraisal["familiarity"]) + (0.14 * appraisal["social_soothing"])
        state["stimulation_load"] = self._clamp01(
            (state["stimulation_load"] * 0.65)
            + (0.50 * novelty_pressure)
            - soothe_buffer
        )
        state["last_event_novelty"] = self._clamp01(appraisal["novelty_load"])

        agent.brain["infant_state"] = state

    def _init_player_style_tracker(self):
        cfg = self.config.get("npc_brain", {}) or {}
        mimic_cfg = cfg.get("player_mimic", {}) or {}
        beta = float(mimic_cfg.get("ema_beta", 0.15))
        return default_player_style_tracker(beta=beta)

    def _update_player_style_tracker(self, observed_features):
        self.player_style_tracker = update_player_style_tracker(
            self.player_style_tracker,
            observed_features or {},
        )
        return self.player_style_tracker

    def _get_mimic_alpha(self, brain_profile, relationship_type=None):
        cfg = self.config.get("npc_brain", {}) or {}
        if not bool(cfg.get("player_mimic_enabled", False)):
            return 0.0
        if not isinstance(brain_profile, dict):
            return 0.0
        mimic = brain_profile.get("player_mimic", {}) or {}
        alpha = float(mimic.get("alpha", 0.0))
        rel_map = mimic.get("alpha_by_relation", {}) or {}
        if relationship_type is not None and relationship_type in rel_map:
            alpha = float(rel_map.get(relationship_type, alpha))
        return max(0.0, min(1.0, alpha))

    def get_effective_brain_weights(self, agent, relationship_type=None):
        """
        Returns blended effective weights for an agent using current player style tracker.
        """
        brain = getattr(agent, "brain", {}) or {}
        base = brain.get("base_weights", {}) or {}
        style = (self.player_style_tracker or {}).get("weights", {}) or {}
        alpha = self._get_mimic_alpha(brain, relationship_type=relationship_type)
        return blend_weights(base, style, alpha)

    def _create_npc(self, **kwargs):
        """Helper to instantiate, register, and return an NPC."""
        if "uid" not in kwargs:
            kwargs["uid"] = self._next_uid("npc")
        if "brain" not in kwargs:
            kwargs["brain"] = self._build_brain_profile(kwargs["uid"], is_player=False)
        agent = Agent(self.config["agent"], is_player=False, **kwargs)
        if hasattr(self, "agent_event_history") and isinstance(self.agent_event_history, dict):
            self.agent_event_history.setdefault(agent.uid, [])
        requested_age_months = int(kwargs.get("age_months", agent.age_months))
        if requested_age_months > 0:
            cfg = self.config.get("npc_brain", {}) or {}
            replay_enabled = (
                bool(cfg.get("enabled", False))
                and bool(cfg.get("events_enabled", False))
                and bool(cfg.get("infant_event_backfill_enabled", False))
            )
            callback = self._npc_infant_backfill_callback if replay_enabled else None
            agent.backfill_to_age_months(
                requested_age_months,
                world_seed=self.world_seed,
                infant_month_callback=callback,
            )
        self.npcs[agent.uid] = agent
        return agent

    def _get_event_manager_for_backfill(self):
        """
        Lazily construct event manager used by deterministic NPC infancy replay.
        """
        if self._event_manager_backfill is None:
            from .events import EventManager

            self._event_manager_backfill = EventManager(self.config)
        return self._event_manager_backfill

    def _npc_infant_backfill_callback(self, agent, age_months):
        """
        Per-month callback invoked by agent backfill to replay infancy events with NPC brain.
        """
        if not hasattr(self, "agent_event_history") or not isinstance(self.agent_event_history, dict):
            self.agent_event_history = {}
        history_store = self.agent_event_history.setdefault(getattr(agent, "uid", "unknown-agent"), [])
        manager = self._get_event_manager_for_backfill()
        manager.resolve_infant_event_for_agent_at_month(
            self,
            agent,
            int(age_months),
            history_store=history_store,
        )

    def _assign_job(self, npc):
        """Assigns a random suitable job to an NPC."""
        # Only assign if age >= 16
        if npc.age < 16: return
        
        jobs = self.config.get("economy", {}).get("jobs", [])
        if not jobs: return
        
        # No smarts filter anymore
        npc.job = random.choice(jobs)
        # Give them some savings based on age/salary
        years_worked = max(0, npc.age - 18)
        npc.money = int(npc.job['salary'] * years_worked * 0.1) # Saved 10%

    def _assign_initial_schooling(self, agent):
        """
        Checks if the agent should be in school based on age and enrolls them.
        This prevents 'Late Enrollment' logs when the first September hits.
        """
        if not self.school_system: return

        # Find the correct grade for their current age
        eligible_idx = -1
        
        for i, grade in enumerate(self.school_system.grades):
            if agent.age == grade["min_age"]:
                eligible_idx = i
                break
        
        # If they match a grade, enroll them silently
        if eligible_idx != -1:
            grade_data = self.school_system.grades[eligible_idx]
            form_label = self.school_system.get_random_form_label()
            
            agent.school = {
                "school_id": self.school_system.id,
                "school_name": self.school_system.name,
                "stage": grade_data["stage"],
                "year_index": eligible_idx,
                "year_label": grade_data["name"],
                "form_label": form_label,
                "performance": 50, # Start average
                "is_in_session": True, # Assume school is active
                "attendance_months_total": 0,
                "attendance_months_present_equiv": 0.0
            }
            agent.sync_subjects_with_school(self.school_system, preserve_existing=True)

    def _setup_family_and_player(self):
        """
        Procedurally generates the family tree for the player.
        Wrapper around the generic lineage factory.
        """
        agent_conf = self.config["agent"]
        initial_age = agent_conf.get("initial_age", 0)
        
        # Generate the player and their entire family tree
        return self._generate_lineage_structure(
            target_age=initial_age,
            is_player=True
        )

    def _generate_lineage_structure(self, target_age, is_player=False, fixed_last_name=None, fixed_city=None, fixed_country=None):
        """
        Generic factory to generate a full family tree (GPs -> Parents -> Child).
        Returns the focus child (target_age).
        """
        agent_conf = self.config["agent"]
        repro_conf = self.config.get("reproduction", {})
        
        # 1. Determine Ages (Backwards from Target)
        # Parents
        father_age = target_age + self._get_reproductive_gap(repro_conf)
        mother_age = target_age + self._get_reproductive_gap(repro_conf)
        
        # Grandparents
        p_gpa_age = father_age + self._get_reproductive_gap(repro_conf)
        p_gma_age = father_age + self._get_reproductive_gap(repro_conf)
        m_gpa_age = mother_age + self._get_reproductive_gap(repro_conf)
        m_gma_age = mother_age + self._get_reproductive_gap(repro_conf)
        
        # Shared Bio Data
        # Use fixed values if provided (e.g. for classmates in same city), else random
        last_name = fixed_last_name if fixed_last_name else random.choice(agent_conf["bio"].get("last_names", ["Doe"]))
        country = fixed_country if fixed_country else random.choice(agent_conf["bio"].get("countries", ["Unknown"]))
        city = fixed_city if fixed_city else random.choice(agent_conf["bio"].get("cities", ["Unknown"]))
        
        # --- Generation 2: Grandparents (Lineage Heads) ---
        # Paternal
        p_gpa = self._create_npc(age=p_gpa_age, gender="Male", last_name=last_name, city=city, country=country)
        p_gma = self._create_npc(age=p_gma_age, gender="Female", last_name=last_name, city=city, country=country)
        
        self._link_agents(p_gpa, p_gma, "Spouse", "Spouse", mod_name="Marriage", mod_val=60)
        
        # Maternal
        # Maternal side often has different last name (Grandfather's name)
        mat_last_name = random.choice(agent_conf["bio"].get("last_names", ["Smith"]))
        m_gpa = self._create_npc(age=m_gpa_age, gender="Male", last_name=mat_last_name, city=city, country=country)
        m_gma = self._create_npc(age=m_gma_age, gender="Female", last_name=mat_last_name, city=city, country=country)
        
        self._link_agents(m_gpa, m_gma, "Spouse", "Spouse", mod_name="Marriage", mod_val=60)
        
        # --- Generation 1: Parents & Aunts/Uncles ---
        
        # 1. Father
        father = self._create_npc(age=father_age, gender="Male", parents=(p_gpa, p_gma), 
                                  last_name=last_name, city=city, country=country)
        self._assign_job(father)
        self._link_parent_child(p_gpa, p_gma, father)

        # 2. Mother
        mother = self._create_npc(age=mother_age, gender="Female", parents=(m_gpa, m_gma),
                                  last_name=mat_last_name, city=city, country=country)
        self._assign_job(mother)
        self._link_parent_child(m_gpa, m_gma, mother)

        # 3. Link Parents
        self._link_agents(father, mother, "Spouse", "Spouse", mod_name="Marriage", mod_val=60)

        # 4. Paternal Aunts/Uncles
        self._generate_siblings_for(father, p_gpa, p_gma, repro_conf, city, country, last_name, in_law=mother)
        
        # 5. Maternal Aunts/Uncles
        self._generate_siblings_for(mother, m_gpa, m_gma, repro_conf, city, country, mat_last_name, in_law=father)

        # --- Bridge Grandparents ---
        # In-Law Link (Civil +10)
        self._link_agents(p_gpa, m_gpa, "In-Law", "In-Law", mod_name="Civil", mod_val=10)
        self._link_agents(p_gpa, m_gma, "In-Law", "In-Law", mod_name="Civil", mod_val=10)
        self._link_agents(p_gma, m_gpa, "In-Law", "In-Law", mod_name="Civil", mod_val=10)
        self._link_agents(p_gma, m_gma, "In-Law", "In-Law", mod_name="Civil", mod_val=10)

        # --- Generation 0: Focus Child & Siblings ---
        
        # 1. Focus Child (Player or NPC)
        if is_player:
            player_uid = self._next_uid("player")
            child = Agent(agent_conf, is_player=True, parents=(father, mother),
                          uid=player_uid,
                          brain=self._build_brain_profile(player_uid, is_player=True),
                          age=target_age, last_name=last_name, city=city, country=country,
                          time_config=self.config.get("time_management", {}))
            if target_age > 0:
                child.backfill_to_age(target_age, world_seed=self.world_seed)
        else:
            # For NPCs, we use _create_npc to register them in self.npcs
            child = self._create_npc(age=target_age, parents=(father, mother),
                                     last_name=last_name, city=city, country=country)
            self._assign_initial_schooling(child)
            self._assign_job(child)

        self._link_parent_child(father, mother, child)
        
        # 2. Siblings
        # Note: is_player_gen=True prevents infinite recursion of cousins-of-cousins
        self._generate_siblings_for(child, father, mother, repro_conf, city, country, last_name, is_player_gen=True)
        
        return child

    def _link_parent_child(self, father, mother, child):
        """Links a child to both parents with Parental Bond."""
        self._link_agents(child, father, "Father", "Child", mod_name="Paternal Bond", mod_val=80)
        self._link_agents(child, mother, "Mother", "Child", mod_name="Maternal Bond", mod_val=80)

    def _generate_siblings_for(self, focal_child, father, mother, repro_conf, city, country, last_name, is_player_gen=False, in_law=None):
        """Generates siblings and links them."""
        prob = repro_conf.get("sibling_prob_base", 0.25)
        decay = repro_conf.get("sibling_prob_decay", 0.5)
        min_rep = repro_conf.get("min_reproductive_age", 16)
        
        while random.random() < prob:
            gap = self._get_reproductive_gap(repro_conf)
            sib_age = mother.age - gap
            
            if sib_age < 0:
                prob *= decay
                continue
                
            sib = self._create_npc(age=sib_age, parents=(father, mother),
                                   last_name=last_name, city=city, country=country)
            self._link_parent_child(father, mother, sib)
            
            # Link to Focal Child (Sibling Bond)
            self._link_agents(focal_child, sib, "Sibling", "Sibling", mod_name="Sibling Bond", mod_val=30)

            # Link to In-Law
            if in_law:
                type_sib = "Brother-in-Law" if sib.gender == "Male" else "Sister-in-Law"
                type_il = "Brother-in-Law" if in_law.gender == "Male" else "Sister-in-Law"
                self._link_agents(sib, in_law, type_il, type_sib, mod_name="Civil", mod_val=10)
            
            self._assign_initial_schooling(sib)
            self._assign_job(sib)
            
            if not is_player_gen and sib.age >= min_rep:
                self._generate_cousins_for(sib, repro_conf, city, country)

            prob *= decay

    def _generate_cousins_for(self, aunt_uncle, repro_conf, city, country):
        """Decides if an Aunt/Uncle has a family."""
        cousin_prob = repro_conf.get("cousin_prob_base", 0.5)
        
        if random.random() < cousin_prob:
            # 1. Spouse
            spouse_age = aunt_uncle.age + random.randint(-5, 5)
            spouse_last = random.choice(self.config["agent"]["bio"].get("last_names", ["Jones"]))
            
            spouse = self._create_npc(age=spouse_age, gender="Female" if aunt_uncle.gender == "Male" else "Male",
                                      last_name=spouse_last, city=city, country=country)
            self._assign_job(spouse)
            
            self._link_agents(aunt_uncle, spouse, "Spouse", "Spouse", mod_name="Marriage", mod_val=60)
            
            # 2. First Cousin
            father = aunt_uncle if aunt_uncle.gender == "Male" else spouse
            mother = aunt_uncle if aunt_uncle.gender == "Female" else spouse
            
            gap = self._get_reproductive_gap(repro_conf)
            c1_age = mother.age - gap
            
            if c1_age >= 0:
                c1 = self._create_npc(age=c1_age, parents=(father, mother),
                                      last_name=father.last_name, city=city, country=country)
                self._link_parent_child(father, mother, c1)
                self._assign_initial_schooling(c1)
                self._assign_job(c1)
                
                self._generate_siblings_for(c1, father, mother, repro_conf, city, country, father.last_name, is_player_gen=True)

    def _link_agents(self, a, b, type_a_to_b, type_b_to_a, mod_name=None, mod_val=0):
        """
        Bi-directional relationship linking using the new Relationship class.
        Calculates base affinity and applies the structural modifier.
        """
        # 1. Calculate Base Affinity (The Gravity)
        aff_score = affinity.calculate_affinity(a, b)
        
        # 2. Create Relationship A -> B
        rel_a = Relationship(a.uid, b.uid, type_a_to_b, aff_score, b.first_name, b.is_alive)
        if mod_name:
            rel_a.add_modifier(mod_name, mod_val)
        a.relationships[b.uid] = rel_a
        
        # 3. Create Relationship B -> A
        rel_b = Relationship(b.uid, a.uid, type_b_to_a, aff_score, a.first_name, a.is_alive)
        if mod_name:
            rel_b.add_modifier(mod_name, mod_val)
        b.relationships[a.uid] = rel_b
        
        # 4. Store original affinity for family relationships to allow recalculation
        if type_a_to_b in ['Parent', 'Mother', 'Father', 'Child'] or type_b_to_a in ['Parent', 'Mother', 'Father', 'Child']:
            rel_a._original_affinity = aff_score
            rel_b._original_affinity = aff_score

    def _update_family_relationships_for_personality(self, agent):
        """
        Updates family relationships to use personality-based affinity when a child develops personality.
        This replaces the neutral infant affinity with calculated personality compatibility.
        """
        # Find all family relationships for this agent
        family_types = ['Parent', 'Mother', 'Father', 'Child', 'Sibling']
        
        for uid, rel in agent.relationships.items():
            if rel.rel_type in family_types and hasattr(rel, '_original_affinity'):
                # Get the other agent
                other_agent = self.npcs.get(uid)
                if not other_agent:
                    continue
                
                # Both agents now have personalities, calculate new affinity
                if agent.personality is not None and other_agent.personality is not None:
                    # Calculate new affinity based on personalities
                    new_affinity = affinity.calculate_affinity(agent, other_agent)
                    
                    # Update the base affinity
                    old_base = rel.base_affinity
                    rel.base_affinity = new_affinity
                    
                    # Recalculate total score
                    rel.recalculate()
                    
                    # Log the change for player
                    if agent.is_player:
                        change = new_affinity - old_base
                        change_text = f"+{change}" if change >= 0 else str(change)
                        self.add_log(f"Relationship with {rel.rel_type} {other_agent.first_name} base affinity changed: {old_base} → {new_affinity} ({change_text})", constants.COLOR_LOG_POSITIVE)
                
                # Also update the reverse relationship
                reverse_rel = other_agent.relationships.get(agent.uid)
                if reverse_rel and hasattr(reverse_rel, '_original_affinity'):
                    if agent.personality is not None and other_agent.personality is not None:
                        new_affinity = affinity.calculate_affinity(other_agent, agent)
                        reverse_rel.base_affinity = new_affinity
                        reverse_rel.recalculate()

    def start_new_year(self, age):
        """Finalizes the current year and starts a new one."""
        # Archive current year (collapse it by default)
        self.current_year_data["expanded"] = False
        self.history.append(self.current_year_data)
        
        # Start new year
        self.current_year_data = {
            "header": (f"--- Age {age} ---", constants.COLOR_LOG_HEADER),
            "events": [],
            "expanded": True
        }

    def add_log(self, message: str, color=None):
        """Adds a message to the current year's event log."""
        if color is None:
            color = constants.COLOR_TEXT
        self.current_year_data["events"].append((message, color))
        
    def get_flat_log_for_rendering(self):
        """
        Returns a flat list of (text, color, indent_level, is_header, year_index) 
        for the UI to render.
        """
        flat = []
        
        # 1. Past Years
        for i, year in enumerate(self.history):
            # Header
            flat.append({
                "text": year["header"][0],
                "color": year["header"][1],
                "indent": 0,
                "is_header": True,
                "index": i,
                "expanded": year["expanded"]
            })
            # Events (if expanded)
            if year["expanded"]:
                for msg, col in year["events"]:
                    flat.append({
                        "text": msg,
                        "color": col,
                        "indent": 20,
                        "is_header": False,
                        "index": None
                    })
                    
        # 2. Current Year (Always show header + events)
        curr = self.current_year_data
        flat.append({
            "text": curr["header"][0],
            "color": curr["header"][1],
            "indent": 0,
            "is_header": True,
            "index": "CURRENT", # Special marker
            "expanded": curr["expanded"]
        })
        if curr["expanded"]:
            for msg, col in curr["events"]:
                flat.append({
                    "text": msg,
                    "color": col,
                    "indent": 20,
                    "is_header": False,
                    "index": None
                })
                
        return flat
        
    def toggle_year(self, index):
        """Toggles the expansion state of a historical year."""
        if index == "CURRENT":
            self.current_year_data["expanded"] = not self.current_year_data["expanded"]
        elif 0 <= index < len(self.history):
            self.history[index]["expanded"] = not self.history[index]["expanded"]
