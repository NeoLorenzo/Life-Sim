# life_sim/simulation/agent.py
"""
Agent model module.
Holds the `Agent` entity and its behavior.
"""
import logging
import math
import random
import uuid
import copy
from .. import constants
from . import school, affinity
from .social import Relationship # Import new class
from .brain import CANONICAL_FEATURE_KEYS, DEFAULT_BASE_WEIGHTS

class Agent:
    """
    Represents a human entity (Player or NPC).
    
    Data Contract:
        Inputs: config dictionary (agent section), **kwargs for overrides
        State: age_months, health, happiness, smarts, looks, relationships, inventory
    """
    def __init__(self, agent_config: dict, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.uid = kwargs.get("uid", str(uuid.uuid4()))
        self.is_player = kwargs.get("is_player", False)
        self.brain = copy.deepcopy(
            kwargs.get(
                "brain",
                {
                    "version": "phase2_scaffold_v1",
                    "enabled": False,
                    "events_enabled": False,
                    "ap_enabled": False,
                    "player_mimic_enabled": False,
                    "drives": {
                        "comfort": 0.5,
                        "achievement": 0.5,
                        "social": 0.5,
                        "risk_avoidance": 0.5,
                        "novelty": 0.5,
                        "discipline": 0.5,
                    },
                    "decision_style": {
                        "temperature": 1.0,
                        "inertia": 0.5,
                        "noise": 0.1,
                    },
                    "player_mimic": {
                        "alpha": 0.0,
                    },
                    "base_weights": dict(DEFAULT_BASE_WEIGHTS),
                    "player_style_weights": {k: 0.0 for k in CANONICAL_FEATURE_KEYS},
                    "history": {
                        "event_decisions": 0,
                        "ap_decisions": 0,
                    },
                },
            )
        )
        self._ensure_brain_contract()
        
        # Form attribute (single character string, default: None)
        self.form = kwargs.get("form", None)
        
        # Allow kwargs to override config defaults (for NPCs)
        # AGE CHANGE: Input is years, store as months
        initial_age_years = kwargs.get("age", agent_config.get("initial_age", 0))
        self.age_months = initial_age_years * 12
        
        # Randomize birth month for NPCs so they don't all share the player's birthday
        if not self.is_player:
            self.age_months += random.randint(0, 11)
        
        self.health = kwargs.get("health", agent_config.get("initial_health", 50))
        self.max_health = constants.HEALTH_PRIME_VALUE # Capacity starts at 100
        self.happiness = kwargs.get("happiness", agent_config.get("initial_happiness", 50))
        
        self.looks = kwargs.get("looks", agent_config.get("initial_looks", 50))
        self.money = kwargs.get("money", agent_config.get("initial_money", 0))
        
        self._recalculate_max_health()

        self.job = None  # None or dict {"title": str, "salary": int}
        self.school = None # None or dict { "system": str, "grade_index": int, "performance": int, "is_in_session": bool }
        self.is_alive = True
        
        # --- Biography ---
        bio_conf = agent_config.get("bio", {})
        
        # Gender: Use kwarg if provided, else random
        self.gender = kwargs.get("gender", random.choice(["Male", "Female"]))
        
        # First Name: Use kwarg if provided, else random based on gender
        if "first_name" in kwargs:
            self.first_name = kwargs["first_name"]
        elif self.gender == "Male":
            self.first_name = random.choice(bio_conf.get("first_names_male", ["John"]))
        else:
            self.first_name = random.choice(bio_conf.get("first_names_female", ["Jane"]))
            
        # Last Name, Country, City: Use kwarg if provided (e.g. inherit from parents), else random
        self.last_name = kwargs.get("last_name", random.choice(bio_conf.get("last_names", ["Doe"])))
        self.country = kwargs.get("country", random.choice(bio_conf.get("countries", ["Unknown"])))
        self.city = kwargs.get("city", random.choice(bio_conf.get("cities", ["Unknown"])))
        
        # --- Appearance & Genetics ---
        self.parents = kwargs.get("parents", None) # Tuple (Father, Mother) or None
        app_conf = agent_config.get("appearance", {})
        
        # Aptitudes Initialization (moved after parents are set)
        self._init_aptitudes(agent_config)
        
        if self.parents:
            self._init_descendant(app_conf)
        else:
            self._init_lineage_head(app_conf)
        
        # Initial Height Calculation (based on start age)
        if self.age >= 20:
            self.height_cm = self.genetic_height_potential
        elif self.age == 0:
            self.height_cm = 50 # Average newborn
        else:
            # Rough linear interpolation for starting mid-childhood
            progress = self.age / 20.0
            self.height_cm = 50 + int((self.genetic_height_potential - 50) * progress)

        self.weight_kg = 0 # Will be calculated by _recalculate_physique

        # --- Genetic Base Attributes (Set Once) ---
        attr_config = agent_config.get("attributes", {})
        
        # Body frame size: 0.8=small, 1.0=medium, 1.2=large frame
        self.body_frame_size = random.uniform(attr_config.get("body_frame_size_min", 0.8), 
                                             attr_config.get("body_frame_size_max", 1.2))
        
        # Muscle fiber composition: % fast-twitch fibers (30-70%)
        self.muscle_fiber_composition = random.uniform(attr_config.get("muscle_fiber_composition_min", 30),
                                                       attr_config.get("muscle_fiber_composition_max", 70))
        
        # Genetic aerobic capacity (VO2 max potential)
        self.aerobic_capacity_genetic = random.uniform(attr_config.get("aerobic_capacity_genetic_min", 40),
                                                      attr_config.get("aerobic_capacity_genetic_max", 80))
        
        # Flexibility and reaction time remain as genetic base attributes
        self.flexibility = self._rand_attr(attr_config, "flexibility")
        self.reaction_time = self._rand_attr(attr_config, "reaction_time")
        
        # --- Dynamic Physical Attributes (Calculated) ---
        # These will be calculated by _recalculate_physical_attributes()
        self.maximal_strength = 0
        self.strength_endurance = 0
        self.max_speed = 0
        self.acceleration = 0
        self.explosive_power = 0
        self.cardiovascular_endurance = 0
        self.muscular_endurance = 0
        self.balance = 0
        self.coordination = 0
        self.agility = 0
        
        # Genotype: The genetic peak potential (0-100)
        self._genetic_fertility_peak = self._rand_attr(attr_config, "fertility")
        self._genetic_libido_peak = self._rand_attr(attr_config, "libido")
        
        # Phenotype: Current expressed value (starts at 0 for babies)
        self.fertility = 0
        self.libido = 0

        # Derived Bio-Metrics (Simple approximation based on genetic aerobic capacity)
        # Base BF: Men ~25%, Women ~35%. Higher aerobic capacity reduces this.
        base_bf = 25.0 if self.gender == "Male" else 35.0
        reduction = (self.aerobic_capacity_genetic / 100.0) * 18.0 # Up to 18% reduction
        variance = random.uniform(-3.0, 5.0)
        self.body_fat = max(4.0, round(base_bf - reduction + variance, 1))
        
        # Initialize dynamic physique stats
        self.lean_mass = 0
        self.weight_kg = 0
        self.bmi = 0
        
        # Calculate initial phenotype based on age
        self._recalculate_hormones()
        self._recalculate_physique()
        self._recalculate_physical_attributes()
        
        # Temperament System
        if self.age < 3:
            # Young children have temperament traits, no Big 5 personality yet
            self.temperament = self._generate_infant_temperament()
            self.plasticity = 1.0
            self.is_personality_locked = False
            self.personality = None
        else:
            # Age 3+ have Big 5 personality, no temperament
            self.temperament = None
            self.plasticity = 0.0
            self.is_personality_locked = True
            # Personality (Big 5 Model)
            # Structure: { "Main": { "Facet": Value, ... }, ... }
            self.personality = self._generate_big_five(attr_config)
        
        # --- Academic Subjects ---
        # Populated dynamically from school curriculum when enrolled.
        self.subjects = {}
        
        self.religiousness = self._rand_attr(attr_config, "religiousness")
        
        # Hidden
        self.sexuality = random.choice(["Heterosexual", "Homosexual", "Bisexual"]) # Simplified for MVP

        # --- Skills ---
        # Dictionary mapping Skill Name -> Level (0-100)
        self.skills = {} 
        
        # --- Social & Inventory ---
        # {uid: {"type": str, "value": int, "name": str}}
        self.relationships = {} 
        self.inventory = []

        # --- Time Management (AP) ---
        self.ap_max = constants.AP_MAX_DAILY
        self.ap_used = 0.0
        self.ap_locked = 0.0 # School/Work
        self.ap_sleep = constants.AP_SLEEP_DEFAULT  # Default
        
        # Schedule Preferences
        self.target_sleep_hours = self.ap_sleep
        self.attendance_rate = 1.0
        self._temp_cognitive_penalty = 0.0
        
        # Calculate initial sleep needs if config provided
        time_config = kwargs.get("time_config", {})
        self._recalculate_ap_needs(time_config)

        # Dashboard Customization (Default Pinned Stats)
        self.pinned_attributes = [
            "Health", "Happiness", "IQ", "Looks", "Energy", "Fitness"
        ]

        self.logger.info(f"Agent initialized ({'Player' if self.is_player else 'NPC'}): {self.first_name} {self.last_name} ({self.gender}) Age {self.age}")
        
        # Recalculate aptitudes based on age development curves
        self._recalculate_aptitudes()

    def _ensure_brain_contract(self):
        """
        Backward-compatible brain schema normalization.
        Adds phase-2 infant-v2 scaffold keys without changing active behavior.
        """
        if not isinstance(self.brain, dict):
            self.brain = {}

        self.brain.setdefault("version", "phase2_scaffold_v1")
        self.brain.setdefault("enabled", False)
        self.brain.setdefault("events_enabled", False)
        self.brain.setdefault("ap_enabled", False)
        self.brain.setdefault("player_mimic_enabled", False)
        self.brain.setdefault("drives", {})
        self.brain.setdefault("decision_style", {})
        self.brain.setdefault("player_mimic", {})
        self.brain.setdefault("base_weights", dict(DEFAULT_BASE_WEIGHTS))
        self.brain.setdefault("player_style_weights", {k: 0.0 for k in CANONICAL_FEATURE_KEYS})
        self.brain.setdefault("history", {})

        drives = self.brain.get("drives", {}) or {}
        for key in ("comfort", "achievement", "social", "risk_avoidance", "novelty", "discipline"):
            drives.setdefault(key, 0.5)
        self.brain["drives"] = drives

        decision_style = self.brain.get("decision_style", {}) or {}
        decision_style.setdefault("temperature", 1.0)
        decision_style.setdefault("inertia", 0.5)
        decision_style.setdefault("noise", 0.1)
        self.brain["decision_style"] = decision_style

        player_mimic = self.brain.get("player_mimic", {}) or {}
        player_mimic.setdefault("alpha", 0.0)
        self.brain["player_mimic"] = player_mimic

        history = self.brain.get("history", {}) or {}
        history.setdefault("event_decisions", 0)
        history.setdefault("ap_decisions", 0)
        self.brain["history"] = history

        # Phase 2 infant-v2 scaffold: data contract only, no selection logic use yet.
        self.brain.setdefault("infant_brain_version", "v2_spec_2026_02")
        self.brain.setdefault("infant_brain_v2_enabled", False)
        self.brain.setdefault("infant_params", {})
        self.brain.setdefault("infant_state", {})

        infant_params = self.brain.get("infant_params", {}) or {}
        infant_params.setdefault("novelty_tolerance", 0.5)
        infant_params.setdefault("threat_sensitivity", 0.5)
        infant_params.setdefault("energy_budget", 0.5)
        infant_params.setdefault("self_regulation", 0.5)
        infant_params.setdefault("comfort_bias", 0.5)
        self.brain["infant_params"] = infant_params

        infant_state = self.brain.get("infant_state", {}) or {}
        infant_state.setdefault("energy_level", 0.65)
        infant_state.setdefault("satiety_level", 0.60)
        infant_state.setdefault("security_level", 0.70)
        infant_state.setdefault("stimulation_load", 0.25)
        infant_state.setdefault("last_event_novelty", 0.20)
        self.brain["infant_state"] = infant_state

    def _init_aptitudes(self, agent_config):
        """Initialize aptitudes with proper heritability from parents or random generation."""
        self.aptitudes = {}
        
        # Get heritability standard deviation from config
        heritability_sd = agent_config.get('aptitudes', {}).get('heritability_sd', 10)
        
        if self.parents is None:
            # Lineage Head: Random generation
            for aptitude in constants.APTITUDES:
                val = int(random.gauss(100, 15))  # mean 100, sd 15
                val = max(constants.APTITUDE_MIN, min(constants.APTITUDE_MAX, val))  # Clamp to bounds
                self.aptitudes[aptitude] = {
                    "genotype": val,
                    "phenotype": val,
                    "plasticity": 1.0
                }
        else:
            # Descendant: Inherit from parents with variance
            father, mother = self.parents
            
            for aptitude in constants.APTITUDES:
                # Calculate mid-parent genotype
                mid_parent = (father.aptitudes[aptitude]['genotype'] + mother.aptitudes[aptitude]['genotype']) / 2
                
                # Add heritability variance
                genotype = mid_parent + random.gauss(0, heritability_sd)
                
                # Clamp to valid range
                genotype = max(constants.APTITUDE_MIN, min(constants.APTITUDE_MAX, genotype))
                
                self.aptitudes[aptitude] = {
                    "genotype": int(genotype),
                    "phenotype": int(genotype),  # Set phenotype to genotype for now
                    "plasticity": 1.0
                }

    def _init_lineage_head(self, app_conf):
        """Generates traits stochastically (First Generation)."""
        # 1. Pigmentation (Random from config)
        self.eye_color = random.choice(app_conf.get("eye_colors", ["Brown"]))
        self.hair_color = random.choice(app_conf.get("hair_colors", ["Brown"]))
        self.skin_tone = random.choice(app_conf.get("skin_tones", ["Fair"]))
        
        # Form attribute (single character string, default: None)
        self.form = None
        
        # 2. Height (Gaussian Distribution)
        genetics_config = app_conf.get("genetics", {})
        if self.gender == "Male":
            mu, sigma = genetics_config.get("height_male_mean", 176), genetics_config.get("height_male_sd", 7)
        else:
            mu, sigma = genetics_config.get("height_female_mean", 163), genetics_config.get("height_female_sd", 6)
            
        self.genetic_height_potential = int(random.gauss(mu, sigma))
        # Clamp to realistic extremes
        self.genetic_height_potential = max(genetics_config.get("height_min", 140), min(genetics_config.get("height_max", 215), self.genetic_height_potential))

    def _init_descendant(self, app_conf):
        """Inherits traits from parents (Next Generation)."""
        father, mother = self.parents
        
        # 1. Height (Mid-Parental Formula)
        # Male Child = ((Mother + 13) + Father) / 2
        # Female Child = ((Father - 13) + Mother) / 2
        # Add random variance (+/- 10cm)
        genetics_config = app_conf.get("genetics", {})
        parent_adjustment = genetics_config.get("height_parent_adjustment", 13)
        if self.gender == "Male":
            base = ((mother.genetic_height_potential + parent_adjustment) + father.genetic_height_potential) / 2
        else:
            base = ((father.genetic_height_potential - parent_adjustment) + mother.genetic_height_potential) / 2
            
        variance = random.gauss(0, 5) # Standard deviation of 5cm from predicted
        self.genetic_height_potential = int(base + variance)

        # 2. Skin Tone (Blending)
        # Assumes config list is ordered Light -> Dark
        tones = app_conf.get("skin_tones", ["Pale", "Fair", "Olive", "Brown", "Dark"])
        try:
            f_idx = tones.index(father.skin_tone)
            m_idx = tones.index(mother.skin_tone)
            
            # Average index with slight variance
            avg_idx = (f_idx + m_idx) / 2
            # 20% chance to drift one shade lighter or darker
            drift = 0
            if random.random() < 0.2:
                drift = random.choice([-1, 1])
            
            final_idx = int(round(avg_idx + drift))
            final_idx = max(0, min(len(tones) - 1, final_idx))
            self.skin_tone = tones[final_idx]
        except ValueError:
            # Fallback if parents have custom skin tones not in config
            self.skin_tone = random.choice([father.skin_tone, mother.skin_tone])

        # 3. Eyes & Hair (Probabilistic Inheritance)
        # 45% Dad, 45% Mom, 10% Mutation (Grandparents/Recessive)
        def inherit(p_attr, m_attr, pool):
            roll = random.random()
            if roll < 0.45: return p_attr
            elif roll < 0.90: return m_attr
            else: return random.choice(pool)

        self.eye_color = inherit(father.eye_color, mother.eye_color, app_conf.get("eye_colors", []))
        self.hair_color = inherit(father.hair_color, mother.hair_color, app_conf.get("hair_colors", []))
        
        # Form attribute (single character string, default: None)
        self.form = None

    def get_attr_value(self, name):
        """Helper to fetch attribute values by string name."""
        # Core
        if name == "Health": return self.health
        if name == "Max Health": return self.max_health
        if name == "Happiness": return self.happiness
        if name == "IQ": return self.iq
        if name == "Looks": return self.looks
        if name == "Money": return self.money
        
        # Aptitudes (with cognitive penalties)
        if name in constants.APTITUDES:
            return self.get_effective_aptitude(name)
        
        # Physical
        if name == "Energy": return self.muscular_endurance
        if name == "Fitness": return self.cardiovascular_endurance
        if name == "Strength": return self.maximal_strength
        if name == "Fertility": return self.fertility
        if name == "Genetic Fertility": return self._genetic_fertility_peak
        if name == "Libido": return self.libido
        if name == "Genetic Libido": return self._genetic_libido_peak
        
        # New Physical Attributes
        if name == "Maximal Strength": return self.maximal_strength
        if name == "Strength Endurance": return self.strength_endurance
        if name == "Max Speed": return self.max_speed
        if name == "Speed": return self.max_speed  # Backward compatibility
        if name == "Acceleration": return self.acceleration
        if name == "Explosive Power": return self.explosive_power
        if name == "Power": return self.explosive_power  # Backward compatibility
        if name == "Cardiovascular Endurance": return self.cardiovascular_endurance
        if name == "Muscular Endurance": return self.muscular_endurance
        if name == "Endurance": return self.muscular_endurance  # Backward compatibility
        if name == "Balance": return self.balance
        if name == "Coordination": return self.coordination
        if name == "Agility": return self.agility
        if name == "Reaction Time": return self.reaction_time
        if name == "Flexibility": return self.flexibility
        
        # Backward compatibility for old attribute names
        if name == "Athleticism": return self.cardiovascular_endurance
        
        # Big 5 (Sums)
        if self.personality and name in self.personality:
            return self.get_personality_sum(name)
            
        # Big 5 (Facets) - Search inside the nested dicts
        if self.personality:
            for trait, facets in self.personality.items():
                if name in facets:
                    return facets[name]

        # Hidden/Other
        if name == "Religiousness": return self.religiousness
        
        # Academic Subjects
        if name in self.subjects:
            return self.subjects[name]["current_grade"]
        
        # Temperament (for infants)
        if self.temperament and name in self.temperament:
            return self.temperament[name]
        
        return 0

    def get_effective_aptitude(self, name):
        """Get aptitude value with cognitive penalties applied."""
        if name not in self.aptitudes:
            return 0
        
        base = self.aptitudes[name]["phenotype"]
        effective = base * (1.0 - self._temp_cognitive_penalty)
        return int(effective)

    @property
    def age(self):
        """Returns age in years (integer)."""
        return self.age_months // 12

    @property
    def iq(self):
        """Returns the integer average of all aptitude phenotype values."""
        if not hasattr(self, 'aptitudes') or not self.aptitudes:
            return 100  # Fallback for agents without aptitudes
        total = sum(apt_data["phenotype"] for apt_data in self.aptitudes.values())
        return int(total / len(self.aptitudes))
    
    @iq.setter
    def iq(self, value):
        """Prevent direct setting of IQ - legacy compatibility only."""
        pass  # Do nothing - IQ is now derived from aptitudes

    def _recalculate_max_health(self):
        """
        Calculates health cap based on age using a 3-stage 'Prime of Life' curve.
        1. Childhood (0-20): Grows from 70 to 100.
        2. Prime (20-50): Stays at 100.
        3. Senescence (50-100): Decays quadratically to 0.
        """
        if self.age < constants.HEALTH_CHILDHOOD_MAX_AGE:
            # Growth Phase: 70 base + 1.5 per year
            self.max_health = int(constants.HEALTH_BASE_CHILD + (constants.HEALTH_GROWTH_RATE * self.age))
        elif self.age < constants.HEALTH_PRIME_MAX_AGE:
            # Prime Phase
            self.max_health = constants.HEALTH_PRIME_VALUE
        else:
            # Senescence Phase: 100 - ((age - 50)^2 / 25)
            decay = ((self.age - constants.HEALTH_PRIME_MAX_AGE) ** 2) / constants.HEALTH_SENESCENCE_DIVISOR
            self.max_health = int(max(0, constants.HEALTH_PRIME_VALUE - decay))

        # Ensure current health never exceeds the new cap
        if self.health > self.max_health:
            self.health = self.max_health
        
        # Recalculate aptitudes based on age development curves
        self._recalculate_aptitudes()

    def _recalculate_aptitudes(self):
        """Recalculate aptitude phenotypes based on age and development curves."""
        # Safety check - if aptitudes don't exist yet, skip
        if not hasattr(self, 'aptitudes') or not self.aptitudes:
            return
        # Load development curves from config (using a default if not available)
        # For now, we'll use hardcoded curves since this is called during Agent initialization
        # before we have access to the full config. This will be improved later.
        development_curves = {
            "fluid": [[0, 0.2], [10, 0.8], [20, 1.0], [60, 0.9], [90, 0.7]],
            "crystallized": [[0, 0.1], [15, 0.6], [30, 0.9], [50, 1.0], [90, 0.95]]
        }
        
        # Map aptitudes to their development curve types
        aptitude_curves = {
            "Analytical Reasoning": "fluid",      # Analytical reasoning
            "Verbal Abilities": "crystallized", # Verbal abilities  
            "Spatial Abilities": "fluid",      # Spatial abilities
            "Working Memory": "fluid",    # Working memory
            "Long-term Memory": "crystallized", # Long-term memory
            "Secondary Cognitive": "crystallized"  # Secondary cognitive abilities
        }
        
        def interpolate_curve(curve, age):
            """Interpolate multiplier from age-based development curve."""
            if not curve:
                return 1.0
            
            # Find the two points to interpolate between
            for i in range(len(curve) - 1):
                age_point, multiplier = curve[i]
                next_age, next_multiplier = curve[i + 1]
                
                if age <= age_point:
                    return multiplier
                elif age < next_age:
                    # Linear interpolation between points
                    progress = (age - age_point) / (next_age - age_point)
                    return multiplier + progress * (next_multiplier - multiplier)
            
            # If age is beyond the last point, return the last multiplier
            return curve[-1][1]
        
        # Update each aptitude's phenotype based on development curve
        for aptitude, data in self.aptitudes.items():
            genotype = data["genotype"]
            curve_type = aptitude_curves.get(aptitude, "fluid")
            curve = development_curves.get(curve_type, [])
            
            # Get age multiplier
            multiplier = interpolate_curve(curve, self.age)
            
            # Calculate target phenotype
            target_phenotype = int(genotype * multiplier)
            
            # Clamp to valid range
            target_phenotype = max(constants.APTITUDE_MIN, min(constants.APTITUDE_MAX, target_phenotype))
            
            # Update phenotype
            self.aptitudes[aptitude]["phenotype"] = target_phenotype

    def _get_physical_age_multiplier(self, attribute_name):
        """Get age-based multiplier for physical attributes based on scientific development curves."""
        # Physical development curves based on exercise science research
        physical_curves = {
            "maximal_strength": {
                "male": [[0, 0.05], [12, 0.3], [18, 0.8], [25, 1.0], [40, 0.95], [60, 0.8], [80, 0.6]],
                "female": [[0, 0.05], [12, 0.25], [16, 0.7], [22, 1.0], [35, 0.9], [55, 0.7], [75, 0.5]]
            },
            "max_speed": {
                "male": [[0, 0.1], [8, 0.6], [16, 0.95], [20, 1.0], [30, 0.95], [50, 0.8], [70, 0.6]],
                "female": [[0, 0.1], [8, 0.6], [14, 0.9], [18, 1.0], [28, 0.9], [45, 0.7], [65, 0.5]]
            },
            "aerobic_capacity": {
                "universal": [[0, 0.2], [10, 0.8], [20, 1.0], [35, 0.95], [50, 0.85], [70, 0.7]]
            },
            "coordination": {
                "universal": [[0, 0.1], [6, 0.4], [12, 0.7], [25, 1.0], [40, 0.95], [60, 0.8], [80, 0.6]]
            },
            "flexibility": {
                "universal": [[0, 0.8], [10, 1.0], [25, 0.95], [40, 0.85], [60, 0.7], [80, 0.5]]
            },
            "reaction_time": {
                "universal": [[0, 0.3], [15, 0.8], [25, 1.0], [35, 0.95], [50, 0.85], [70, 0.7]]
            }
        }
        
        def interpolate_curve(curve, age):
            """Interpolate multiplier from age-based development curve."""
            if not curve:
                return 1.0
            
            # Find the two points to interpolate between
            for i in range(len(curve) - 1):
                age_point, multiplier = curve[i]
                next_age, next_multiplier = curve[i + 1]
                
                if age <= age_point:
                    return multiplier
                elif age < next_age:
                    # Linear interpolation between points
                    progress = (age - age_point) / (next_age - age_point)
                    return multiplier + progress * (next_multiplier - multiplier)
            
            # If age is beyond the last point, return the last multiplier
            return curve[-1][1]
        
        # Get the appropriate curve
        if attribute_name in physical_curves:
            curve_data = physical_curves[attribute_name]
            if self.gender.lower() in curve_data:
                return interpolate_curve(curve_data[self.gender.lower()], self.age)
            elif "universal" in curve_data:
                return interpolate_curve(curve_data["universal"], self.age)
        
        return 1.0  # Default multiplier

    def _recalculate_physical_attributes(self):
        """Recalculate all physical attributes based on genetic base, age, and relationships."""
        # Calculate primary attributes
        self.maximal_strength = self._calculate_maximal_strength()
        self.max_speed = self._calculate_max_speed()
        self.cardiovascular_endurance = self._calculate_cardiovascular_endurance()
        self.coordination = self._calculate_coordination()
        
        # Calculate secondary attributes
        self.strength_endurance = self._calculate_strength_endurance()
        self.acceleration = self._calculate_acceleration()
        self.explosive_power = self._calculate_explosive_power()
        self.muscular_endurance = self._calculate_muscular_endurance()
        self.balance = self._calculate_balance()
        self.agility = self._calculate_agility()
        
        # Apply validation constraints
        self._validate_physical_attributes()

    def _calculate_maximal_strength(self):
        """Based on cross-sectional area of muscle fibers"""
        # Strength ∝ Muscle Cross-sectional Area × Neural Efficiency
        age_multiplier = self._get_physical_age_multiplier("maximal_strength")
        
        base_strength = (self.lean_mass / 100.0) * 45  # Muscle mass contribution
        frame_bonus = (self.body_frame_size - 1.0) * 50  # Larger frame = more leverage
        neural_efficiency = (self.muscle_fiber_composition / 100.0) * 25  # Fast-twitch advantage
        
        raw_strength = base_strength + frame_bonus + neural_efficiency
        return min(100, max(0, raw_strength * age_multiplier))

    def _calculate_strength_endurance(self):
        """Based on slow-twitch fiber percentage and aerobic capacity"""
        age_multiplier = self._get_physical_age_multiplier("aerobic_capacity")
        
        # More slow-twitch fibers = better endurance
        slow_twitch_percentage = (100 - self.muscle_fiber_composition) / 100.0
        aerobic_component = (self.aerobic_capacity_genetic / 100.0) * 0.6
        fiber_component = slow_twitch_percentage * 0.4
        
        raw_endurance = (aerobic_component + fiber_component) * 100
        return min(100, max(0, raw_endurance * age_multiplier))

    def _calculate_max_speed(self):
        """Based on stride length and stride frequency"""
        age_multiplier = self._get_physical_age_multiplier("max_speed")
        
        # Speed = Stride Length × Stride Frequency
        stride_length_factor = (self.height_cm / 200.0) * 40  # Taller = longer stride
        stride_frequency = (self.muscle_fiber_composition / 100.0) * 30  # Fast-twitch = faster turnover
        coordination_bonus = (self.coordination / 100.0) * 30  # Better coordination = more efficient movement
        
        raw_speed = stride_length_factor + stride_frequency + coordination_bonus
        return min(100, max(0, raw_speed * age_multiplier))

    def _calculate_acceleration(self):
        """Based on strength-to-weight ratio"""
        age_multiplier = self._get_physical_age_multiplier("maximal_strength")
        
        if self.weight_kg > 0:
            strength_to_weight = self.maximal_strength / (self.weight_kg / 100.0)
        else:
            strength_to_weight = 50
        
        raw_acceleration = strength_to_weight * 0.5
        return min(100, max(0, raw_acceleration * age_multiplier))

    def _calculate_explosive_power(self):
        """Force × Velocity, the cornerstone of athletic performance"""
        age_multiplier = self._get_physical_age_multiplier("maximal_strength")
        
        force_component = self.maximal_strength / 100.0
        velocity_component = self.max_speed / 100.0
        # Power output peaks at moderate loads, not max strength
        optimal_load_factor = 0.7  # 70% of max strength for peak power
        
        raw_power = (force_component * optimal_load_factor * velocity_component) * 100
        return min(100, max(0, raw_power * age_multiplier))

    def _calculate_cardiovascular_endurance(self):
        """Aerobic performance capacity"""
        age_multiplier = self._get_physical_age_multiplier("aerobic_capacity")
        
        # Mix of genetic potential and current health
        genetic_component = (self.aerobic_capacity_genetic / 100.0) * 0.8
        health_component = (self.health / 100.0) * 0.2
        
        raw_endurance = (genetic_component + health_component) * 100
        return min(100, max(0, raw_endurance * age_multiplier))

    def _calculate_muscular_endurance(self):
        """Resistance to fatigue in repeated contractions"""
        # Blend of strength endurance and cardiovascular endurance
        strength_component = (self.strength_endurance / 100.0) * 0.7
        cardio_component = (self.cardiovascular_endurance / 100.0) * 0.3
        
        raw_endurance = (strength_component + cardio_component) * 100
        return min(100, max(0, raw_endurance))

    def _calculate_balance(self):
        """Based on proprioception and core stability"""
        age_multiplier = self._get_physical_age_multiplier("coordination")
        
        # Base balance with age factor
        base_balance = 50 + (age_multiplier - 1.0) * 30
        coordination_bonus = (self.coordination / 100.0) * 20
        core_stability = (self.maximal_strength / 100.0) * 10
        
        raw_balance = base_balance + coordination_bonus + core_stability
        return min(100, max(0, raw_balance))

    def _calculate_coordination(self):
        """Neuromuscular efficiency"""
        age_multiplier = self._get_physical_age_multiplier("coordination")
        
        # Base coordination with genetic factors
        genetic_base = 50 + (self.muscle_fiber_composition - 50) * 0.3  # Fast-twitch = better motor unit recruitment
        frame_factor = (self.body_frame_size - 1.0) * 10  # Larger frame = slightly less precise
        
        raw_coordination = genetic_base + frame_factor
        return min(100, max(0, raw_coordination * age_multiplier))

    def _calculate_agility(self):
        """Change of direction ability"""
        # Agility = (Speed + Coordination + Balance) / 3
        speed_component = (self.max_speed / 100.0) * 0.4
        coordination_component = (self.coordination / 100.0) * 0.4
        balance_component = (self.balance / 100.0) * 0.2
        
        raw_agility = (speed_component + coordination_component + balance_component) * 100
        return min(100, max(0, raw_agility))

    def _validate_physical_attributes(self):
        """Ensure biologically impossible combinations don't exist"""
        # Power cannot exceed strength × speed constraints
        max_possible_power = (self.maximal_strength / 100.0) * (self.max_speed / 100.0) * 80
        if self.explosive_power > max_possible_power * 100:
            self.explosive_power = max_possible_power * 100
        
        # Speed requires minimum coordination
        min_coordination_for_speed = self.max_speed * 0.6
        if self.coordination < min_coordination_for_speed:
            self.coordination = min_coordination_for_speed
        
        # Strength requires muscle mass
        if self.lean_mass < 30:
            max_strength_from_mass = self.lean_mass * 2
            if self.maximal_strength > max_strength_from_mass:
                self.maximal_strength = max_strength_from_mass
        
        # Ensure all values are in valid range
        self.maximal_strength = min(100, max(0, self.maximal_strength))
        self.strength_endurance = min(100, max(0, self.strength_endurance))
        self.max_speed = min(100, max(0, self.max_speed))
        self.acceleration = min(100, max(0, self.acceleration))
        self.explosive_power = min(100, max(0, self.explosive_power))
        self.cardiovascular_endurance = min(100, max(0, self.cardiovascular_endurance))
        self.muscular_endurance = min(100, max(0, self.muscular_endurance))
        self.balance = min(100, max(0, self.balance))
        self.coordination = min(100, max(0, self.coordination))
        self.agility = min(100, max(0, self.agility))

    def _rand_attr(self, config, name):
        """Helper to get random attribute within config range."""
        return random.randint(config.get(f"{name}_min", 0), config.get(f"{name}_max", 100))

    def _generate_big_five(self, config):
        """Generates the 30 facets grouped by Big 5 attribute."""
        min_v = config.get("facet_min", 1)
        max_v = config.get("facet_max", 20)
        
        def r(): return random.randint(min_v, max_v)
        
        return {
            "Openness": {
                "Fantasy": r(), "Aesthetics": r(), "Feelings": r(), 
                "Actions": r(), "Ideas": r(), "Values": r()
            },
            "Conscientiousness": {
                "Competence": r(), "Order": r(), "Dutifulness": r(), 
                "Achievement": r(), "Self-Discipline": r(), "Deliberation": r()
            },
            "Extraversion": {
                "Warmth": r(), "Gregariousness": r(), "Assertiveness": r(), 
                "Activity": r(), "Excitement": r(), "Positive Emotions": r()
            },
            "Agreeableness": {
                "Trust": r(), "Straightforwardness": r(), "Altruism": r(), 
                "Compliance": r(), "Modesty": r(), "Tender-Mindedness": r()
            },
            "Neuroticism": {
                "Anxiety": r(), "Angry Hostility": r(), "Depression": r(), 
                "Self-Consciousness": r(), "Impulsiveness": r(), "Vulnerability": r()
            }
        }

    def _generate_infant_temperament(self):
        """Generates temperament traits for infants (age < 3)."""
        temperament = {}

        # Facet-level inheritance: closer to temperament research than broad trait means.
        # Each tuple: (Big5 trait, facet, weight, invert)
        parent_facet_mapping = {
            "Activity": [
                ("Extraversion", "Activity", 0.45, False),
                ("Extraversion", "Excitement", 0.35, False),
                ("Conscientiousness", "Achievement", 0.20, False),
            ],
            "Regularity": [
                ("Conscientiousness", "Order", 0.45, False),
                ("Conscientiousness", "Deliberation", 0.30, False),
                ("Conscientiousness", "Self-Discipline", 0.25, False),
            ],
            "Approach_Withdrawal": [
                ("Extraversion", "Warmth", 0.35, False),
                ("Extraversion", "Gregariousness", 0.30, False),
                ("Neuroticism", "Anxiety", 0.35, True),
            ],
            "Adaptability": [
                ("Openness", "Actions", 0.30, False),
                ("Openness", "Values", 0.25, False),
                ("Conscientiousness", "Deliberation", 0.20, False),
                ("Neuroticism", "Vulnerability", 0.25, True),
            ],
            "Threshold": [
                ("Neuroticism", "Vulnerability", 0.45, True),
                ("Neuroticism", "Anxiety", 0.35, True),
                ("Extraversion", "Positive Emotions", 0.20, False),
            ],
            "Intensity": [
                ("Extraversion", "Excitement", 0.35, False),
                ("Neuroticism", "Angry Hostility", 0.35, False),
                ("Neuroticism", "Impulsiveness", 0.30, False),
            ],
            "Mood": [
                ("Extraversion", "Positive Emotions", 0.45, False),
                ("Neuroticism", "Depression", 0.35, True),
                ("Neuroticism", "Anxiety", 0.20, True),
            ],
            "Distractibility": [
                ("Conscientiousness", "Self-Discipline", 0.35, True),
                ("Conscientiousness", "Order", 0.30, True),
                ("Openness", "Ideas", 0.20, False),
                ("Neuroticism", "Impulsiveness", 0.15, False),
            ],
            "Persistence": [
                ("Conscientiousness", "Achievement", 0.40, False),
                ("Conscientiousness", "Self-Discipline", 0.35, False),
                ("Neuroticism", "Vulnerability", 0.25, True),
            ],
        }

        parental_weight = 0.70
        nonshared_environment_weight = 0.30

        for trait in constants.TEMPERAMENT_TRAITS:
            if self.parents:
                father, mother = self.parents
                mappings = parent_facet_mapping.get(trait, [])
                parent_estimates = []

                for parent in (father, mother):
                    if not parent.personality:
                        continue

                    weighted_sum = 0.0
                    total_weight = 0.0
                    for big5_trait, facet, weight, invert in mappings:
                        facet_value = parent.personality.get(big5_trait, {}).get(facet)
                        if facet_value is None:
                            continue

                        # Facets are 1-20; normalize to 0-100.
                        norm_value = ((float(facet_value) - 1.0) / 19.0) * 100.0
                        if invert:
                            norm_value = 100.0 - norm_value
                        weighted_sum += norm_value * weight
                        total_weight += weight

                    if total_weight > 0:
                        parent_estimates.append(weighted_sum / total_weight)

                parental_avg = sum(parent_estimates) / len(parent_estimates) if parent_estimates else 50.0

                # Shared environment + developmental noise (non-shared environment).
                random_val = max(0.0, min(100.0, random.gauss(50.0, 12.0)))
                final_value = (parental_avg * parental_weight) + (random_val * nonshared_environment_weight)
                final_value = max(0.0, min(100.0, final_value))
            else:
                # No parents - pure random generation
                final_value = random.gauss(50, 15)
                final_value = max(0, min(100, final_value))

            temperament[trait] = round(final_value, 1)

        return temperament

    def crystallize_personality(self):
        """Converts temperament traits to a deterministic full Big Five profile."""
        if not self.temperament:
            return

        def temp_norm(trait_name):
            raw = float(self.temperament.get(trait_name, constants.TEMPERAMENT_DEFAULT_VALUE))
            raw = max(0.0, min(100.0, raw))
            return (raw - 50.0) / 50.0

        t = {trait: temp_norm(trait) for trait in constants.TEMPERAMENT_TRAITS}
        inv = {trait: -value for trait, value in t.items()}

        # Latent dimensions anchored in classic temperament structure.
        latent = {
            "Surgency": (
                (0.34 * t["Activity"]) +
                (0.26 * t["Approach_Withdrawal"]) +
                (0.20 * t["Intensity"]) +
                (0.20 * t["Mood"])
            ),
            "EffortfulControl": (
                (0.30 * t["Persistence"]) +
                (0.25 * t["Regularity"]) +
                (0.25 * t["Adaptability"]) +
                (0.20 * inv["Distractibility"])
            ),
            "NegativeAffect": (
                (0.30 * inv["Threshold"]) +
                (0.25 * inv["Mood"]) +
                (0.20 * t["Intensity"]) +
                (0.15 * inv["Adaptability"]) +
                (0.10 * t["Distractibility"])
            ),
            "OrientationSensitivity": (
                (0.35 * t["Adaptability"]) +
                (0.25 * t["Approach_Withdrawal"]) +
                (0.20 * inv["Regularity"]) +
                (0.20 * inv["Distractibility"])
            ),
        }

        facet_models = {
            "Openness": {
                "Fantasy": {"latent": {"OrientationSensitivity": 0.65}, "temp": {"Mood": 0.25, "Activity": 0.15}},
                "Aesthetics": {"latent": {"OrientationSensitivity": 0.60}, "temp": {"Mood": 0.30, "Intensity": 0.20}},
                "Feelings": {"latent": {"OrientationSensitivity": 0.35, "NegativeAffect": 0.20}, "temp": {"Mood": 0.25, "Intensity": 0.15}},
                "Actions": {"latent": {"OrientationSensitivity": 0.55}, "temp": {"Approach_Withdrawal": 0.35, "Regularity": -0.20}},
                "Ideas": {"latent": {"OrientationSensitivity": 0.70}, "temp": {"Distractibility": 0.15, "Persistence": 0.10}},
                "Values": {"latent": {"OrientationSensitivity": 0.55}, "temp": {"Adaptability": 0.30, "Approach_Withdrawal": 0.15}},
            },
            "Conscientiousness": {
                "Competence": {"latent": {"EffortfulControl": 0.65}, "temp": {"Persistence": 0.30, "Intensity": -0.10}},
                "Order": {"latent": {"EffortfulControl": 0.35}, "temp": {"Regularity": 0.70, "Distractibility": -0.35}},
                "Dutifulness": {"latent": {"EffortfulControl": 0.55}, "temp": {"Adaptability": 0.25, "Intensity": -0.25}},
                "Achievement": {"latent": {"EffortfulControl": 0.70}, "temp": {"Activity": 0.25, "Mood": 0.10}},
                "Self-Discipline": {"latent": {"EffortfulControl": 0.75}, "temp": {"Persistence": 0.35, "Distractibility": -0.45}},
                "Deliberation": {"latent": {"EffortfulControl": 0.40}, "temp": {"Regularity": 0.35, "Intensity": -0.40, "Threshold": 0.10}},
            },
            "Extraversion": {
                "Warmth": {"latent": {"Surgency": 0.45}, "temp": {"Approach_Withdrawal": 0.35, "Mood": 0.30}},
                "Gregariousness": {"latent": {"Surgency": 0.65}, "temp": {"Activity": 0.30, "Threshold": 0.10}},
                "Assertiveness": {"latent": {"Surgency": 0.55}, "temp": {"Activity": 0.25, "Intensity": 0.25}},
                "Activity": {"latent": {"Surgency": 0.35}, "temp": {"Activity": 0.85, "Mood": 0.10}},
                "Excitement": {"latent": {"Surgency": 0.45}, "temp": {"Intensity": 0.65, "Threshold": 0.20}},
                "Positive Emotions": {"latent": {"Surgency": 0.35, "NegativeAffect": -0.55}, "temp": {"Mood": 0.80}},
            },
            "Agreeableness": {
                "Trust": {"latent": {"NegativeAffect": -0.40}, "temp": {"Adaptability": 0.45, "Mood": 0.35}},
                "Straightforwardness": {"latent": {"EffortfulControl": 0.35, "NegativeAffect": -0.25}, "temp": {"Regularity": 0.25, "Intensity": -0.15}},
                "Altruism": {"latent": {"NegativeAffect": -0.25}, "temp": {"Mood": 0.40, "Approach_Withdrawal": 0.30, "Adaptability": 0.30}},
                "Compliance": {"latent": {"NegativeAffect": -0.30}, "temp": {"Adaptability": 0.65, "Intensity": -0.45}},
                "Modesty": {"latent": {"Surgency": -0.25, "EffortfulControl": 0.20}, "temp": {"Intensity": -0.35, "Approach_Withdrawal": -0.10}},
                "Tender-Mindedness": {"latent": {"NegativeAffect": -0.20}, "temp": {"Mood": 0.35, "Adaptability": 0.35, "Intensity": -0.20}},
            },
            "Neuroticism": {
                "Anxiety": {"latent": {"NegativeAffect": 0.85}, "temp": {"Threshold": -0.35, "Mood": -0.20}},
                "Angry Hostility": {"latent": {"NegativeAffect": 0.55}, "temp": {"Intensity": 0.45, "Adaptability": -0.35}},
                "Depression": {"latent": {"NegativeAffect": 0.75, "Surgency": -0.20}, "temp": {"Mood": -0.55}},
                "Self-Consciousness": {"latent": {"NegativeAffect": 0.60}, "temp": {"Approach_Withdrawal": -0.35, "Mood": -0.25}},
                "Impulsiveness": {"latent": {"NegativeAffect": 0.35, "EffortfulControl": -0.55}, "temp": {"Intensity": 0.55}},
                "Vulnerability": {"latent": {"NegativeAffect": 0.80}, "temp": {"Persistence": -0.35, "Threshold": -0.35}},
            },
        }

        def to_facet(raw_score):
            # Logistic transform creates realistic central tendency with bounded extremes.
            scaled = 1.0 + (19.0 / (1.0 + math.exp(-1.35 * raw_score)))
            return max(1, min(20, int(round(scaled))))

        personality = {}
        for big5_trait, facets in facet_models.items():
            personality[big5_trait] = {}
            for facet, model in facets.items():
                raw = 0.0
                for latent_name, weight in model.get("latent", {}).items():
                    raw += latent[latent_name] * weight
                for trait_name, weight in model.get("temp", {}).items():
                    raw += t[trait_name] * weight
                personality[big5_trait][facet] = to_facet(raw)

        # Set the new personality and clear temperament
        self.personality = personality
        self.temperament = None
        self.is_personality_locked = True
        self.plasticity = 0.0

    def _seeded_rng(self, world_seed, step, channel):
        """Deterministic per-agent RNG for backfill replay."""
        seed = f"{world_seed}|{self.uid}|{step}|{channel}"
        return random.Random(seed)

    def _personality_backfill_plasticity(self, age_year):
        """Age-based residual personality plasticity after age 3."""
        if age_year <= 6:
            return 0.20
        if age_year <= 12:
            return 0.14
        if age_year <= 17:
            return 0.10
        if age_year <= 25:
            return 0.06
        if age_year <= 40:
            return 0.03
        return 0.02

    def _temperament_latents(self, temperament_values):
        """Shared latent scaffold for developmental continuity."""
        def norm(name):
            raw = float(temperament_values.get(name, constants.TEMPERAMENT_DEFAULT_VALUE))
            raw = max(0.0, min(100.0, raw))
            return (raw - 50.0) / 50.0

        t = {trait: norm(trait) for trait in constants.TEMPERAMENT_TRAITS}
        inv = {trait: -value for trait, value in t.items()}
        latents = {
            "surgency": (0.34 * t["Activity"]) + (0.26 * t["Approach_Withdrawal"]) + (0.20 * t["Intensity"]) + (0.20 * t["Mood"]),
            "effortful": (0.30 * t["Persistence"]) + (0.25 * t["Regularity"]) + (0.25 * t["Adaptability"]) + (0.20 * inv["Distractibility"]),
            "negative_affect": (0.30 * inv["Threshold"]) + (0.25 * inv["Mood"]) + (0.20 * t["Intensity"]) + (0.15 * inv["Adaptability"]) + (0.10 * t["Distractibility"]),
            "orientation": (0.35 * t["Adaptability"]) + (0.25 * t["Approach_Withdrawal"]) + (0.20 * inv["Regularity"]) + (0.20 * inv["Distractibility"]),
            "adaptability": t["Adaptability"],
            "mood": t["Mood"],
            "intensity": t["Intensity"],
        }
        return latents

    def _apply_backfill_personality_year(self, age_year, latents, world_seed):
        """Applies one deterministic year of age-dependent personality drift."""
        if not self.personality:
            return

        p = self._personality_backfill_plasticity(age_year)
        trait_targets = {
            "Openness": 10.0 + (2.4 * latents["orientation"]) + (0.6 * latents["surgency"]) - (0.4 * latents["negative_affect"]),
            "Conscientiousness": 10.0 + (2.8 * latents["effortful"]) - (0.6 * latents["negative_affect"]),
            "Extraversion": 10.0 + (2.6 * latents["surgency"]) - (0.5 * latents["negative_affect"]),
            "Agreeableness": 10.0 + (1.8 * latents["adaptability"]) + (0.8 * latents["mood"]) - (1.2 * latents["intensity"]),
            "Neuroticism": 10.0 + (2.8 * latents["negative_affect"]) - (0.8 * latents["effortful"]),
        }

        for trait_name, facets in self.personality.items():
            trait_center = max(2.0, min(18.0, trait_targets.get(trait_name, 10.0)))
            for facet_name, current in facets.items():
                offset_rng = self._seeded_rng(world_seed, 0, f"facet-offset-{trait_name}-{facet_name}")
                facet_offset = offset_rng.uniform(-1.1, 1.1)
                target = max(1.0, min(20.0, trait_center + facet_offset))

                step_rng = self._seeded_rng(world_seed, age_year, f"facet-year-{trait_name}-{facet_name}")
                random_walk = step_rng.gauss(0.0, 0.9) * p
                mean_pull = (target - float(current)) * 0.55 * p
                updated = float(current) + mean_pull + random_walk
                self.personality[trait_name][facet_name] = max(1, min(20, int(round(updated))))

    def backfill_to_age_months(self, target_age_months, world_seed=0, infant_month_callback=None):
        """
        Deterministically reconstructs developmental history from birth to target age in months.
        Used for late-spawned agents so they remain comparable to continuously simulated agents.
        """
        target_age_months = max(0, int(target_age_months))
        if target_age_months <= 0:
            self._backfilled_to_age = 0
            self._backfilled_to_age_months = 0
            return
        if getattr(self, "_backfilled_to_age_months", None) == target_age_months:
            return

        # Rebuild early development from birth state.
        self.personality = None
        self.temperament = self._generate_infant_temperament()
        self.is_personality_locked = False
        self.plasticity = 1.0

        months_until_three = min(target_age_months, 36)
        for month in range(months_until_three):
            age_year = month // 12
            self.plasticity = constants.PLASTICITY_DECAY.get(age_year, 0.0)
            for trait_name in constants.TEMPERAMENT_TRAITS:
                rng = self._seeded_rng(world_seed, month, f"temp-{trait_name}")
                current = float(self.temperament.get(trait_name, constants.TEMPERAMENT_DEFAULT_VALUE))
                shock = rng.gauss(0.0, 1.8) * self.plasticity
                baseline_pull = (constants.TEMPERAMENT_DEFAULT_VALUE - current) * 0.03 * self.plasticity
                updated = max(0.0, min(100.0, current + shock + baseline_pull))
                self.temperament[trait_name] = round(updated, 1)
            if callable(infant_month_callback):
                # Callback receives 1-based age month cursor to align with event triggers.
                infant_month_callback(self, month + 1)

        if target_age_months >= 36:
            infant_snapshot = dict(self.temperament)
            self.crystallize_personality()
            latents = self._temperament_latents(infant_snapshot)
            target_age_years = target_age_months // 12
            for age_year in range(3, target_age_years):
                self._apply_backfill_personality_year(age_year, latents, world_seed)
        else:
            target_age_years = target_age_months // 12
            self.plasticity = constants.PLASTICITY_DECAY.get(target_age_years, self.plasticity)

        self._backfilled_to_age = target_age_months // 12
        self._backfilled_to_age_months = target_age_months

    def backfill_to_age(self, target_age, world_seed=0):
        """
        Deterministically reconstructs developmental history from birth to target age.
        Used for late-spawned agents so they remain comparable to continuously simulated agents.
        """
        self.backfill_to_age_months(int(target_age) * 12, world_seed=world_seed)

    def get_personality_sum(self, trait):
        """Returns the sum (0-120) of a main trait."""
        if not self.personality:
            return 50  # Neutral fallback for young children without personality
        return sum(self.personality.get(trait, {}).values())

    def _subject_trait_inputs(self):
        """Returns normalized aptitude + personality inputs used by subject calculations."""
        if self.personality:
            openness = self.personality.get("Openness", {})
            conscientiousness = self.personality.get("Conscientiousness", {})
        else:
            openness = {"Ideas": 10, "Aesthetics": 10, "Values": 10}
            conscientiousness = {"Competence": 10}

        aptitudes = getattr(self, "aptitudes", {}) or {}

        def normalized_aptitude(name):
            phenotype = aptitudes.get(name, {}).get("phenotype", 100.0)
            normalized = (float(phenotype) / 180.0) * 100.0
            return max(0.0, min(100.0, normalized))

        return {
            "analytical": normalized_aptitude("Analytical Reasoning"),
            "verbal": normalized_aptitude("Verbal Abilities"),
            "spatial": normalized_aptitude("Spatial Abilities"),
            "working_memory": normalized_aptitude("Working Memory"),
            "long_term_memory": normalized_aptitude("Long-term Memory"),
            "secondary_cognitive": normalized_aptitude("Secondary Cognitive"),
            "competence": max(0, min(100, (conscientiousness.get("Competence", 10) / 20.0) * 100)),
            "ideas": max(0, min(100, (openness.get("Ideas", 10) / 20.0) * 100)),
            "aesthetics": max(0, min(100, (openness.get("Aesthetics", 10) / 20.0) * 100)),
            "values": max(0, min(100, (openness.get("Values", 10) / 20.0) * 100)),
            "athleticism": max(0, min(100, float(self.cardiovascular_endurance)))
        }

    def _classify_subject_category(self, subject_name):
        """Classifies subjects into broad categories for aptitude/progression profiles."""
        name = subject_name.lower()
        keyword_map = {
            "core_skills": ("communication", "psed", "development", "reception", "nursery"),
            "stem": ("math", "mathematics", "science", "biology", "chem", "physics", "comput", "ict", "technology"),
            "language": ("english", "language", "literature", "phonics", "french", "spanish", "german", "mandarin", "literacy", "lang"),
            "humanities": ("history", "geography", "citizenship", "economics", "business", "societies", "perspectives", "knowledge"),
            "creative": ("art", "music", "drama", "expressive", "design"),
            "physical": ("physical", "pe", "sport")
        }

        for category, keywords in keyword_map.items():
            if any(keyword in name for keyword in keywords):
                return category
        return "default"

    def _get_subject_profile(self, category):
        """Returns weighting and progression profile for a subject category."""
        profiles = {
            "core_skills": {
                "weights": {
                    "verbal": 0.25,
                    "long_term_memory": 0.20,
                    "working_memory": 0.15,
                    "competence": 0.20,
                    "ideas": 0.10,
                    "values": 0.10
                },
                "progression_rate": 0.020
            },
            "stem": {
                "weights": {
                    "analytical": 0.35,
                    "working_memory": 0.25,
                    "spatial": 0.15,
                    "competence": 0.15,
                    "ideas": 0.10
                },
                "progression_rate": 0.018
            },
            "language": {
                "weights": {
                    "verbal": 0.35,
                    "long_term_memory": 0.20,
                    "working_memory": 0.15,
                    "aesthetics": 0.10,
                    "competence": 0.10,
                    "ideas": 0.05,
                    "values": 0.05
                },
                "progression_rate": 0.019
            },
            "humanities": {
                "weights": {
                    "verbal": 0.20,
                    "long_term_memory": 0.20,
                    "values": 0.25,
                    "competence": 0.15,
                    "ideas": 0.10,
                    "secondary_cognitive": 0.10
                },
                "progression_rate": 0.018
            },
            "creative": {
                "weights": {
                    "spatial": 0.25,
                    "aesthetics": 0.35,
                    "ideas": 0.15,
                    "verbal": 0.10,
                    "competence": 0.10,
                    "secondary_cognitive": 0.05
                },
                "progression_rate": 0.021
            },
            "physical": {
                "weights": {
                    "athleticism": 0.50,
                    "competence": 0.20,
                    "spatial": 0.15,
                    "working_memory": 0.05,
                    "analytical": 0.05,
                    "values": 0.05
                },
                "progression_rate": 0.020
            },
            "default": {
                "weights": {
                    "analytical": 0.20,
                    "verbal": 0.20,
                    "working_memory": 0.15,
                    "long_term_memory": 0.15,
                    "competence": 0.15,
                    "ideas": 0.10,
                    "aesthetics": 0.05
                },
                "progression_rate": 0.019
            }
        }
        return profiles.get(category, profiles["default"])

    def _calculate_subject_profile(self, subject_name):
        """
        Calculates natural aptitude and progression tuning for a configured subject.
        Returns tuple: (natural_aptitude, category, progression_rate).
        """
        category = self._classify_subject_category(subject_name)
        profile = self._get_subject_profile(category)
        trait_inputs = self._subject_trait_inputs()

        raw = 0.0
        for trait_name, weight in profile["weights"].items():
            raw += trait_inputs.get(trait_name, 50.0) * weight

        natural_aptitude = min(100, max(0, raw))
        return natural_aptitude, category, profile["progression_rate"]

    def _initialize_subjects(self, subject_names=None, preserve_existing=False, reset_monthly_change=False):
        """Builds per-subject grade records for a dynamic subject list."""
        if subject_names is None:
            # Legacy fallback for older flows not yet migrated.
            subject_names = ["Math", "Science", "Language Arts", "History"]

        # De-duplicate while preserving order.
        unique_subjects = list(dict.fromkeys(subject_names))
        existing = self.subjects if preserve_existing and isinstance(self.subjects, dict) else {}
        subjects = {}

        for subject_name in unique_subjects:
            prev = existing.get(subject_name, {})
            current_grade = float(prev.get("current_grade", 50))
            monthly_change = 0.0 if reset_monthly_change else float(prev.get("monthly_change", 0.0))
            natural_aptitude, category, progression_rate = self._calculate_subject_profile(subject_name)

            subjects[subject_name] = {
                "current_grade": max(0, min(100, current_grade)),
                "natural_aptitude": natural_aptitude,
                "monthly_change": monthly_change,
                "category": category,
                "progression_rate": progression_rate
            }

        return subjects

    def sync_subjects_with_school(self, school_system, preserve_existing=True, reset_monthly_change=False):
        """
        Synchronizes this agent's subject portfolio to the active school curriculum.
        Returns True if subjects were updated.
        """
        if not self.school or not school_system:
            return False

        active_subjects = school_system.get_active_subjects_for_agent(self)
        if not active_subjects:
            return False

        self.subjects = self._initialize_subjects(
            active_subjects,
            preserve_existing=preserve_existing,
            reset_monthly_change=reset_monthly_change
        )
        return True

    def _recalculate_hormones(self):
        """
        Calculates current Fertility and Libido based on Age and Gender curves.
        Distinguishes Genotype (Peak) from Phenotype (Current).
        """
        age = self.age
        
        # --- Fertility Curve ---
        fert_factor = 0.0
        if self.gender == "Female":
            if age < 12:
                fert_factor = 0.0
            elif age < 15:
                # Puberty ramp (12-15)
                fert_factor = (age - 11) / 4.0
            elif age <= 30:
                # Prime (15-30)
                fert_factor = 1.0
            elif age <= 45:
                # Decline (30-45)
                fert_factor = 1.0 - ((age - 30) / 20.0) # Drops to 0.25
            elif age < 50:
                # Menopause onset (45-50)
                fert_factor = 0.25 - ((age - 45) / 5.0 * 0.25)
            else:
                # Menopause complete
                fert_factor = 0.0
        else: # Male
            if age < 13:
                fert_factor = 0.0
            elif age < 18:
                # Puberty ramp
                fert_factor = (age - 12) / 6.0
            elif age < 40:
                # Prime
                fert_factor = 1.0
            else:
                # Gradual Senescence (never fully hits 0)
                decay = (age - 40) * 0.01
                fert_factor = max(0.2, 1.0 - decay)

        self.fertility = int(self._genetic_fertility_peak * fert_factor)

        # --- Libido Curve ---
        # Simplified: Both genders spike in teens, plateau, then decay with age/health
        lib_factor = 0.0
        if age < 13:
            lib_factor = 0.0
        elif age < 18:
            # Hormonal Storm (13-18)
            lib_factor = 0.5 + ((age - 13) / 5.0 * 0.5) # Ramps 0.5 -> 1.0
        elif age < 35:
            lib_factor = 1.0
        else:
            # Age decay
            decay = (age - 35) * 0.015
            lib_factor = max(0.1, 1.0 - decay)
            
        self.libido = int(self._genetic_libido_peak * lib_factor)

    def _recalculate_physique(self):
        """
        Updates Lean Mass, Weight, and BMI based on current Height and physical attributes.
        Uses a 'Lean Body Mass Index' (LBMI) abstraction.
        """
        # 1. Determine Base LBMI (Lean Mass / Height^2)
        # Male range: 18 (Skinny) - 24 (Muscular)
        # Female range: 15 (Skinny) - 21 (Muscular)
        base_lbmi = 18.0 if self.gender == "Male" else 15.0
        
        # Use cardiovascular endurance instead of old athleticism
        athletic_bonus = (self.cardiovascular_endurance / 100.0) * 6.0
        current_lbmi = base_lbmi + athletic_bonus
        
        # 2. Calculate Lean Mass (LBMI * Height_m^2)
        height_m = self.height_cm / 100.0
        self.lean_mass = round(current_lbmi * (height_m ** 2), 1)
        
        # 3. Calculate Total Weight (Lean Mass + Body Fat)
        # Weight = Lean / (1 - BF%)
        bf_decimal = self.body_fat / 100.0
        # Prevent division by zero or negative mass
        if bf_decimal >= 1.0: bf_decimal = 0.99 
        
        self.weight_kg = round(self.lean_mass / (1 - bf_decimal), 1)
        
        # 4. Calculate BMI
        if height_m > 0:
            self.bmi = round(self.weight_kg / (height_m ** 2), 1)
        else:
            self.bmi = 0
        
        # 5. Recalculate physical attributes based on new physique
        self._recalculate_physical_attributes()

    def _recalculate_ap_needs(self, time_config):
        """Calculates sleep requirements based on age."""
        if not time_config: 
            return
        
        reqs = time_config.get("sleep_requirements", {})
        # Sort by max_age to find the correct bracket
        sorted_reqs = sorted(reqs.values(), key=lambda x: x["max_age"])
        
        for r in sorted_reqs:
            if self.age <= r["max_age"]:
                self.ap_sleep = r["hours"]
                # Keep target_sleep_hours in sync with calculated requirements
                self.target_sleep_hours = self.ap_sleep
                return
        
        # Fallback for oldest age
        if sorted_reqs:
            self.ap_sleep = sorted_reqs[-1]["hours"]
            self.target_sleep_hours = self.ap_sleep

    @property
    def free_ap(self):
        """Returns available AP."""
        locked_ap = self.ap_locked * self.attendance_rate
        sleep_ap = self.target_sleep_hours
        return max(0.0, self.ap_max - locked_ap - sleep_ap - self.ap_used)

    def set_schedule(self, sleep=None, attendance=None):
        """Set schedule preferences with validation and rounding."""
        if sleep is not None:
            # Apply age-based cap: max 12 hours after age 3
            max_sleep = 12.0 if self.age >= 3 else 24.0
            
            # Clamp between minimum permitted and age-based max, then round to granularity
            sleep = max(constants.MIN_SLEEP_PERMITTED, min(max_sleep, sleep))
            self.target_sleep_hours = round(sleep / constants.AP_GRANULARITY) * constants.AP_GRANULARITY
        
        if attendance is not None:
            # Clamp between 0.0 and 1.0, then round to nearest decimal place
            attendance = max(0.0, min(1.0, attendance))
            self.attendance_rate = round(attendance, 1)

