# life_sim/simulation/state.py
"""
Simulation State Module.
Holds the core data model for the simulation.
"""
import logging
import random
import uuid
from .. import constants

class Agent:
    """
    Represents a human entity (Player or NPC).
    
    Data Contract:
        Inputs: config dictionary (agent section), **kwargs for overrides
        State: age, health, happiness, smarts, looks, relationships, inventory
    """
    def __init__(self, agent_config: dict, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.uid = str(uuid.uuid4())
        self.is_player = kwargs.get("is_player", False)
        
        # Allow kwargs to override config defaults (for NPCs)
        self.age = kwargs.get("age", agent_config.get("initial_age", 0))
        self.health = kwargs.get("health", agent_config.get("initial_health", 50))
        self.max_health = 100 # Capacity starts at 100
        self.happiness = kwargs.get("happiness", agent_config.get("initial_happiness", 50))
        self.smarts = kwargs.get("smarts", agent_config.get("initial_smarts", 50))
        self.looks = kwargs.get("looks", agent_config.get("initial_looks", 50))
        self.money = kwargs.get("money", agent_config.get("initial_money", 0))
        
        self._recalculate_max_health()

        self.job = None  # None or dict {"title": str, "salary": int}
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
        
        # Personality (Big 5 Model)
        # Structure: { "Main": { "Facet": Value, ... }, ... }
        self.personality = self._generate_big_five(attr_config)
        
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

        self.logger.info(f"Agent initialized ({'Player' if self.is_player else 'NPC'}): {self.first_name} {self.last_name} ({self.gender}) Age {self.age}")

    def _recalculate_max_health(self):
        """
        Calculates health cap based on age using a 3-stage 'Prime of Life' curve.
        1. Childhood (0-20): Grows from 70 to 100.
        2. Prime (20-50): Stays at 100.
        3. Senescence (50-100): Decays quadratically to 0.
        """
        if self.age < 20:
            # Growth Phase: 70 base + 1.5 per year
            self.max_health = int(70 + (1.5 * self.age))
        elif self.age < 50:
            # Prime Phase
            self.max_health = 100
        else:
            # Senescence Phase: 100 - ((age - 50)^2 / 25)
            # At age 50: 100 - 0 = 100
            # At age 75: 100 - 25 = 75
            # At age 100: 100 - 100 = 0
            decay = ((self.age - 50) ** 2) / 25.0
            self.max_health = int(max(0, 100 - decay))

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

    def get_personality_sum(self, trait):
        """Returns the sum (0-120) of a main trait."""
        return sum(self.personality.get(trait, {}).values())

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
        self.player = Agent(config["agent"], is_player=True)
        self.npcs = {} # uid -> Agent
        
        # Generate Family
        self._generate_parents()
        
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
        # Map old attributes to new Big 5 Facets (Range 0-20)
        if self.player.personality['Neuroticism']['Angry Hostility'] > 15:
            pers_txt = f"{pronoun} is screaming uncontrollably and thrashing around!"
        elif self.player.personality['Conscientiousness']['Self-Discipline'] > 15:
            pers_txt = f"{pronoun} is unusually calm, observing the room silently."
        elif self.player.smarts > 80:
            pers_txt = f"{pronoun} seems to be focusing intensely on the doctor's face. Very alert."
        else:
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
            marital_happiness = f.relationships[m.uid]['value']
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
            if m.age < 20:
                mom_txt = f"Your mother, {m.first_name} ({m.age}), looks terrified, clutching the bedsheets like she wants to run away."
            elif m.personality['Openness']['Fantasy'] > 18 and m.personality['Neuroticism']['Anxiety'] > 15:
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
            elif f.personality['Neuroticism']['Anxiety'] > 18 and f.personality['Openness']['Ideas'] > 15:
                dad_txt = f"Your father, {f.first_name}, is inspecting your fingers and toes, muttering about government tracking chips."
            elif f.personality['Neuroticism']['Vulnerability'] > 18:
                dad_txt = f"Your father, {f.first_name}, is currently unconscious on the floor after fainting at the sight of the umbilical cord."
            elif f.job and f.job['title'] == "Software Engineer":
                dad_txt = f"Your father, {f.first_name}, is already typing your birth weight into a spreadsheet on his laptop."
            elif f.personality['Agreeableness']['Altruism'] > 18:
                dad_txt = f"Your father, {f.first_name}, has somehow managed to order pizza for the entire maternity ward."
            else:
                dad_txt = f"Your father, {f.first_name} ({f.age}), stands awkwardly by the bedside, afraid he might break you if he touches you."

            parents_txt = f"{intro} {vibe} {mom_txt} {dad_txt}"

        self.current_year_data = {
            "header": ("--- Life Begins ---", constants.COLOR_LOG_HEADER),
            "events": [
                (f"Name: {self.player.first_name} {self.player.last_name}", constants.COLOR_ACCENT),
                (f"Born: {birth_month} {birth_day}, Year 0 in {self.player.city}, {self.player.country}", constants.COLOR_TEXT),
                (parents_txt, constants.COLOR_TEXT),
                (f"Nurse: \"It's a {self.player.gender}!\"", constants.COLOR_LOG_POSITIVE),
                (looks_txt, constants.COLOR_TEXT),
                (phys_txt, constants.COLOR_TEXT),
                (pers_txt, constants.COLOR_TEXT),
                (luck_txt, constants.COLOR_TEXT_DIM)
            ],
            "expanded": True
        }

    @property
    def agent(self):
        """Backward compatibility for logic/renderer until refactor is complete."""
        return self.player

    def _generate_parents(self):
        """Generates Mother and Father and links them."""
        # Father
        f_age = self.player.age + random.randint(18, 45)
        father = Agent(self.config["agent"], 
                       is_player=False, 
                       gender="Male", 
                       age=f_age,
                       last_name=self.player.last_name,
                       city=self.player.city,
                       country=self.player.country)
        self._assign_job(father)
        self.npcs[father.uid] = father
        
        # Mother
        m_age = self.player.age + random.randint(18, 40)
        mother = Agent(self.config["agent"], 
                       is_player=False, 
                       gender="Female", 
                       age=m_age,
                       last_name=self.player.last_name,
                       city=self.player.city,
                       country=self.player.country)
        self._assign_job(mother)
        self.npcs[mother.uid] = mother
        
        # Link Relationships
        # Player <-> Father
        self._link_agents(self.player, father, "Father", "Child", 100)
        # Player <-> Mother
        self._link_agents(self.player, mother, "Mother", "Child", 100)
        # Father <-> Mother
        self._link_agents(father, mother, "Spouse", "Spouse", random.randint(60, 100))

    def _assign_job(self, npc):
        """Assigns a random suitable job to an NPC."""
        jobs = self.config.get("economy", {}).get("jobs", [])
        if not jobs: return
        
        # Filter by smarts
        valid_jobs = [j for j in jobs if npc.smarts >= j.get("min_smarts", 0)]
        if valid_jobs:
            npc.job = random.choice(valid_jobs)
            # Give them some savings based on age/salary
            years_worked = max(0, npc.age - 18)
            npc.money = int(npc.job['salary'] * years_worked * 0.1) # Saved 10%

    def _link_agents(self, a, b, type_a_to_b, type_b_to_a, value):
        """Bi-directional relationship linking."""
        a.relationships[b.uid] = {
            "type": type_a_to_b, 
            "value": value, 
            "name": b.first_name,
            "is_alive": b.is_alive
        }
        b.relationships[a.uid] = {
            "type": type_b_to_a, 
            "value": value, 
            "name": a.first_name,
            "is_alive": a.is_alive
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