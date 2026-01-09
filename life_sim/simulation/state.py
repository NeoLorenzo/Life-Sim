# life_sim/simulation/state.py
"""
Simulation State Module.
Holds the core data model for the simulation.
"""
import logging
import random

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
        self.happiness = agent_config.get("initial_happiness", 50)
        self.smarts = agent_config.get("initial_smarts", 50)
        self.looks = agent_config.get("initial_looks", 50)
        self.money = agent_config.get("initial_money", 0)
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
        self.height_cm = random.randint(150, 200) if self.gender == "Male" else random.randint(140, 180)
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
        self.lean_mass = round(self.weight_kg * (1 - (self.body_fat / 100.0)), 1)
        
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

    def _rand_attr(self, config, name):
        """Helper to get random attribute within config range."""
        return random.randint(config.get(f"{name}_min", 0), config.get(f"{name}_max", 100))

class SimState:
    """
    Container for the entire simulation world.
    """
    def __init__(self, config: dict):
        self.config = config
        self.agent = Agent(config["agent"])
        self.event_log = ["Simulation started."]

    def add_log(self, message: str):
        """Adds a message to the in-game event log."""
        self.event_log.append(message)