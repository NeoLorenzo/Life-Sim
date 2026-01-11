# life_sim/simulation/state.py
"""
Simulation State Module.
Holds the core data model for the simulation.
"""
import logging
import random
from .. import constants

class Agent:
    """
    Represents the primary agent (Player).
    
    Data Contract:
        Inputs: config dictionary (agent section)
        State: age (int), health (int), happiness (int), smarts (int), looks (int)
    """
    def __init__(self, agent_config: dict):
        self.logger = logging.getLogger(__name__)
        
        self.age = agent_config.get("initial_age", 0)
        self.health = agent_config.get("initial_health", 50)
        self.max_health = 100 # Capacity starts at 100
        self.happiness = agent_config.get("initial_happiness", 50)
        self.smarts = agent_config.get("initial_smarts", 50)
        self.looks = agent_config.get("initial_looks", 50)
        self.money = agent_config.get("initial_money", 0)
        
        self._recalculate_max_health()

        self.job = None  # None or dict {"title": str, "salary": int}
        self.is_alive = True
        
        # --- Biography ---
        bio_conf = agent_config.get("bio", {})
        self.gender = random.choice(["Male", "Female"])
        if self.gender == "Male":
            self.first_name = random.choice(bio_conf.get("first_names_male", ["John"]))
        else:
            self.first_name = random.choice(bio_conf.get("first_names_female", ["Jane"]))
        self.last_name = random.choice(bio_conf.get("last_names", ["Doe"]))
        self.country = random.choice(bio_conf.get("countries", ["Unknown"]))
        self.city = random.choice(bio_conf.get("cities", ["Unknown"]))
        
        # --- Appearance ---
        app_conf = agent_config.get("appearance", {})
        self.eye_color = random.choice(app_conf.get("eye_colors", ["Brown"]))
        self.hair_color = random.choice(app_conf.get("hair_colors", ["Brown"]))
        self.skin_tone = random.choice(app_conf.get("skin_tones", ["Fair"]))
        
        # Height Genetics & Growth
        # Potential is determined by gender ranges
        pot_min = 150 if self.gender == "Male" else 140
        pot_max = 200 if self.gender == "Male" else 180
        self.genetic_height_potential = random.randint(pot_min, pot_max)
        
        # Initial Height Calculation (based on start age)
        if self.age >= 20:
            self.height_cm = self.genetic_height_potential
        elif self.age == 0:
            self.height_cm = 50 # Average newborn
        else:
            # Rough linear interpolation for starting mid-childhood
            progress = self.age / 20.0
            self.height_cm = 50 + int((self.genetic_height_potential - 50) * progress)

        self.weight_kg = random.randint(60, 100) if self.gender == "Male" else random.randint(45, 80)

        # --- Extended Attributes ---
        attr_config = agent_config.get("attributes", {})
        
        # Physical
        self.strength = self._rand_attr(attr_config, "strength")
        self.athleticism = self._rand_attr(attr_config, "athleticism")
        self.endurance = self._rand_attr(attr_config, "endurance")
        self.fertility = self._rand_attr(attr_config, "fertility")
        self.libido = self._rand_attr(attr_config, "libido")

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
        self._recalculate_physique()
        
        # Personality
        self.discipline = self._rand_attr(attr_config, "discipline")
        self.willpower = self._rand_attr(attr_config, "willpower")
        self.generosity = self._rand_attr(attr_config, "generosity")
        self.religiousness = self._rand_attr(attr_config, "religiousness")
        self.craziness = self._rand_attr(attr_config, "craziness")
        
        # Hidden
        self.karma = self._rand_attr(attr_config, "karma")
        self.luck = self._rand_attr(attr_config, "luck")
        self.sexuality = random.choice(["Heterosexual", "Homosexual", "Bisexual"]) # Simplified for MVP

        # --- Skills ---
        # Dictionary mapping Skill Name -> Level (0-100)
        self.skills = {} 

        self.logger.info(f"Agent initialized: {self.first_name} {self.last_name} ({self.gender}) from {self.city}, {self.country}")

    def _recalculate_max_health(self):
        """
        Calculates health cap based on age.
        Formula: Quadratic decay ensuring 0 max_health at age 100.
        Curve: 100 - (age^2 / 100)
        """
        # Rule 8: Scientifically-grounded abstraction for Frailty/Senescence
        decay = (self.age ** 2) / 100.0
        self.max_health = int(max(0, 100 - decay))
        # Ensure current health never exceeds the new cap
        if self.health > self.max_health:
            self.health = self.max_health

    def _rand_attr(self, config, name):
        """Helper to get random attribute within config range."""
        return random.randint(config.get(f"{name}_min", 0), config.get(f"{name}_max", 100))

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

class SimState:
    """
    Container for the entire simulation world.
    """
    def __init__(self, config: dict):
        self.config = config
        self.agent = Agent(config["agent"])
        
        # Structure: List of dictionaries
        # [
        #   {"header": ("--- Age 0 ---", COLOR), "events": [("Born", COLOR), ...], "expanded": False},
        #   ...
        # ]
        self.history = []
        
        # Buffer for the current year being simulated
        # Generate Narrative Birth Message
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        birth_month = random.choice(months)
        birth_day = random.randint(1, 28)
        
        pronoun = "He" if self.agent.gender == "Male" else "She"
        possessive = "His" if self.agent.gender == "Male" else "Her"
        obj_pronoun = "him" if self.agent.gender == "Male" else "her"

        # 1. Appearance Reaction
        if self.agent.looks > 85:
            looks_txt = f"The doctor pauses. \"This might be the most beautiful baby I've ever seen.\""
        elif self.agent.looks > 60:
            looks_txt = f"The nurses are cooing over {possessive} {self.agent.eye_color.lower()} eyes."
        elif self.agent.looks < 30:
            looks_txt = f"The mother hesitates before holding {obj_pronoun}. \"{pronoun} has... character.\""
        else:
            looks_txt = f"{pronoun} has {possessive} mother's {self.agent.eye_color.lower()} eyes and {self.agent.hair_color.lower()} hair."

        # 2. Physical/Strength Reaction
        if self.agent.strength > 80:
            phys_txt = f"{pronoun} is gripping the nurse's finger tightly. Surprisingly strong!"
        elif self.agent.health < 40:
            phys_txt = f"{pronoun} is breathing shallowly and looks quite frail."
        else:
            phys_txt = f"{pronoun} is a healthy size, weighing {self.agent.weight_kg}kg."

        # 3. Personality/Behavior Reaction
        if self.agent.craziness > 80:
            pers_txt = f"{pronoun} is screaming uncontrollably and thrashing around!"
        elif self.agent.discipline > 70:
            pers_txt = f"{pronoun} is unusually calm, observing the room silently."
        elif self.agent.smarts > 80:
            pers_txt = f"{pronoun} seems to be focusing intensely on the doctor's face. Very alert."
        else:
            pers_txt = f"{pronoun} is crying softly, looking for warmth."

        # 4. Luck/Karma Flavor
        if self.agent.luck > 90:
            luck_txt = "A double rainbow appeared outside the hospital window just now."
        elif self.agent.luck < 20:
            luck_txt = "The hospital power flickered right as {pronoun} was delivered."
        else:
            luck_txt = f"Welcome to the world, {self.agent.first_name}."

        self.current_year_data = {
            "header": ("--- Life Begins ---", constants.COLOR_LOG_HEADER),
            "events": [
                (f"Name: {self.agent.first_name} {self.agent.last_name}", constants.COLOR_ACCENT),
                (f"Born: {birth_month} {birth_day}, Year 0 in {self.agent.city}, {self.agent.country}", constants.COLOR_TEXT),
                (f"Nurse: \"It's a {self.agent.gender}!\"", constants.COLOR_LOG_POSITIVE),
                (looks_txt, constants.COLOR_TEXT),
                (phys_txt, constants.COLOR_TEXT),
                (pers_txt, constants.COLOR_TEXT),
                (luck_txt, constants.COLOR_TEXT_DIM)
            ],
            "expanded": True
        }

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