# life_sim/simulation/state.py
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

class Agent:
    """
    Represents a human entity (Player or NPC).
    
    Data Contract:
        Inputs: config dictionary (agent section), **kwargs for overrides
        State: age_months, health, happiness, smarts, looks, relationships, inventory
    """
    def __init__(self, agent_config: dict, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.uid = str(uuid.uuid4())
        self.is_player = kwargs.get("is_player", False)
        
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
        
        # IQ Initialization (Gaussian)
        mean = agent_config.get("iq_mean", 100)
        sd = agent_config.get("iq_sd", 15)
        val = int(random.gauss(mean, sd))
        self.iq = max(50, min(180, val)) # Clamp to realistic bounds
        
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

        # --- Extended Attributes ---
        attr_config = agent_config.get("attributes", {})
        
        # Physical
        self.strength = self._rand_attr(attr_config, "strength")
        self.athleticism = self._rand_attr(attr_config, "athleticism")
        self.endurance = self._rand_attr(attr_config, "endurance")
        
        # Genotype: The genetic peak potential (0-100)
        self._genetic_fertility_peak = self._rand_attr(attr_config, "fertility")
        self._genetic_libido_peak = self._rand_attr(attr_config, "libido")
        
        # Phenotype: Current expressed value (starts at 0 for babies)
        self.fertility = 0
        self.libido = 0

        # Derived Bio-Metrics (Simple approximation based on Athleticism)
        # Base BF: Men ~25%, Women ~35%. Athleticism reduces this.
        base_bf = 25.0 if self.gender == "Male" else 35.0
        reduction = (self.athleticism / 100.0) * 18.0 # Up to 18% reduction
        variance = random.uniform(-3.0, 5.0)
        self.body_fat = max(4.0, round(base_bf - reduction + variance, 1))
        
        # Initialize dynamic physique stats
        self.lean_mass = 0
        self.weight_kg = 0
        self.bmi = 0
        
        # Calculate initial phenotype based on age
        self._recalculate_hormones()
        self._recalculate_physique()
        
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
        self.subjects = self._initialize_subjects()
        
        self.religiousness = self._rand_attr(attr_config, "religiousness")
        
        # Hidden
        self.karma = self._rand_attr(attr_config, "karma")
        self.luck = self._rand_attr(attr_config, "luck")
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
        
        # Calculate initial sleep needs if config provided
        time_config = kwargs.get("time_config", {})
        self._recalculate_ap_needs(time_config)

        # Dashboard Customization (Default Pinned Stats)
        self.pinned_attributes = [
            "Health", "Happiness", "IQ", "Looks", "Energy", "Fitness"
        ]

        self.logger.info(f"Agent initialized ({'Player' if self.is_player else 'NPC'}): {self.first_name} {self.last_name} ({self.gender}) Age {self.age}")

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
        
        # Physical
        if name == "Energy": return self.endurance
        if name == "Fitness": return self.athleticism
        if name == "Strength": return self.strength
        if name == "Fertility": return self.fertility
        if name == "Genetic Fertility": return self._genetic_fertility_peak
        if name == "Libido": return self.libido
        if name == "Genetic Libido": return self._genetic_libido_peak
        
        # Big 5 (Sums)
        if self.personality and name in self.personality:
            return self.get_personality_sum(name)
            
        # Big 5 (Facets) - Search inside the nested dicts
        if self.personality:
            for trait, facets in self.personality.items():
                if name in facets:
                    return facets[name]

        # Hidden/Other
        if name == "Karma": return self.karma
        if name == "Luck": return self.luck
        if name == "Religiousness": return self.religiousness
        
        # Academic Subjects
        if name in self.subjects:
            return self.subjects[name]["current_grade"]
        
        # Temperament (for infants)
        if self.temperament and name in self.temperament:
            return self.temperament[name]
        
        return 0

    @property
    def age(self):
        """Returns age in years (integer)."""
        return self.age_months // 12

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
        
        # Simplified mapping from parent Big 5 traits to child temperament traits
        # This is a basic mapping - could be made more sophisticated
        parent_trait_mapping = {
            "Activity": ["Extraversion"],
            "Regularity": ["Conscientiousness"], 
            "Approach_Withdrawal": ["Extraversion", "Neuroticism"],
            "Adaptability": ["Openness", "Conscientiousness"],
            "Threshold": ["Neuroticism"],
            "Intensity": ["Extraversion", "Neuroticism"],
            "Mood": ["Neuroticism"],
            "Distractibility": ["Openness", "Neuroticism"],
            "Persistence": ["Conscientiousness"]
        }
        
        for trait in constants.TEMPERAMENT_TRAITS:
            if self.parents:
                # Child has parents - blend genetic and random factors
                father, mother = self.parents
                
                # Get relevant parent Big 5 traits
                parent_traits = parent_trait_mapping.get(trait, [])
                parental_values = []
                
                for parent_trait in parent_traits:
                    if father.personality and parent_trait in father.personality:
                        father_sum = sum(father.personality[parent_trait].values())
                        parental_values.append(father_sum / 6.0)  # Average of 6 facets (0-20 scale)
                    
                    if mother.personality and parent_trait in mother.personality:
                        mother_sum = sum(mother.personality[parent_trait].values())
                        parental_values.append(mother_sum / 6.0)  # Average of 6 facets (0-20 scale)
                
                # Calculate parental average (convert to 0-100 scale)
                if parental_values:
                    parental_avg = sum(parental_values) / len(parental_values) * 5.0  # Convert 0-20 to 0-100
                else:
                    parental_avg = 50.0
                
                # Generate random value with Gaussian distribution
                random_val = random.gauss(50, 15)
                random_val = max(0, min(100, random_val))
                
                # Blend parental and random values (70% genetic, 30% random)
                final_value = (parental_avg * 0.7) + (random_val * 0.3)
                final_value = max(0, min(100, final_value))
                
            else:
                # No parents - pure random generation
                final_value = random.gauss(50, 15)
                final_value = max(0, min(100, final_value))
            
            temperament[trait] = round(final_value, 1)
        
        return temperament

    def crystallize_personality(self):
        """Converts temperament traits to Big 5 personality facets."""
        if not self.temperament:
            return
        
        # Initialize personality structure
        attr_config = {}  # Use default config for random generation
        personality = self._generate_big_five(attr_config)
        
        # Mapping from temperament traits to Big 5 facets
        # Convert 0-100 temperament score to 0-20 facet score
        temperament_to_facet_mapping = {
            # Activity -> Extraversion['Activity']
            "Activity": ("Extraversion", "Activity"),
            # Regularity -> Conscientiousness['Order'] 
            "Regularity": ("Conscientiousness", "Order"),
            # Mood -> Extraversion['Positive Emotions']
            "Mood": ("Extraversion", "Positive Emotions"),
            # Adaptability -> Agreeableness['Compliance']
            "Adaptability": ("Agreeableness", "Compliance"),
            # Threshold -> Neuroticism['Vulnerability'] (Inverse mapping)
            "Threshold": ("Neuroticism", "Vulnerability"),
            # Additional mappings for more comprehensive conversion
            "Intensity": ("Extraversion", "Excitement"),
            "Persistence": ("Conscientiousness", "Self-Discipline"),
            "Approach_Withdrawal": ("Extraversion", "Warmth"),
            "Distractibility": ("Openness", "Ideas")
        }
        
        # Apply temperament mappings to personality facets
        for temp_trait, (big5_trait, facet) in temperament_to_facet_mapping.items():
            if temp_trait in self.temperament:
                temp_value = self.temperament[temp_trait]
                
                # Convert 0-100 to 0-20 scale
                if temp_trait == "Threshold":
                    # Inverse mapping: Low Threshold = High Vulnerability
                    # Threshold 0-100 -> Vulnerability 20-0
                    facet_value = 20 - int((temp_value / 100.0) * 20)
                else:
                    # Direct mapping: 0-100 -> 0-20
                    facet_value = int((temp_value / 100.0) * 20)
                
                # Clamp to valid range
                facet_value = max(1, min(20, facet_value))
                
                # Apply to personality
                personality[big5_trait][facet] = facet_value
        
        # Set the new personality and clear temperament
        self.personality = personality
        self.temperament = None
        self.is_personality_locked = True
        self.plasticity = 0.0

    def get_personality_sum(self, trait):
        """Returns the sum (0-120) of a main trait."""
        if not self.personality:
            return 50  # Neutral fallback for young children without personality
        return sum(self.personality.get(trait, {}).values())

    def _initialize_subjects(self):
        """Initialize academic subjects with natural aptitude based on IQ and personality."""
        subjects = {}
        
        # Get personality facets for calculations (handle None for young children)
        if self.personality:
            openness = self.personality.get("Openness", {})
            conscientiousness = self.personality.get("Conscientiousness", {})
        else:
            # Default values for young children without Big 5 personality
            openness = {"Ideas": 10, "Aesthetics": 10}
            conscientiousness = {"Competence": 10}
        
        # Normalize IQ to 0-100 scale for calculations
        iq_normalized = (self.iq - 50) / 130.0 * 100  # IQ range 50-180 mapped to 0-100
        iq_normalized = max(0, min(100, iq_normalized))
        
        # Calculate natural aptitude for each subject
        subjects["Math"] = {
            "current_grade": 50,  # Start at middle grade
            "natural_aptitude": min(100, max(0, (iq_normalized * 0.4) + (conscientiousness.get("Competence", 10) * 1.5) + (openness.get("Ideas", 10) * 1.5))),
            "monthly_change": 0.0  # Track last month's change for tooltips
        }
        
        subjects["Science"] = {
            "current_grade": 50,
            "natural_aptitude": min(100, max(0, (iq_normalized * 0.5) + (conscientiousness.get("Competence", 10) * 1.25) + (openness.get("Ideas", 10) * 1.25))),
            "monthly_change": 0.0
        }
        
        subjects["Language Arts"] = {
            "current_grade": 50,
            "natural_aptitude": min(100, max(0, (iq_normalized * 0.4) + (openness.get("Aesthetics", 10) * 1.5) + (conscientiousness.get("Competence", 10) * 1.5))),
            "monthly_change": 0.0
        }
        
        subjects["History"] = {
            "current_grade": 50,
            "natural_aptitude": min(100, max(0, (iq_normalized * 0.3) + (openness.get("Values", 10) * 2.0) + (conscientiousness.get("Competence", 10) * 1.5))),
            "monthly_change": 0.0
        }
        
        return subjects

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
        Updates Lean Mass, Weight, and BMI based on current Height and Athleticism.
        Uses a 'Lean Body Mass Index' (LBMI) abstraction.
        """
        # 1. Determine Base LBMI (Lean Mass / Height^2)
        # Male range: 18 (Skinny) - 24 (Muscular)
        # Female range: 15 (Skinny) - 21 (Muscular)
        base_lbmi = 18.0 if self.gender == "Male" else 15.0
        athletic_bonus = (self.athleticism / 100.0) * 6.0
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
                return
        
        # Fallback for oldest age
        if sorted_reqs:
            self.ap_sleep = sorted_reqs[-1]["hours"]

    @property
    def free_ap(self):
        """Returns available AP."""
        return max(0.0, self.ap_max - self.ap_locked - self.ap_sleep - self.ap_used)

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
        
        # Generate Family & Player (Order matters for genetics)
        self.player = self._setup_family_and_player()
        
        # Generate Classmates (if player is in school)
        if self.player.school:
            self.populate_classmates()
        
        self.history = []
        
        # Event System
        self.pending_event = None  # Active event instance
        self.event_history = []     # IDs of past events
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
        if self.player.strength > 80:
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

        # 4. Luck/Karma Flavor
        if self.player.luck > 90:
            luck_txt = "A double rainbow appeared outside the hospital window just now."
        elif self.player.luck < 20:
            luck_txt = "The hospital power flickered right as {pronoun} was delivered."
        else:
            luck_txt = f"Welcome to the world, {self.player.first_name}."

        # 5. Family Flavor
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
            
            # 1. The Setting (Weather + City Vibe)
            weather = random.choice([
                "a torrential downpour rattling the hospital windows",
                "a sweltering afternoon where the AC is barely working",
                "a quiet, snowy morning",
                "a chaotic night with sirens wailing in the distance",
                "a crisp, golden autumn dawn"
            ])
            intro = f"You enter the world in {self.player.city} during {weather}."
            
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
            elif m.athleticism > 80:
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
                (pers_txt, constants.COLOR_TEXT),
                (luck_txt, constants.COLOR_TEXT)
            ],
            "expanded": True
        }

    def _assign_form_to_student(self, student, index):
        """
        Helper function that returns "A", "B", "C", or "D" based on student position.
        Index 0 (player) gets "A", then distribute evenly across all forms.
        """
        forms = ["A", "B", "C", "D"]
        return forms[index % 4]

    def populate_classmates(self):
        """
        Generates a cohort of students for the player's current class.
        Public method called by school.py upon enrollment.
        """
        school_data = self.player.school
        if not school_data: return
        
        # 1. Set capacity to 80 total students (player + 79 classmates)
        total_capacity = 80
            
        # 2. Identify the Cohort (Player + Existing NPCs)
        cohort = [self.player]
        for npc in self.npcs.values():
            if not npc.school: continue
            if (npc.school["school_id"] == school_data["school_id"] and
                npc.school["year_index"] == school_data["year_index"] and
                npc.school["form_label"] == school_data["form_label"]):
                cohort.append(npc)

        existing_count = len(cohort)
        needed = total_capacity - existing_count
        
        # 3. Generate New Students (if needed) - exactly 79 classmates total
        if needed > 0:
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
                    "is_in_session": school_data["is_in_session"]
                }
                
                cohort.append(classmate)
        
        # 4. Assign Forms to All Students
        # Player gets Form A, distribute remaining students evenly across Forms A, B, C, D
        for i, student in enumerate(cohort):
            student.form = self._assign_form_to_student(student, i)

        # 5. Wire Relationships (The Mesh)
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
                    # Add "Same Form" modifier (+10) for students in the same form
                    self._link_agents(agent_a, agent_b, rel_type, rel_type, "Same Form", 10)
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

    def _get_reproductive_gap(self, repro_conf):
        """Calculates a realistic generation gap using Gaussian distribution."""
        min_rep = repro_conf.get("min_reproductive_age", 16)
        max_rep = repro_conf.get("max_reproductive_age", 45)
        mu = repro_conf.get("avg_reproductive_age", 28)
        sigma = repro_conf.get("reproductive_age_sd", 6)
        
        gap = int(random.gauss(mu, sigma))
        return max(min_rep, min(max_rep, gap))

    def _setup_family_and_player(self):
        """
        Procedurally generates the family tree.
        Algorithm: Backwards Age Calculation -> Forwards Entity Generation.
        """
        agent_conf = self.config["agent"]
        repro_conf = self.config.get("reproduction", {})
        
        # 1. Determine Ages (Backwards from Player)
        player_age = agent_conf.get("initial_age", 0)
        
        # Parents
        father_age = player_age + self._get_reproductive_gap(repro_conf)
        mother_age = player_age + self._get_reproductive_gap(repro_conf)
        
        # Grandparents
        p_gpa_age = father_age + self._get_reproductive_gap(repro_conf)
        p_gma_age = father_age + self._get_reproductive_gap(repro_conf)
        m_gpa_age = mother_age + self._get_reproductive_gap(repro_conf)
        m_gma_age = mother_age + self._get_reproductive_gap(repro_conf)
        
        # Shared Bio Data
        last_name = random.choice(agent_conf["bio"].get("last_names", ["Doe"]))
        country = random.choice(agent_conf["bio"].get("countries", ["Unknown"]))
        city = random.choice(agent_conf["bio"].get("cities", ["Unknown"]))
        
        # --- Generation 2: Grandparents (Lineage Heads) ---
        # Paternal
        p_gpa = self._create_npc(age=p_gpa_age, gender="Male", last_name=last_name, city=city, country=country)
        p_gma = self._create_npc(age=p_gma_age, gender="Female", last_name=last_name, city=city, country=country)
        
        # Affinity Calculation
        aff_p = affinity.calculate_affinity(p_gpa, p_gma)
        # Base Marriage (+40) + Affinity + History Variance (+/- 20)
        score_p = 40 + aff_p + random.randint(-20, 20)
        self._link_agents(p_gpa, p_gma, "Spouse", "Spouse", score_p)
        
        # Maternal
        # Maternal side often has different last name (Grandfather's name)
        mat_last_name = random.choice(agent_conf["bio"].get("last_names", ["Smith"]))
        m_gpa = self._create_npc(age=m_gpa_age, gender="Male", last_name=mat_last_name, city=city, country=country)
        m_gma = self._create_npc(age=m_gma_age, gender="Female", last_name=mat_last_name, city=city, country=country)
        
        aff_m = affinity.calculate_affinity(m_gpa, m_gma)
        score_m = 40 + aff_m + random.randint(-20, 20)
        self._link_agents(m_gpa, m_gma, "Spouse", "Spouse", score_m)
        
        # --- Generation 1: Parents & Aunts/Uncles ---
        
        # 1. Father (Guaranteed Child of Paternal GPs)
        father = self._create_npc(age=father_age, gender="Male", parents=(p_gpa, p_gma), 
                                  last_name=last_name, city=city, country=country)
        self._assign_job(father)
        self._link_parent_child(p_gpa, p_gma, father)

        # 2. Mother (Guaranteed Child of Maternal GPs)
        mother = self._create_npc(age=mother_age, gender="Female", parents=(m_gpa, m_gma),
                                  last_name=mat_last_name, city=city, country=country)
        self._assign_job(mother)
        self._link_parent_child(m_gpa, m_gma, mother)

        # 3. Link Parents
        aff_parents = affinity.calculate_affinity(father, mother)
        score_parents = 40 + aff_parents + random.randint(-20, 20)
        self._link_agents(father, mother, "Spouse", "Spouse", score_parents)

        # 4. Paternal Aunts/Uncles (Siblings of Father)
        # Link them to Mother as In-Laws
        self._generate_siblings_for(father, p_gpa, p_gma, repro_conf, city, country, last_name, in_law=mother)
        
        # 5. Maternal Aunts/Uncles (Siblings of Mother)
        # Link them to Father as In-Laws
        self._generate_siblings_for(mother, m_gpa, m_gma, repro_conf, city, country, mat_last_name, in_law=father)

        # --- Bridge Grandparents ---
        # Formula: Civil_Base (+10) + (Parent_Marriage_Score * 0.5)
        gp_bridge_score = 10 + (score_parents * 0.5)
        
        # Paternal GPA <-> Maternal GPA/GMA
        self._link_agents(p_gpa, m_gpa, "In-Law", "In-Law", gp_bridge_score)
        self._link_agents(p_gpa, m_gma, "In-Law", "In-Law", gp_bridge_score)
        # Paternal GMA <-> Maternal GPA/GMA
        self._link_agents(p_gma, m_gpa, "In-Law", "In-Law", gp_bridge_score)
        self._link_agents(p_gma, m_gma, "In-Law", "In-Law", gp_bridge_score)

        # --- Generation 0: Player & Siblings ---
        
        # 1. Player (Guaranteed Child)
        player = Agent(agent_conf, is_player=True, parents=(father, mother),
                       age=player_age, last_name=last_name, city=city, country=country,
                       time_config=self.config.get("time_management", {}))
        self._link_parent_child(father, mother, player)
        
        # 2. Player Siblings
        # Note: Player takes the "Guaranteed" slot. Extra siblings start at base probability.
        self._generate_siblings_for(player, father, mother, repro_conf, city, country, last_name, is_player_gen=True)
        
        return player

    def _create_npc(self, **kwargs):
        """Helper to instantiate, register, and return an NPC."""
        agent = Agent(self.config["agent"], is_player=False, **kwargs)
        self.npcs[agent.uid] = agent
        return agent

    def _link_parent_child(self, father, mother, child):
        """Links a child to both parents."""
        # Biological Imperative (+50) + Affinity
        # Note: We calculate affinity separately for Father and Mother
        
        aff_f = affinity.calculate_affinity(father, child)
        score_f = 50 + aff_f
        
        aff_m = affinity.calculate_affinity(mother, child)
        score_m = 50 + aff_m
        
        self._link_agents(child, father, "Father", "Child", score_f)
        self._link_agents(child, mother, "Mother", "Child", score_m)

    def _generate_siblings_for(self, focal_child, father, mother, repro_conf, city, country, last_name, is_player_gen=False, in_law=None):
        """
        Generates siblings for the focal_child based on probability decay.
        Also handles Cousin generation if the sibling is an adult (Aunt/Uncle).
        """
        prob = repro_conf.get("sibling_prob_base", 0.25)
        decay = repro_conf.get("sibling_prob_decay", 0.5)
        min_rep = repro_conf.get("min_reproductive_age", 16)
        
        # We are generating the "Next" sibling, so we loop until RNG fails
        while random.random() < prob:
            # Determine Age
            # Sibling must be a valid child of the parents.
            # Parent Age is fixed. Sibling Age = Parent Age - Gap.
            # We use the mother's age as the constraint.
            gap = self._get_reproductive_gap(repro_conf)
            sib_age = mother.age - gap
            
            # Sanity check: Age must be >= 0
            if sib_age < 0:
                prob *= decay
                continue
                
            # Create Sibling
            sib = self._create_npc(age=sib_age, parents=(father, mother),
                                   last_name=last_name, city=city, country=country)
            self._link_parent_child(father, mother, sib)
            
            # Link to Focal Child (Sibling <-> Sibling)
            aff_sib = affinity.calculate_affinity(focal_child, sib)
            # Sibling Base (+20) + Affinity
            score_sib = 20 + aff_sib
            self._link_agents(focal_child, sib, "Sibling", "Sibling", score_sib)

            # Link to In-Law (Sibling-in-Law)
            if in_law:
                aff_il = affinity.calculate_affinity(sib, in_law)
                # In-Law Base (0) + Affinity
                type_sib = "Brother-in-Law" if sib.gender == "Male" else "Sister-in-Law"
                type_il = "Brother-in-Law" if in_law.gender == "Male" else "Sister-in-Law"
                self._link_agents(sib, in_law, type_il, type_sib, aff_il)
            
            # Link to existing siblings of focal child? 
            # Ideally yes, but for MVP we just link to focal. 
            # (The Family Tree layout handles implicit sibling relationships visually via shared parents).
            
            self._assign_initial_schooling(sib)
            self._assign_job(sib)
            
            # --- Cousin Generation (If this sibling is an Aunt/Uncle) ---
            if not is_player_gen and sib.age >= min_rep:
                self._generate_cousins_for(sib, repro_conf, city, country)

            # Decay probability for next sibling
            prob *= decay

    def _generate_cousins_for(self, aunt_uncle, repro_conf, city, country):
        """
        Decides if an Aunt/Uncle has a family (Spouse + Kids).
        """
        # 50% chance to have a family (First kid)
        cousin_prob = repro_conf.get("cousin_prob_base", 0.5)
        
        if random.random() < cousin_prob:
            # 1. Generate Spouse (In-Law)
            # Spouse needs to be roughly same age
            spouse_age = aunt_uncle.age + random.randint(-5, 5)
            spouse_last = random.choice(self.config["agent"]["bio"].get("last_names", ["Jones"]))
            
            spouse = self._create_npc(age=spouse_age, gender="Female" if aunt_uncle.gender == "Male" else "Male",
                                      last_name=spouse_last, city=city, country=country)
            self._assign_job(spouse)
            
            aff_c = affinity.calculate_affinity(aunt_uncle, spouse)
            score_c = 40 + aff_c + random.randint(-20, 20)
            self._link_agents(aunt_uncle, spouse, "Spouse", "Spouse", score_c)
            
            # 2. Generate First Cousin (Guaranteed since we passed the 50% check)
            # Determine parents for the cousin
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
                
                # 3. Generate Additional Cousins (Decaying Probability)
                # Pass c1 as focal to link siblings
                self._generate_siblings_for(c1, father, mother, repro_conf, city, country, father.last_name, is_player_gen=True) 
                # Note: is_player_gen=True prevents infinite recursion of cousins-of-cousins

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
                "is_in_session": True # Assume school is active
            }

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
            child = Agent(agent_conf, is_player=True, parents=(father, mother),
                          age=target_age, last_name=last_name, city=city, country=country,
                          time_config=self.config.get("time_management", {}))
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