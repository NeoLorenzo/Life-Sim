# Life-Sim

**Life-Sim** is a modular, extensible life simulation engine built in Python. It simulates the biological, economic, and social trajectory of a single agent within a deterministic, configuration-driven world. The project emphasizes statistical realism, emergent behavior, and strict separation of concerns between simulation logic and visualization.

## 🚀 Current Features (MVP 0.5)

### Core Simulation & Architecture
*   **Deterministic Simulation Loop:**
    *   **Master Seed:** The entire simulation (Python `random`, `numpy.random`) is initialized via a single integer seed defined in `config.json`, ensuring 100% reproducibility for debugging and sharing runs.
    *   **Turn-Based Logic:** The simulation advances in **1-month increments** (`process_turn`).
        *   **Date Tracking:** The system now tracks the specific Month and Year (starting Jan 2025), allowing for seasonal events and precise timeline management.
        *   **Age Calculation:** Age is stored as `age_months`. The "Age X" log headers are triggered specifically on the agent's birth month, decoupling biological age from the calendar year.
    *   **Event Logging:** A dual-channel logging system writes runtime events to both the console (stdout) and rotating log files (`logs/run_YYYYMMDD_HHMMSS.log`) with the format `Time | Level | Module | Message`.
*   **Dynamic Action Point (AP) System:**
    *   **The "Typical Day" Abstraction:**
        *   **Resource Model:** Time is modeled as a finite resource of **24.0 Action Points (AP)** per turn, representing the agent's "Average Daily Routine" for that month. 1.0 AP equates to 1 hour of daily activity.
        *   **Turn Reset:** At the start of every month (`process_turn`), the AP budget is fully reset, allowing for fresh allocation based on the agent's current life stage.
    *   **Configuration-Driven Biology:**
        *   **`time_management` Config:** Sleep requirements are not hardcoded. They are defined in `config.json` via age brackets (e.g., `Infant: 14h`, `Child: 10h`, `Teen: 9h`, `Adult: 8h`).
        *   **Dynamic Recalculation:** Upon every birthday, the agent's `_recalculate_ap_needs()` method queries the config to adjust their **Maintenance AP** (Sleep), automatically unlocking more "Free Time" as they grow from infancy to adulthood.
    *   **State Management:**
        *   **Locked AP:** Reserved for mandatory obligations (School, Work).
        *   **Maintenance AP:** Reserved for biological needs (Sleep).
        *   **Free AP:** The calculated remainder (`24.0 - Locked - Maintenance - Used`) available for player agency.
    *   **Visual Dashboard (`APBar` Widget):**
        *   **24-Segment Grid:** A dedicated UI element in the Left Panel visualizes the 24-hour day as distinct blocks.
        *   **Color-Coded Allocation:**
            *   **Blue (Right-Aligned):** Sleep/Maintenance hours.
            *   **Red (Left-Aligned):** Locked obligations (School/Work).
            *   **Gray:** Time already spent on voluntary actions.
            *   **Green:** The remaining "Free" budget available for gameplay.
        *   **Feedback:** A text label dynamically updates to show exact availability (e.g., *"Time: 7.0h Free / 9.0h Sleep"*).
*   **Configuration-Driven Design:**
    *   **No Magic Numbers:** All gameplay variables (initial stats, costs, salary multipliers) are loaded from `config.json`.
    *   **Static Constants:** Visualization settings (Screen Size, Colors, FPS) and Time settings (Start Year, Month Names) are decoupled in `constants.py`.
*   **Multi-Agent Architecture:**
    *   **Unified Entity Model:** The `Agent` class supports both the **Player** and **NPCs** (Non-Player Characters). All agents share the same biological DNA (Attributes, Health, Inventory), distinguished only by an `is_player` flag and unique UUIDs.
    *   **Full Fidelity Simulation (Unified Loop):** The "Truman Show" optimization has been removed in favor of total simulation parity. NPCs now process the exact same biological, economic, and time-management logic as the Player every month.
        *   **Shared Economy:** NPCs earn monthly salaries, accumulate wealth, and pay costs exactly like the player.
        *   **Automated Routine:** NPCs possess a simulated Action Point (AP) budget. A passive routine automatically "spends" their AP on mandatory obligations (Work, School, Sleep) to maintain a valid state for future AI decision-making.
    *   **Desynchronized Aging:** NPCs are initialized with randomized birth months (0-11 offset) to ensure biological updates occur naturally throughout the year rather than synchronizing perfectly with the player's birthday.

### Identity & Biology
*   **Procedural Generation & Genetics:**
    *   **Lineage System:** Distinguishes between **Lineage Heads** (First Generation, procedurally generated) and **Descendants** (Next Generation, inherited traits).
    *   **Bio-Data:** Agents are initialized with a First Name, Last Name, Gender, Country, and City. Descendants inherit Last Name, City, and Country from parents.
    *   **Appearance Inheritance:**
        *   **Pigmentation:** Skin Tone is calculated by blending parental values with slight variance. Eye and Hair colors use probabilistic inheritance (45% Father, 45% Mother, 10% Mutation).
    *   **Procedural Family Generation:**
        *   **Algorithm:** Implements a "Backwards Age, Forwards Genetics" approach.
            *   *Age Calculation:* Ages are determined top-down starting from the Player (Age 0) -> Parents -> Grandparents using a **Gaussian Distribution** (Mean 28, SD 6) clamped to reproductive limits (16-45). This ensures realistic generational gaps.
            *   *Entity Instantiation:* Agents are created bottom-up (Grandparents -> Parents -> Player) to ensure valid genetic inheritance references exist at instantiation.
        *   **Refined Psychometric Affinity System:**
            *   **Deterministic Architecture:** Relationships are strictly deterministic based on Seed and Personality, with no randomness in initial calculations.
            *   **The Gravity Model:** Relationships are modeled as `Total_Score = Base_Affinity + Sum(Active_Modifiers)`.
                *   **Base Affinity:** The permanent psychometric compatibility between two personalities, calculated using the refined affinity engine.
                *   **Active Modifiers:** Contextual buffs/debuffs that temporarily or permanently alter the score (e.g., Maternal Bond, Marriage).
            *   **Enhanced Calculation System:**
                *   **Actor Effects (Individual Traits):** 
                    *   *Neuroticism:* Threshold-based penalty above 70, scaling at 0.5x the excess value. High neuroticism actively drags down all relationships.
                    *   *Agreeableness:* Threshold-based bonus above 70, scaling at 0.5x the excess value. High agreeableness provides universal social lubrication.
                *   **Dyadic Effects (Similarity/Homophily):** 
                    *   *Openness:* Shared interests vs. value clashes using `(20 - delta) * 0.8` weighting. Small differences create bonuses, large differences create penalties.
                    *   *Conscientiousness:* Lifestyle sync vs. clashes using `(20 - delta) * 0.8` weighting. Measures compatibility in organization and life approach.
                    *   *Extraversion:* Energy match using `(20 - delta) * 0.5` weighting. Rewards similar energy levels between agents.
            *   **Detailed Breakdown System:** The affinity engine provides comprehensive mathematical breakdowns showing exactly how each personality factor contributes to the final score, with clear labeling of positive ("Shared Interests") and negative ("Value Clash") effects.
        *   **Expanded Relationship Range:** The social data model supports a range of **`-100` to `+100`**.
        *   **Structural Modifiers (The "Bond" System):**
            *   Instead of arbitrary "Base Values," relationships are initialized with specific **Structural Modifiers** that represent social contracts.
            *   **Maternal/Paternal Bond:** **+80** (Permanent). This massive buffer allows parents to love even "difficult" children, though extreme personality clashes can still drag the total score down over time.
            *   **Marriage Bond:** **+60** (Permanent). Represents the commitment of marriage.
            *   **Sibling Bond:** **+30** (Permanent).
            *   **Civil/In-Law:** **+10** (Permanent).
        *   **Extended Family & In-Law Topology:**
            *   **The Grandparent Bridge:** Paternal and Maternal sides of the family are now linked. Grandparents have "In-Law" relationships with their counterparts.
            *   **Marriage-Driven Sentiment:** The starting score for Grandparent-In-Laws is calculated as `Civil_Base (+10) + (Parent_Marriage_Score * 0.5)`. If the parents have a toxic marriage, the extended family network naturally fractures as grandparents "take sides."
            *   **Siblings-in-Law:** Aunts and Uncles are automatically linked to their siblings' spouses (In-Laws) using the affinity engine.
    *   **Anthropometry & Growth:**
        *   **Height Inheritance:**
            *   *Lineage Heads:* Generated via Gaussian distribution (Male: 176cm/7SD, Female: 163cm/6SD).
            *   *Descendants:* Implements the **Mid-Parental Height Formula**: `(Father + Mother +/- 13) / 2`. A Gaussian variance (SD 5cm) is applied to simulate regression to the mean.
        *   **Dynamic Growth:** Agents are born at ~50cm. Growth is simulated stochastically (20% chance per month to gain 1cm) towards their `genetic_height_potential` until **Age 20**.
        *   **Senescence Shrinkage:** After **Age 60**, agents have a 3% monthly chance to lose 1cm of height due to spinal compression.
        *   **Physique (LBMI Model):** Weight is strictly derived, not random.
            *   **Lean Body Mass Index (LBMI):** Calculated as `Base_LBMI (M:18/F:15) + (Athleticism * 0.06)`.
            *   **Body Fat %:** Calculated as `Base_BF (M:25/F:35) - (Athleticism * 0.18) + Variance`.
            *   **Mass Calculation:** `Total Weight = (LBMI * Height²) / (1 - BodyFat%)`. This ensures high-athleticism agents are heavier due to muscle, not fat.
*   **Universal Attribute System:**
    *   **IQ:** Replaces "Smarts" with a Gaussian distribution (Mean 100, SD 15).
    *   **Attributes (0-100 Scale):**
        *   **Physical:** Strength, Athleticism, Endurance.
    *   **Hormonal Curves (Genotype vs. Phenotype):**
        *   **Genotype:** Agents are born with a hidden `_genetic_peak` (0-100) for Fertility and Libido.
        *   **Phenotype:** The expressed value is recalculated annually via `_recalculate_hormones()`:
            *   *Puberty (12-18):* Linear ramp-up from 0% to 100% of genetic peak.
            *   *Female Fertility:* Prime (15-30), Decline (30-45), Menopause (45-50), Sterile (50+).
            *   *Male Fertility:* Prime (18-40), followed by slow linear decay (never reaching 0).
            *   *Libido:* Spikes during "Hormonal Storm" (13-18), plateaus until 35, then decays by 1.5% annually.
    *   **Personality (Big Five Model):** A deep psychological simulation based on the OCEAN model.
        *   **Structure:** 5 Main Traits, each composed of 6 specific sub-facets.
        *   **Scoring:** Facets range from 0-20; Main Traits range from 0-120.
        *   **Visualization:** The Attribute Modal displays the full psychometric profile with color-coded values (Green for high positive traits, Red for high negative traits like Neuroticism).
        *   **1. Openness to Experience:** Appreciation for art, emotion, adventure, and unusual ideas.
            *   *Fantasy:* Having a vivid imagination and an active dream life.
            *   *Aesthetics:* Deep appreciation for art, music, poetry, and beauty in nature.
            *   *Feelings:* Receptivity to one's own inner feelings and emotions; valuing emotional depth.
            *   *Actions:* Willingness to try different activities, go to new places, or eat unusual foods.
            *   *Ideas:* Intellectual curiosity; an active interest in abstract concepts and philosophical debates.
            *   *Values:* Readiness to re-examine social, political, and religious values (opposite of dogmatism).
        *   **2. Conscientiousness:** Tendency to be self-disciplined, organized, and achievement-oriented.
            *   *Competence:* Belief in one’s own self-efficacy; feeling capable and sensible.
            *   *Order:* Personal organization; a preference for schedules, lists, and tidiness.
            *   *Dutifulness:* Emphasis on ethical principles and fulfilling moral obligations.
            *   *Achievement Striving:* The drive to hit goals, work hard, and be successful.
            *   *Self-Discipline:* The ability to persist at difficult or boring tasks despite distractions.
            *   *Deliberation:* Tendency to think carefully before acting; caution and impulse control.
        *   **3. Extraversion:** Energy, positive emotions, surgency, and the tendency to seek stimulation in the company of others.
            *   *Warmth:* Interest in and friendliness towards others; ease of forming attachments.
            *   *Gregariousness:* Preference for the company of others; enjoying crowds and social stimulation.
            *   *Assertiveness:* Social dominance; forcefulness of expression and leadership ability.
            *   *Activity:* Pace of living; level of energy and busyness.
            *   *Excitement-Seeking:* Need for environmental stimulation, thrills, and risk.
            *   *Positive Emotions:* Tendency to experience happiness, joy, excitement, and optimism.
        *   **4. Agreeableness:** Tendency to be compassionate and cooperative rather than suspicious and antagonistic.
            *   *Trust:* Belief in the sincerity and good intentions of others.
            *   *Straightforwardness:* Frankness, sincerity, and ingenuity (avoiding manipulation).
            *   *Altruism:* Active concern for the welfare of others; generosity and willingness to help.
            *   *Compliance:* Response to interpersonal conflict; tendency to defer to others rather than compete.
            *   *Modesty:* Tendency to play down one's own achievements and be humble.
            *   *Tender-Mindedness:* Attitude of sympathy and concern for others; governed by emotion rather than cold logic.
        *   **5. Neuroticism:** Tendency to experience negative emotions like anger, anxiety, or depression.
            *   *Anxiety:* Tendency to be apprehensive, fearful, prone to worry, and nervous.
            *   *Angry Hostility:* Tendency to experience anger and related states like frustration and bitterness.
            *   *Depression:* Tendency to experience feelings of guilt, sadness, despondency, and loneliness.
            *   *Self-Consciousness:* Sensitivity to criticism and feelings of inferiority; shyness or social anxiety.
            *   *Impulsiveness:* Inability to control cravings and urges.
            *   *Vulnerability:* Inability to cope with stress; becoming dependent, hopeless, or panicked in difficult situations.
    *   **Hidden:** Karma, Luck, Sexuality (Hetero/Homo/Bi).
*   **Derived Metrics (Physiology):**
    *   **Body Fat %:** Calculated dynamically based on Gender and Athleticism.
        *   *Formula:* `Base_BF (M:25/F:35) - (Athleticism% * 18) + Random_Variance(-3 to +5)`.
        *   *Constraint:* Minimum 4.0%.
    *   **Lean Mass:** Calculated dynamically (`LBMI * Height²`).
    *   **BMI:** Automatically calculated to track physical condition.
*   **Aging & Mortality:**
    *   **The "Prime of Life" Curve:** `max_health` is not static.
        *   *Childhood (0-20):* Capacity grows linearly from 70 to 100.
        *   *Prime (20-50):* Capacity peaks at 100.
        *   *Senescence (50+):* Capacity decays quadratically ($100 - (age-50)^2/25$), hitting 0 at age 100.
    *   **Death Condition:** If Health drops to $\le 0$, the `is_alive` flag is set to `False`, and further actions are blocked.
    *   **Natural Entropy:** NPCs over age 50 experience slight random health decay **monthly**, creating a high-mortality window that ensures natural death occurs variably rather than strictly at the mathematical cap.

### Economy & Career
*   **Job Market:**
    *   **Data Structure:** Jobs are defined in `config.json` with a `title` and `salary`.
    *   **Application Logic:** The "Find Job" action picks a random job from the pool. Success is currently guaranteed (requirements removed for IQ refactor).
    *   **Age Restriction:** Agents cannot apply for jobs until **Age 16**.
    *   **Income:** Salaries are distributed monthly (`Salary / 12`) during the `process_turn` phase, simulating realistic cash flow.
    *   **NPC Savings Initialization:** Upon generation, adult NPCs are assigned a starting cash balance calculated as `10% of Salary * Years Worked (Age - 18)`, simulating prior life savings.
*   **Active Income (Overtime):**
    *   **Mechanic:** Employed agents can manually "Work Overtime."
    *   **Reward:** Immediate cash bonus equal to **1%** of the annual salary.
    *   **Constraint:** Action is blocked if the agent is unemployed.

### Education System
*   **Persistent School Entity:**
    *   **The Royal British College of Lisbon:** The simulation now instantiates a specific school object with defined metadata (Tuition: €18,000, Uniform Policy, Location).
    *   **Hierarchical Structure:** Grades are no longer a flat list but are grouped into logical **Stages** (Early Years, Primary, Secondary, Sixth Form), allowing for future rule differentiation (e.g., Uniforms optional in Sixth Form).
*   **The Cohort System:**
    *   **Form Assignment:** Upon enrollment, agents are assigned to a specific **Form** (e.g., "Year 7**B**").
    *   **Static Groups:** This assignment is persistent. If a player starts in the "B" stream, they remain in the "B" stream until graduation, simulating a stable peer group.
    *   **Structure:** Configured for **3 Forms per Year** (A, B, C) with a capacity of **20 students** each.
*   **Academic Calendar:**
    *   **Timeline:** School runs independently of biological age, operating on a **September to June** cycle.
    *   **Status:** Tracks "In Session" vs. "Summer Break" states.
*   **Subject-Based Academic System:**
    *   **Four Core Subjects:** Math, Science, Language Arts, and History replace the single performance score.
    *   **Natural Aptitude Calculation:** Each subject's aptitude is calculated based on IQ and Big 5 personality traits:
        *   **Math:** (IQ × 0.4) + (Conscientiousness × 0.3) + (Openness[Ideas] × 0.3)
        *   **Science:** (IQ × 0.5) + (Conscientiousness × 0.25) + (Openness[Ideas] × 0.25)
        *   **Language Arts:** (IQ × 0.4) + (Openness[Aesthetics] × 0.3) + (Conscientiousness × 0.3)
        *   **History:** (IQ × 0.3) + (Openness[Values] × 0.4) + (Conscientiousness × 0.3)
    *   **Deterministic Grade Progression:** Grades change monthly based purely on natural aptitude, removing random fluctuations:
        *   **Formula:** `(natural_aptitude - 50) × 0.02` per month
        *   **High aptitude (80):** +0.6 monthly improvement
        *   **Average aptitude (50):** No change
        *   **Low aptitude (20):** -0.6 monthly decline
        *   **Perfect aptitude (100):** +1.0 monthly improvement
    *   **Monthly Change Tracking:** Each subject tracks its monthly change for tooltip display, showing progression patterns.
*   **Interactive Academic Dashboard:**
    *   **Left Panel Display:** When enrolled in school, the left dashboard shows an "Academics" section with all four subjects and their current grades.
    *   **Color-Coded Performance:** Grades are color-coded for quick visual assessment:
        *   **90-100:** Green (Excellent)
        *   **70-89:** Blue (Good)
        *   **50-69:** Yellow (Average)
        *   **<50:** Red (Poor)
    *   **Vertical Layout:** Each subject appears on its own line to prevent wrapping issues and ensure readability within panel bounds.
    *   **Interactive Tooltips:** Hovering over any grade reveals detailed information:
        *   Current grade and subject name
        *   Natural aptitude score
        *   Monthly change with color-coded direction (green for positive, red for negative)
        *   Smart positioning to stay within screen boundaries
    *   **Top-Layer Rendering:** Tooltips render on top of all other UI elements, including modals, ensuring visibility.
*   **Progression:**
    *   **Immediate Enrollment:** Agents are automatically enrolled in the appropriate grade level immediately upon generation.
    *   **Overall Performance:** Calculated as the average of all subject grades for backward compatibility with existing systems.
    *   **Pass/Fail Logic:**
        *   *Threshold:* Overall performance must be **> 20** to pass a grade.
        *   *Failure:* Results in repeating the year and a **-20 Happiness** penalty.
        *   *Graduation:* Completing the final year (Year 13) awards a **+20 Happiness** boost and removes the "School" status.
*   **Comprehensive Classmate Generation:**
    *   **Dynamic Population System:** The school now fully populates the form with complete NPC cohorts. When the player enrolls or advances to a new grade, the system generates all missing classmates to fill the form capacity (20 students per form).
    *   **Generic Lineage Factory:** Utilizes the `_generate_lineage_structure()` method to create fully-realized NPC classmates with complete family trees, genetic inheritance, and personality profiles.
    *   **Forced Enrollment:** Generated classmates are automatically assigned to the same school, stage, year, and form as the player, ensuring a cohesive peer group.
    *   **Relationship Meshing:** The system automatically establishes relationships between all classmates in a cohort, creating a realistic social web where every student knows every other student, not just the player.
    *   **Affinity-Driven Relationships:** Classmate relationships are determined by the refined affinity calculation system, resulting in natural social dynamics (Classmates, Acquaintances, Rivals) based on personality compatibility.

### Actions & Progression
*   **Healthcare (Doctor):**
    *   **Cost:** Flat fee of **$100**.
    *   **Effect:** Restores Health by a random value of **10 to 20** (clamped to the current `max_health`).
    *   **Constraints:** Action fails if `Agent.money < 100`.
*   **Toggle Attributes:**
    *   A UI-only action that pauses the log view to inspect the full list of 15+ agent attributes (Identity, Physical, Personality, Skills).

### User Interface & Visualization
*   **Technical Specs:**
    *   **Resolution:** Fixed **1920x1080** window.
    *   **Framerate:** Capped at 60 FPS.
    *   **Theme:** Dark Mode (Background: RGB 20,20,20; Panels: RGB 40,40,40).
*   **Three-Panel Layout:**
    *   **Left Panel (300px):** Real-time dashboard showing Name, Age (Years + Months), Current Date (Month/Year), Money, Job, Vitals (Health/Happiness/IQ/Looks), and Physical Energy.
    *   **Center Panel (Variable):**
        *   **Advanced Narrative Engine:** The `SimState` initialization logic synthesizes Weather, City Atmosphere, Household Wealth, and Parental Personality (Big 5) to generate a unique, cohesive opening paragraph.
            *   **Context Awareness:** Accounts for specific scenarios like "Teen Mom," "Old Father," or "Neurotic Parents."
            *   **Grandparent Presence:** The engine now checks the relationship status of all four grandparents. It dynamically generates flavor text describing their presence (e.g., *"Your maternal grandfather is handing out cigars"*) or their absence/tension (e.g., *"Your paternal grandmother is present but refuses to look at your mother"*) based on their relationships with your parents.
        *   **LogPanel Widget:**
            *   **Smart Wrapping:** Text is dynamically wrapped based on font size and panel width.
            *   **Collapsible History:** The log is structured hierarchically. Clicking year headers (e.g., `[-] Age 5`) toggles the `expanded` state in the history buffer, hiding/showing events for that year.
        *   **Attribute Modal:**
            *   **Detailed Columns:** Renders 4 columns: Vitals/Physical, Openness/Conscientiousness, Extraversion/Agreeableness, and Neuroticism.
            *   **Economic Visibility:** The **Vitals** column now includes **Money** for all agents, allowing the player to verify the economic progress of NPCs (parents saving money, siblings earning wages).
            *   **Pinning System:** Clicking any attribute card toggles it into the **Pinned Attributes** list on the Left Panel (Dashboard), allowing players to track specific stats (e.g., "Fitness") without reopening the modal.
            *   **Visual Feedback:** Neuroticism traits use inverted color logic (High = Red, Low = Green), while positive traits use standard logic.
            *   **Interactive Family Tree (Modal):**
                *   **Topology:** Uses a **Layered Graph** approach with **Virtual Marriage Hubs** to handle complex relations (half-siblings, in-laws).
                *   **Relationship Filtering:** The BFS traversal algorithm filters relationships to only include direct family connections (Father, Mother, Child, Spouse), preventing the merging of separate family trees that occurred through "In-Law" bridge relationships.
                *   **Layout Algorithm:**
                    1.  **Harvest:** BFS traversal from the focus agent to find all relatives.
                    2.  **Rank:** Assigns generations relative to the focus (Parents = +1, Children = -1).
                    3.  **Ordering:** Uses **Ancestry-Based Sorting** to keep family units (spouses and children) vertically aligned under their grandparents.
                    4.  **Relaxation:** Runs 5 iterations of a force-directed sweep (Down/Up) to center parents over children and resolve collisions.
                *   **Rendering:** Draws **Orthogonal Edges** (Manhattan geometry). Spousal links connect bottom-to-center; Parent-Child links use a "Bus" style routing.
                *   **Visual Distinction:** Nodes feature dynamic borders to distinguish relationships: **Solid Borders** indicate blood relatives (sharing a common ancestor), while **Dashed Borders** indicate in-laws or spouses.
                *   **Controls:**
                    *   **Left-Drag:** Pan the view (infinite canvas).
                    *   **Left-Click:** Refocus the tree on the clicked relative.
                    *   **Right-Click:** Close tree and open the **Attribute Modal** for the clicked relative.
            *   **Interactive Social Map (Modal):**
                *   **Advanced Physics Engine:** A real-time **Force-Directed Graph** simulation using NumPy with dynamic force scaling.
                    *   **Attraction Scaling:** The spring force between nodes is weighted by relationship strength using tiered multipliers (Weak: 0.5x-2.0x, Moderate: 2.0x-6.0x, Strong: 6.0x-10.0x), causing close-knit families and spouses to snap together into tight clusters.
                    *   **Hostile Repulsion:** Negative relationships (Enemies) act as active repulsors. The engine transforms the spring force into a repulsive force, ensuring that rivals and enemies actively push away from each other on the canvas.
                    *   **Balanced Forces:** Carefully tuned repulsion (50.0) and attraction (2.0) constants ensure relationship-based forces have meaningful impact without overwhelming the physics.
                *   **Advanced Navigation & Interaction:**
                    *   **Zoom Controls:** Mouse wheel zoom in/out (0.2x to 5.0x) centered on the modal, with nodes and edges scaling proportionally while text remains constant size for readability.
                    *   **Infinite Canvas Panning:** Click and drag background to pan around the graph.
                    *   **Physics Interaction:** Users can drag nodes to fling them around the canvas; the physics engine reacts elastically.
                    *   **Precise Hover Detection:** Hover mechanics properly account for zoom level, ensuring accurate node and edge selection at any magnification.
                *   **Network Visualization:**
                    *   **Nodes:** Represent agents. The Player is distinct (White), while NPCs are color-coded by their relationship to the player (Green=Friend, Red=Enemy, Gray=Stranger).
                    *   **Edges:** Dynamic lines representing relationships. **Thickness** indicates intensity (magnitude of the score), and **Color** uses linear interpolation between Gray (Neutral), Bright Green (Best Friend), and Deep Red (Nemesis).
                *   **Filters & Controls:**
                    *   **Population Toggle:** Switch between "Show Known" (Player's immediate circle) and "Show All" (The entire simulation population).
                    *   **Network Toggle:** Switch between "Direct Links" (Only Player connections) and "All Links" (Visualizing the complete web of NPC-NPC relationships).
                *   **Interactivity:**
                    *   **Physics Interaction:** Users can drag nodes to fling them around the canvas; the physics engine reacts elastically.
                    *   **Navigation:** Infinite canvas panning via background drag.
                    *   **Rich Node Tooltips:** Hovering over a node displays a detailed overlay with Name, Age, Job, and precise Relationship stats.
                    *   **Interactive Edge Highlighting:** Hovering over a relationship line visually highlights it (glows bright yellow and thickens), making it easy to select specific connections in a dense social web.
                    *   **Detailed Edge Tooltips (The "Math of Love"):** Hovering over the connection line between any two agents reveals the full mathematical breakdown of their relationship:
                        *   **Base Affinity:** Displays the raw psychometric score, explicitly listing factors like *"Value Clash (Openness): -12.5"* or *"Neuroticism Penalty: -5.0"*.
                        *   **Active Modifiers:** Lists all currently active buffs/debuffs (e.g., *"Maternal Bond: +80.0"*), allowing the player to see exactly why a relationship exists.
    *   **Right Panel (300px):**
        *   **Tabbed Navigation:** Actions are organized into switchable categories (**Main**, **Social**, **Assets**).
        *   **Dynamic Visibility:** Buttons appear/disappear based on context (e.g., "Find Job" hidden <16, "Work Overtime" hidden if unemployed).
        *   **Auto-Layout:** The interface automatically restacks buttons to fill gaps when items are hidden.
        *   **Social Dashboard:** The Social Tab now features a **Relationship List**.
        *   **Bi-directional Relationship Bars:** UI cards now feature a center-aligned bar.
            *   **Positive:** Fills **Green to the right** (0 to 100).
            *   **Negative:** Fills **Red to the left** (0 to -100).
            *   **Visual Feedback:** This provides immediate visual identification of social standing, distinguishing between a "strained" relationship (short red bar) and a "nemesis" (full red bar).
        *   **Interactive Cards:** Each relationship card includes "Attributes" (to view the NPC's stats), a **Family Tree Icon** (graphical button), and "Interact" buttons.
        *   **Styling:** Buttons feature rounded corners and hover-responsive darkening (RGB 80,80,80). The primary action button is now labeled "Age Up (+1 Month)".

## 🗺️ Roadmap (Planned Features)

The following features are planned to expand the simulation depth into a comprehensive life emulator:

### Core Mechanics: Dynamic Action Point (AP) System
*   **Concept: "The Typical Day":**
    *   **Resource:** A budget of **24.0 Action Points (AP)** per turn, representing the "Average Daily Routine" for that month.
    *   **Granularity:** Supports fractional costs (e.g., 0.5 AP) for micro-tasks.
*   **The Three Buckets:**
    *   **Locked AP (Obligations):** Automatically deducted for School (e.g., 7 AP), Job (8 AP), and Commute.
    *   **Maintenance AP (Biology):** Reserved for Sleep (e.g., 8-14 AP depending on age).
    *   **Free AP:** The remaining balance available for player actions (`24 - Locked - Maintenance`).
*   **"Rule Breaking" (Reclaiming AP):**
    *   **Truancy:** Option to "Skip School/Work" to refund Locked AP into Free AP. *Risk:* Truancy events, grade drops, firing.
    *   **Sleep Deprivation:** Option to "Stay Up Late" (reduce Maintenance AP). *Consequence:* Cumulative Health/Stress penalties if below required sleep threshold.
*   **Spending Logic:**
    *   **Standard Actions:** Study, Gym, Date (~1.0 - 2.0 AP).
    *   **Micro Actions:** Quick Chat, Snack, Social Media (~0.5 AP).
    *   **Constraint:** Actions are disabled if `Cost > Free AP`.
*   **Min-Maxing:**
    *   **Auto-Rest:** Unspent AP converts to extra Sleep/Recovery at the end of the turn.
    *   **Crunch:** Players can sacrifice health (Sleep) for productivity (AP).
*   **Visualization:**
    *   **The Day Bar:** A horizontal UI element showing Red (Locked), Blue (Sleep), and Green (Free) sections.
    *   **Dynamic Updates:** Clicking "Skip School" visually transforms Red segments into Green.

### UX Polish & Advanced UI
*   **Advanced Visualization:**
    *   **Agent Portrait:** A visual representation in the Left Panel based on appearance stats.
*   **Dynamic Menus:**
    *   **Responsive Design:** Support for true full-screen resizing.

### Genetics, Growth & Identity
*   **Legal Identity & Transition:**
    *   **Name Changes:** Ability to visit the courthouse to legally change First or Last name (e.g., to evade a bad reputation or after marriage).
    *   **Gender Identity:** A dedicated identity tab to socially transition (Transgender/Non-Binary) independent of medical surgery. This affects pronouns in the log and relationship reactions from conservative family members.
*   **Medical Transition Protocol:**
    *   **Hormone Replacement Therapy (HRT):** A recurring medical action required for at least 3 years before Gender Reassignment Surgery becomes unlocked.
    *   **Social Consequences:** While on HRT but pre-surgery, family relationship stats fluctuate based on their "Religiousness" and "Generosity."
*   **Dietary System:**
    *   **Diet Plans:** Selectable lifestyles with monthly costs and stat impacts:
        *   *Vegan/Vegetarian:* Increases Karma/Health, slight relationship friction with certain NPCs.
        *   *Keto/Mediterranean:* High cost, boosts Health and Looks.
        *   *Junk Food/Hot Cheetos:* Low cost, rapid Health decay, increases Happiness temporarily.
    *   **Consequences:** Random events triggered by diet (e.g., "Your tapeworm cured your high blood pressure" or "You developed scurvy").
*   **Skill Mastery Mechanics:**
    *   **Practice System:** Logic to learn and level up specific skills (0-100).
    *   **Content:** Instruments, Martial Arts, Licenses (Driving, Pilot, Boating).
*   **Manual Character Creator:** UI to manually select Name, Appearance, and Attributes.
*   **Random Scenario Engine (The "Pop-up" System):**
    *   **Moral Dilemmas:** A procedural event generator that presents the player with A/B/C choices (e.g., "You found a wallet," "A bully insulted you").
    *   **Stat-Based Outcomes:** Choices are not guaranteed to succeed. Trying to "Attack" a bully calculates the winner based on the *Strength* and *Martial Arts* stats of both parties.
    *   **Karma Integration:** Decisions feed directly into the hidden Karma stat, influencing future luck.
*   **Identity Services:**
    *   **Legal Name Change:** Ability to visit the courthouse to change First or Last name (requires fee and no criminal record).
    *   **Gender Identity:** A dedicated identity tab allowing agents to socially transition (pronouns/identity) independent of medical reassignment surgery.
*   **Geopolitical Economy:**
    *   **Socialized Services:** Logic checking the `Country_ID`. If the agent is born in specific countries (e.g., UK, Canada, Norway), "Visit Doctor" and "University" actions are free (tax-funded). In others (USA), they incur high costs.
    *   **Royalty RNG:** In monarchies (Japan, UK, Saudi Arabia, etc.), a tiny RNG chance to be born into the Royal Family, overriding standard parents with Royal NPCs.

### Social Web & Relationships
*   **Family Generation:** Procedural creation of parents, stepparents, and siblings.
*   **Relationship Dynamics:**
    *   **Interactions:** Spend time, conversation, argue, insult, prank, rumor spreading.
    *   **Gifting Engine:** Ability to buy items (flowers, cars, houses) and gift them to NPCs to massively boost relationships.
    *   **Status:** Relationship bars (0-100) fluctuate based on interactions.
*   **Romance & Ex-Partners:**
    *   **Dating:** Apps, blind dates, hookups.
    *   **Partnership:** Engagement, marriage (prenups), eloping, divorce.
    *   **The "Ex" State:** Breakups move NPCs to an "Ex-Partner" list. Exes can randomly stalk the player, beg to get back together, or file restraining orders if the player persists.
    *   **Cheating:** Affairs, paternity tests, confrontation.
*   **Paternity Disputes:**
    *   **DNA Testing:** If a hookup results in pregnancy, the option to "Demand Paternity Test."
    *   **Denial:** NPCs may claim a child is yours when it isn't (or vice versa). Refusing to pay child support for a confirmed child results in automatic salary garnishment and legal trouble.
*   **Advanced Intimacy:**
    *   **Threesomes:** A rare interaction option available only if the partner has high "Craziness" (>80).
    *   **Consequences:** High risk of the partner leaving the agent for the third party, or the third party contracting an STD.
*   **Wedding Complexity:**
    *   **Venue Selection:** Choice between "Courthouse" (Cheap), "Golf Course" (Mid), or "Castle" (Expensive).
    *   **Honeymoon:** Selecting a destination affects the immediate Happiness boost and the post-wedding Relationship bar.
    *   **Prenup Logic:** If the agent is significantly richer than the fiancé, they can demand a prenup. Refusal often leads to the fiancé calling off the wedding.
*   **Reproductive Health:**
    *   **Birth Control:** Toggleable options (Condoms, The Pill) to reduce pregnancy RNG.
    *   **Sterilization:** Medical procedures (Vasectomy, Tubal Ligation) for 0% pregnancy chance.
    *   **STD Mechanics:** Unprotected hookups carry risks of specific diseases (Herpes, HIV, Syphilis) that drain Health until treated.
*   **Progeny:**
    *   **Reproduction:** Pregnancy, birth events, IVF, sperm donors, surrogacy, adoption.
    *   **Parenting:** Interactions affecting offspring stats; disowning children.
*   **Social Circles:** Friends, best friends, enemies, workplace cliques.
*   **Pets:** Adoption, exotic pets, interactions, veterinary health.
*   **Childhood Economy:**
    *   **Freelance Gigs:** Minors (ages 8-17) can perform task-based work for pocket money (e.g., Lawn Mowing, Babysitting, Dog Walking, Tutoring).
    *   **Parental Funding:** Interaction to "Ask for Money" with success rates based on the Relationship bar and the parents' Generosity stat.
*   **Advanced Relationship Mechanics:**
    *   **Gifting System:** Ability to purchase items from the Asset tab or specific shops (flowers, chocolates, BitLife merchandise) to gift to NPCs for massive relationship boosts.
    *   **Ex-Partners:** A persistent list of former lovers. Mechanics include "Stalking," "Rekindling," or obtaining Restraining Orders.
*   **Reproductive Health:**
    *   **Birth Control:** Toggleable options for "Safe Sex" (Condoms), hormonal birth control (The Pill), or permanent sterilization (Vasectomy/Tubal Ligation).
    *   **STD System:** Unprotected encounters carry risks of specific diseases (Herpes, HIV, Syphilis) that require medical treatment and persist until cured.
*   **Cultural & Advanced Romance:**
    *   **Arranged Marriages:** In specific cultures, parents may force an arranged marriage event at age 18+. Refusing drastically lowers the Relationship bar with parents; accepting locks the agent into a marriage with a random NPC.
    *   **Eloping:** An alternative to the "Plan Wedding" action. Costs $0 but denies the player wedding gifts/money and slightly lowers relationship with traditional parents.
    *   **Marriage Counseling:** An action available when the Spouse Relationship bar is <50%. Costs money but prevents divorce if successful. Failure accelerates divorce.
*   **School Socials:**
    *   **Classmate List:** A distinct list separate from "Friends." Allows specific interactions: "Help with Homework" (Boosts Smarts/Relationship), "Ask for Notes," or "Bully."
    *   **School Nurse:** A low-tier medical option available only during school years. Can cure minor ailments (Headache, Cold) but fails on serious diseases.
*   **Enemy Dynamics:**
    *   **The Rumble:** A specific "Attack" option for Enemies. Unlike standard assaults, this is a mutual combat event.
    *   **Lethal Force:** The ability to attempt to murder an enemy directly (without a hitman). Success depends on Strength/Weapon, but carries the highest risk of prison.

### Assets, Economy & Lifestyle
*   **Real Estate & Landlord System:**
    *   **Market:** Dynamic housing market.
    *   **Ownership:** Mortgages, cash purchases, flipping.
    *   **Landlord:** Renting, screening tenants, evictions, maintenance.
    *   **Upgrades:** Pools, gyms, renovations.
*   **Vehicles:** Purchasing cars/boats/aircraft; maintenance and breakdowns.
*   **Personal Assets & Shopping:**
    *   **Jewelry:** Buying/selling rings, necklaces.
    *   **Heirlooms:** Rare items passed down.
    *   **The "Useless" Market:** Buying random items (fake watches, prayer beads, boomboxes) to hoard or gift.
    *   **Wishlists:** (Childhood only) Ability to ask parents to buy specific assets (e.g., "Ask Mom for a car" at age 16).
*   **Financial Management:**
    *   **Banking:** Savings, debt, student loans.
    *   **Gambling:** Casino, Horse Racing, Lottery.
    *   **Taxation:** Income brackets, location-based tax, evasion risks.
*   **Consumer Goods:**
    *   **Shopping:** A general store interface to buy miscellaneous items (electronics, instruments for skill practice, gifts).
    *   **Wishlists:** Minors can add expensive items (cars, consoles) to a wishlist, which parents may purchase upon Age Up depending on their Generosity.
*   **Asset Maintenance & History:**
    *   **Jewelry Care:** "Clean" action to maintain asset condition and "Appraise" action to see current market value (which fluctuates independently of inflation).
*   **Renovations:**
    *   **Value Add:** "Renovate" action (e.g., Add Extension, Remodel Kitchen) costs money but increases the asset's market value beyond inflation.
    *   **Vacation Homes:** Ability to buy property in foreign countries. These do not generate rent but provide a free place to stay during "Vacation" actions.
*   **Auction Houses:**
    *   **Bidding War:** A mini-game where the agent bids against NPCs for rare jewelry or art.
    *   **Authenticity:** A hidden stat for auctioned items. An item can be bought for millions but turn out to be a "Fake" upon appraisal.
*   **Taxidermy:**
    *   **Preservation:** Upon the death of a pet (or rarely, a human relative), the option to "Taxidermy" the body.
    *   **Furniture:** The resulting item becomes a possession that can be displayed or sold (though selling human taxidermy carries legal risks).
*   **Private Museums:**
    *   **Curator Mode:** If the agent owns >10 high-value Heirlooms or Taxidermy items, they can open a Museum.
    *   **Revenue:** Generates passive monthly income based on the total value of the collection.
*   **Active Interactions:**
    *   **Drive:** "Go for a Drive" action for owned vehicles. Increases Happiness but carries a risk of "Car Accident" events (Health damage/Lawsuits).
    *   **Play:** Specific interaction for pets (e.g., "Play with Dog") distinct from walking, essential for maintaining the Pet Relationship bar.

### Education, Career & Fame
*   **Education System:**
    *   **Primary/Secondary:** Public vs. Private, study habits, extracurriculars.
    *   **Academic Authority:** Specific interactions with Teachers/Professors (Suck up, Flirt, Insult). Poor relationships lead to bad grades or suspension.
    *   **Higher Ed:** Majors, scholarships, loans, Greek life.
    *   **Graduate:** Law, Med, Business, Pharmacy, Nursing, PhD.
*   **The Student Economy:**
    *   **Freelance Gigs (Minors):** Ability for children (<16) to earn money via Lawn Mowing, Babysitting, Pet Sitting, or Tutoring.
    *   **Part-Time Jobs:** High school/College students can hold "Shift Work" (Cashier, Barista) simultaneously with school.
    *   **Parental Support:** Interaction to "Ask parents for money" or "Ask to pay tuition."
*   **Advanced Careers:**
    *   **Specialty Paths:** Military, Politics, Corporate.
    *   **Performance:** Musician, Actor, Athlete.
    *   **Modeling:** Auditions, photoshoots.
*   **Fame System:**
    *   **Social Media:** Followers, viral posts, verification, monetization.
    *   **Publicity:** Talk shows, commercials, books, scandals.
*   **Student Economy:**
    *   **Part-Time Jobs:** High School and University students can hold specific low-tier jobs (Barista, Cashier) simultaneously with their studies.
    *   **Stress Management:** Holding a job while studying applies a multiplier to the annual Stress accumulation, increasing the risk of High Blood Pressure or burnout.
*   **Faculty Dynamics:**
    *   **Teacher Interactions:** A list of current teachers/professors with relationship bars.
    *   **Actions:** "Suck Up" (improves grades), "Flirt" (high risk of expulsion), "Insult," or "Gift."
*   **School Cliques:**
    *   **Social Tribes:** High schools contain cliques (Goths, Jocks, Nerds, Mean Girls, Skaters).
    *   **Entry Requirements:** Joining requires specific stats (e.g., Mean Girls require 80+ Looks, Nerds require 80+ Smarts/Grades).
    *   **Benefits:** Joining a clique provides passive stat protection (e.g., Jocks don't get bullied).
*   **Workplace Politics:**
    *   **Hierarchy:** Distinguishes "Supervisor" from "Co-workers."
        *   *Supervisor:* Interactions affect job security and promotion chances. Sleeping with the boss creates a high-risk/high-reward promotion shortcut.
        *   *Co-workers:* Can be befriended or enemies.
    *   **Human Resources (HR):** Ability to "Report" a co-worker for bullying/pranks. Conversely, the agent can be called to HR and fired if they behave poorly.
    *   **Active Progression:** "Ask for Promotion" and "Ask for Raise" actions. Success depends on Performance bar and Relationship with Supervisor. Failure decreases Professionalism.
*   **Retirement:**
    *   **Pension Logic:** After 20+ years in a career, the "Retire" option unlocks, providing a % of the salary annually until death. Quitting early forfeits this.
*   **Skill Classes:**
    *   **Voice & Acting Lessons:** Paid activities required to unlock the "Musician" or "Actor" special careers. Unlike school, these cost money per session.
    *   **Library:** A "Visit Library" action. It provides a smaller Smarts boost than "Study Hard" but is free and lowers Stress.
*   **Political Campaigns:**
    *   **Campaign Manager:** Before becoming a Mayor/Governor, the agent must run a campaign.
    *   **Platform:** Player chooses a focus (Economy, Education, Environment).
    *   **Budget:** Player must allocate personal funds to the campaign. Low budget = high chance of losing the election.
    *   **Rallies:** Events where the player answers RNG questions to sway voters.
*   **Military Service Nuances:**
    *   **Rank Progression:** Enlisted vs. Officer tracks.
    *   **Medals:** Random events during deployment (e.g., "Save a squadmate") can award medals (Purple Heart, Medal of Honor). These medals are physical assets that can be sold after discharge.
*   **The Gig Economy (Adults):**
    *   **Side Hustles:** Adults can work "Freelance" apps (Ride Share, Food Delivery) alongside their full-time job.
    *   **Risk:** High stress accumulation and random events (e.g., "Passenger vomited in your car").

### Activities, Crime & Health
*   **Health & Wellness:**
    *   **Specific Pathology:** Instead of generic "Health Low," agents contract specific ailments (High Blood Pressure, Bunions, Cancer, Erectile Dysfunction) requiring specific treatments.
    *   **Medical:** Plastic surgery, fertility, gender reassignment.
    *   **Alternative Medicine:**
        *   *Acupuncture/Chiropractor:* Low risk, low reward.
        *   *Witch Doctors:* High risk RNG. Can cure terminal illness instantly or kill the agent immediately (e.g., "Monkey Paw" mechanic).
    *   **Mental Health:** Therapy, psychiatry, meditation.
    *   **Addiction:** Alcohol/drug dependency, rehab.
    *   **Fitness & Spa:** Gym, martial arts, tanning, massage.
*   **Crime & Justice:**
    *   **Activities:** Shoplifting, burglary, GTA, embezzlement, robbery, murder.
    *   **Juvenile Justice:** Crimes committed under 18 result in "Juvie" (Juvenile Detention) with different events/escape mechanics than adult prison.
    *   **Legal Nuance:**
        *   *False Accusations:* Random events where police arrest the agent for a crime they didn't commit; requires legal defense.
        *   *Sex Offender Registry:* Certain crimes place the agent on a registry, permanently blocking specific career paths (Education, Politics).
        *   *Informant:* Option to become a "Rat" for the police to avoid jail time, at the risk of Mafia retaliation.
    *   **Prison:** Riots, gangs, escapes, appeals, parole.
*   **Leisure:**
    *   **Travel:** Vacations, cruises, emigration.
    *   **Hobbies:** Instruments, reading, clubbing, cinema.
*   **Dietary System:**
    *   **Diet Plans:** Selectable lifestyle choices with monthly costs and stat modifiers.
        *   *Examples:* Vegan (High Health/Karma), Keto (Weight Loss), Liquid Diet (High Risk), "Hot Cheetos" Diet (Health decay).
    *   **Consequences:** Diets can trigger specific medical events (e.g., Tapeworm from unwashed veggies, Heart Attack from high fat).
*   **Specific Pathology:**
    *   **Disease Library:** Instead of generic "Sick," agents contract specific ailments (Flu, Bunions, Erectile Dysfunction, Cancer, Dementia).
    *   **Treatment Logic:** Each disease has a specific cure probability via standard medicine. Some are chronic and require annual management.
*   **Juvenile Justice:**
    *   **Juvie:** A separate incarceration system for agents under 18.
    *   **Behavior:** Good behavior in Juvie can lead to early release; bad behavior transfers the agent to adult prison upon turning 18.
*   **Legal Nuances:**
    *   **False Accusations:** Random events where the police accuse the agent of a crime they did not commit.
    *   **Lawsuits:** Ability to sue NPCs (for assault) or former employers (for wrongful termination), or be sued by them.
*   **Intellectual Leisure:**
    *   **Reading:** "Read Book" action. Player selects a genre (Children's, Non-Fiction, Dictionary). Completing a book provides a massive Smarts boost.
    *   **Visual Media:** "Watch Documentary" (Smarts boost) vs. "Go to Movies" (Happiness boost).
    *   **Garden:** If the agent owns a house with a garden, "Tend Garden" becomes available as a high-efficiency stress reducer.
*   **Nightlife:**
    *   **Clubbing:** "Go Clubbing" action. Events include being offered alcohol/drugs (Addiction risk) or "Hook up with Stranger" (Happiness boost + STD risk).
*   **Underworld Services:**
    *   **Hitmen:** A "Crime" menu option to pay a large sum to kill an NPC.
        *   *Outcomes:* Success (Target dies, no police), Botched (Target lives, takes money), or Undercover Cop (Immediate arrest).
    *   **Bribery:** When confronted by Police or Prison Guards, the option to "Attempt Bribe." Success depends on the amount offered and the official's hidden "Professionalism" stat.
*   **Advanced Medical:**
    *   **Hormone Therapy:** An annual medical action available to Transgender agents. Must be maintained for X years before Gender Reassignment Surgery becomes available.
*   **Illegal Emigration:**
    *   **Border Crossing:** If an agent has a criminal record (blocking legal travel), they can attempt to "Emigrate Illegally."
    *   **Risk:** High chance of arrest or deportation back to the home country.
*   **Micro-Wellness:**
    *   **Walk:** "Go for a Walk" action. Free, slight Happiness boost, slight Health boost. Small RNG chance to find money or items on the ground.
*   **Surgical Risks:**
    *   **Botched Procedures:** Plastic surgery has a failure rate based on the doctor's "Reputation" and cost.
    *   **Consequences:** A botched surgery reduces "Looks" to <10% and cannot be fixed until the agent sues the doctor or pays for expensive corrective surgery.
*   **Advanced Criminal Activities:**
    *   **Porch Pirate:** Stealing packages from neighbors. Low reward, low risk, but high frequency availability.
    *   **Train Robbery:** A "Time-Sensitive" crime. It is only available to attempt at specific real-world times (e.g., 4:20 PM or Midnight system time). Attempting at the wrong time results in instant death ("The train ran you over").
*   **The "Rat" System:**
    *   **Informant:** If arrested, police may offer a plea deal to become a Confidential Informant.
    *   **Mini-Game:** The agent must return to their Mafia family and "Gather Evidence" periodically without being caught.
    *   **Witness Protection:** Upon gathering enough evidence, the agent is acquitted, their name/location is legally changed, and they are migrated to a new country with a wiped history.
*   **Emigration Nuances:**
    *   **Political Asylum:** If the agent lives in a country with low "Stability" or is being persecuted, they can apply for Asylum in another country (bypassing financial requirements).
    *   **Deportation:** If an agent emigrates illegally or commits crimes on a Visa, they are forcibly returned to their spawn country.

### Legacy & Meta-Game
*   **End of Life Protocols:**
    *   **Funeral Planning:** Selecting method (Burial vs. Cremation), casket type, and location.
    *   **Attendees:** Logic determining who shows up based on Relationship stats (e.g., "Your ungrateful son didn't attend").
*   **Inheritance:** Wills, estate division, charity, taxes.
*   **Dynasty:** "Continue as Child" mechanic.
*   **Graveyard:** Persistent records and epitaphs.
*   **Technical:** Save/Load, dashboards, God Mode.
*   **End of Life Rituals:**
    *   **Funeral Planning:** Selecting the method (Burial vs. Cremation) and the ceremony type (Open Casket, Eco-friendly).
    *   **Attendance:** Logic determining who attends based on lifelong Relationship stats.
    *   **Mourning:** Attending the funerals of parents/friends/pets, with options to "Pay Respects" or "Disrespect," affecting the mental health of survivors.
*   **Meta-Tools:**
    *   **Time Machine:** A premium/cheat feature allowing the player to age down 1, 3, or 5 years to undo a death or bad decision.
    *   **God Mode (NPC Editor):** An interface to edit the stats of existing NPCs (e.g., lowering a Boss's "Professionalism" or a Spouse's "Willpower").
    *   **Surrender:** A menu option to end the current life immediately (Suicide), triggering the End of Life sequence without waiting for natural death.

### Psychology, Scenarios & Genetics
*   **The "Nature vs. Nurture" Architecture:**
    *   **Genotype (The Reaction Range):** At birth, agents are not assigned a static value for Big 5 traits. Instead, they are assigned a **Genetic Range** (e.g., Extraversion Potential: 8-16). This is heavily influenced by parental heritability (approx. 40-60% correlation).
    *   **Phenotype (The Realized Self):** The current, visible attribute value. It starts at the midpoint of the Genetic Range and drifts based on environmental choices and "Core Memories."
    *   **Plasticity Curve:** The ability to change stats decreases with age.
        *   *Ages 0-6:* 100% Plasticity (Massive shifts possible).
        *   *Ages 7-18:* 50% Plasticity (Moderate shifts).
        *   *Ages 25+:* 10% Plasticity (Personality "crystallizes," requiring major trauma or effort to change).

*   **Developmental Stages & Critical Periods:**
    *   **Infancy (0-2) - Temperament:**
        *   *Focus:* **Neuroticism & Extraversion**.
        *   *Mechanic:* The "Fussiness" hidden stat. High fussiness leads to higher baseline Neuroticism (Anxiety/Vulnerability).
        *   *Parental Impact:* "Secure Attachment" events (parents responding to crying) lower Neuroticism. "Avoidant Attachment" raises it.
    *   **Early Childhood (3-6) - Impulse & Imagination:**
        *   *Focus:* **Openness & Agreeableness**.
        *   *Scenarios:* "Sharing Toys" (Altruism), "Imaginary Friend" (Fantasy), "Tantrums" (Angry Hostility).
        *   *Outcome:* Determining if the child is "Difficult" or "Easy," affecting parental relationship stress.
    *   **School Age (7-12) - Industry vs. Inferiority:**
        *   *Focus:* **Conscientiousness**.
        *   *Mechanic:* The "Homework Loop." Choices to study vs. play directly build the *Self-Discipline* and *Achievement Striving* facets.
        *   *Socialization:* First exposure to "Peer Pressure." High Agreeableness (Compliance) makes the agent susceptible to bad influences; Low Agreeableness makes them a potential bully.
    *   **Adolescence (13-19) - Identity vs. Confusion:**
        *   *Focus:* **The Volatility Spike**.
        *   *Puberty Modifier:* Between ages 13-15, a temporary "Hormonal" modifier is applied: +Impulsiveness, +Libido, +Angry Hostility, -Dutifulness.
        *   *Risk-Taking:* The prefrontal cortex is undeveloped. Scenarios involving drugs, reckless driving, and truancy appear frequently.
        *   *Ideological Formation:* The agent challenges parental values. High *Openness (Values)* increases the chance of rejecting the parents' Religion or Politics.

*   **Emergent Identity:**
    *   **Sexuality Spectrum (The Kinsey Scale):**
        *   *Latent Value:* Sexuality is a hidden float (0.0 to 6.0) determined at birth but invisible.
        *   *Discovery Phase (Ages 11-16):* Random "Crush" events reveal the value.
        *   *Fluidity:* High *Openness* allows for slight drifting on the scale during college years (Experimentation).
    *   **Religious Trajectory:**
        *   *Indoctrination (0-12):* Religiousness is inherited directly from parents.
        *   *Crisis of Faith (16-25):* High *Openness* or High *Neuroticism* (Tragedy) triggers events to question faith. Outcomes: "Devout," "Agnostic," or "Atheist."
    *   **Political Compass:**
        *   Derived from Big 5: High *Openness* correlates with Liberalism; High *Conscientiousness (Order)* correlates with Conservatism.

*   **The Scenario Engine (Context-Aware Events):**
    *   **Trigger Logic:** Scenarios are not random; they are pulled from a deck based on current stats.
        *   *Example:* An agent with High *Extraversion (Excitement Seeking)* will trigger "Street Racing" or "Clubbing" scenarios. An agent with High *Neuroticism* will trigger "Existential Dread" or "Jealousy" scenarios.
    *   **Moral Dilemmas:**
        *   *The Heinz Dilemma:* Complex choices with no right answer (e.g., "Steal medicine to save a dying friend?").
        *   *Impact:* These choices do not just adjust stats; they add **Flags** to the character (e.g., `Has_Criminal_Mindset`).
    *   **Core Memories (Perks/Traumas):**
        *   *Mechanic:* Critical successes or failures in scenarios create permanent modifiers.
        *   *Positive:* "Won State Championship" -> Permanent +5 Confidence (Lowers Vulnerability).
        *   *Negative:* "Caught Shoplifting" -> Permanent +5 Anxiety (Neuroticism).

*   **Psychopathology (The Extremes):**
    *   **Thresholds:** If a Big 5 trait hits 0 or 100 (sum 120), it manifests as a pathology.
        *   *Extreme Conscientiousness:* OCD tendencies (Obsessive cleaning events).
        *   *Extreme Neuroticism:* Clinical Depression or Panic Disorder.
        *   *Extreme Low Agreeableness:* Anti-Social Personality Disorder (Sociopathy).
    *   **Therapy:** Actions to mitigate these extremes, moving the stats back toward the mean.

### Special Careers & Organizations
*   **Royalty:**
    *   **Titles:** Baron to King/Queen.
    *   **Duties:** Public service, laws, executions.
    *   **Exile:** Abdication/Overthrow.
*   **Organized Crime (Mafia):**
    *   **Hierarchy:** Soldier to Godfather.
    *   **Rackets:** Extortion, whacking, turf wars.
*   **Business Tycoon:**
    *   **Startup:** Creating companies.
    *   **Management:** Products, marketing, factories, selling.
*   **Cults:**
    *   **Leadership:** Communes, doctrine.
    *   **Events:** Ceremonies, standoffs.
*   **Secret Agent:**
    *   **Espionage:** Infiltration, hacking, assassination.
*   **Astronaut:**
    *   **Academy:** Training.
    *   **Missions:** Spacewalks, aliens.
*   **Street Hustler:**
    *   **Streets:** Busking, panhandling, scams.

### Interactive Systems & Mini-Games
*   **Skill-Based Challenges:**
    *   **Burglary:** Maze-based stealth game.
    *   **Prison Escape:** Grid-based puzzle.
    *   **Military Deployment:** Minesweeper logic.
    *   **Intelligence:** IQ/Memory tests.
*   **The "Rat" Collection:** A push-your-luck mini-game for informants trying to record mafia conversations.

## ⚖️ Design Philosophy & Abstractions

To maintain playability and focus on emergent storytelling, **Life-Sim** deliberately abstracts specific real-world complexities. We prioritize *decision-making* over *micromanagement*.

### 1. Biological Needs: Auto-Regulation
*   **Constraint:** We do not simulate hunger, thirst, bladder, or hygiene meters.
*   **Abstraction:** These are bundled into **Cost of Living** and **Health Decay**.
    *   If a player has money, "Food" is automatically purchased and consumed.
    *   If a player is broke, Health decays rapidly due to "Malnutrition."
    *   Hygiene is a modifier on the "Looks" stat, maintained by a "Grooming" time allocation in the schedule.

### 2. Economy: Aggregated Cash Flow
*   **Constraint:** No manual grocery shopping, utility bill payments, or tax filing.
*   **Abstraction:** Expenses are aggregated into a single **Monthly Outflow**.
    *   **Cost of Living:** Derived from location + house quality + family size.
    *   **Taxes:** Automatically deducted from salary before it hits the player's balance.
    *   **Inflation:** Applied globally to prices each year.

### 3. Social Interaction: Intent vs. Dialogue
*   **Constraint:** No branching dialogue trees for every conversation.
*   **Abstraction:** Interactions are **Intent-Based**.
    *   Player chooses an intent: *Compliment, Insult, Ask for Money, Flirt*.
    *   The engine calculates the outcome based on Stats (Smarts/Looks), Relationship Score, and RNG.
    *   We simulate the *result* of the conversation, not the conversation itself.

### 4. Geography: Node-Based Movement
*   **Constraint:** No open-world walking or driving physics.
*   **Abstraction:** The world is a collection of **Nodes** (Home, Work, Gym, Park).
    *   Travel is instant but incurs a "Commute Time" penalty in the Weekly Schedule based on the distance between nodes (e.g., moving to a suburb increases Commute hours, reducing Leisure hours).

### 5. Scope of Reality: Strictly Material
*   **Constraint:** No supernatural, paranormal, or sci-fi elements (e.g., Ghosts, Aliens, Cryptids, Hauntings).
*   **Abstraction:** The simulation is grounded in **Deterministic Realism**.
    *   Events are strictly biological, sociological, or statistical.
    *   "Luck" is a mathematical probability modifier, not a magical force.
    *   *Reasoning:* Excluding paranormal logic reduces code complexity (no need for "Exorcism" mechanics or "Ghost Encounter" RNG) and maintains a consistent, grounded tone focused on real-life simulation.

### 6. Progression: Sandbox over Gamification
*   **Constraint:** No "Achievements," "Ribbons," "Badges," or global leaderboards.
*   **Abstraction:** The focus is on **Intrinsic Motivation**.
    *   The "Goal" is defined by the player (e.g., "I want to be a billionaire" or "I want to have 10 kids"), not by a checklist provided by the engine.
    *   We avoid tracking meta-data across save files to keep the architecture modular and focused on the current agent's lifecycle.
    *   *Reasoning:* This prevents "Checklist Fatigue" and encourages players to experiment with the sandbox mechanics rather than optimizing their life solely to unlock a badge.

### 7. The "Faux-Conomy": Static vs. Dynamic
*   **Constraint:** No supply-and-demand logic, stock market simulation, or global trade physics.
*   **Abstraction:** The economy is **Reference-Based**.
    *   **Base Values:** Every item (House, Car, Diamond Ring) has a static `Base_Price` in the config files.
    *   **Multipliers:** Prices are calculated at runtime: `Base_Price * Inflation_Multiplier * Country_Cost_of_Living_Multiplier`.
    *   **Real Estate:** Housing markets do not crash or boom based on inventory. They simply follow a randomized noise curve (e.g., `Current_Value = Previous_Value * random(0.95, 1.08)`).
    *   *Reasoning:* Building a real economic engine is a separate game entirely. This system ensures prices *feel* dynamic without requiring a math degree to balance.

### 8. Legal & Medical: Stat-Check Resolution
*   **Constraint:** No mini-games for court trials, surgeries, or complex diagnosis puzzles.
*   **Abstraction:** Complex institutional interactions are resolved via **Weighted RNG Rolls**.
    *   **Justice:** The outcome of a trial is a single calculation: `(Lawyer_Cost * Lawyer_Skill) vs. (Crime_Severity * Evidence_RNG)`.
    *   **Medicine:** Curing a disease is not a treatment plan; it is a roll of `(Doctor_Competence * Money_Spent) vs. (Disease_Lethality)`.
    *   *Reasoning:* This keeps the gameplay loop fast. The player inputs resources (Money/Time), and the engine outputs a binary result (Guilty/Not Guilty, Cured/Dead).

## 🛠️ Installation & Usage

1.  **Prerequisites:** Python 3.10+, Pygame, NumPy.
2.  **Install Dependencies:**
    ```bash
    pip install pygame numpy
    ```
3.  **Run Simulation:**
    ```bash
    python main.py
    ```

## 📋 Development Rules & Standards

This project follows strict development rules to ensure code quality, maintainability, and scientific rigor. All contributors must adhere to these standards:

### 1. No Magic Numbers - Configuration Separation
Configuration is separated into two distinct types:
- **Application Constants:** All values that are static to the application/framework (e.g., visualization settings, rendering properties, file paths) are defined in `constants.py`. These don't change between runs.
- **Simulation Parameters:** All variables that define a specific experiment or scenario (e.g., number of entities/agents, behavioral parameters, initial conditions) are loaded from a `config.json` file. This enables running different scenarios without touching core code.

### 2. Logging System - No Direct Prints
All runtime messages use the Python logging system with levels `INFO, DEBUG, WARNING, ERROR, CRITICAL`. No direct `print` in the simulation core.
- Logging configuration is loaded from config at startup: global level, formats, destinations.
- Every run writes logs to both the console and a rotating file in the run folder.
- Log format includes timestamp, step/frame/tick, module, event name, and key fields. At minimum include seed, run id, and step/frame/tick.
- Hot loops must throttle logs: sample every N steps; aggregate counts and print summaries once per second of wall time; or only log state changes (not steady states).
- `INFO` is for human-scale events and milestones. `DEBUG` is dense trace and off by default. `WARNING/ERROR` are reserved for real problems.
- Long-term trends do not stream to console. Persist metrics and plot after the run or in a dashboard.
- Exceptions inside steps/ticks are caught at the outer loop, logged with the last N lines of `DEBUG` from each module, then the run stops cleanly.

### 3. Maximum Realism with Managed Complexity
The simulation aims for maximum realism **in behavior and outcomes**, with complexity managed deliberately. Implementations should model real-world processes or constraints accurately, with a cited source where possible. If exact 1:1 realism causes excessive complexity or poor performance, use this checklist before deferring to Rule 8. If **two or more** checks are "yes," switch to a scientifically-grounded abstraction (Rule 8). All abstractions must still leverage real-world properties/constraints and be explicitly documented.
- **Impact check** — Does this detail materially affect emergent behaviors or final metrics? If no, abstract it.
- **Performance check** — Does adding this detail slow the core loop by >10%? If yes, abstract it.
- **Maintainability check** — Will this detail require constant retuning when other systems change? If yes, abstract it.

### 4. Emergent Behavior Focus
The simulation should leverage emergent behaviors.

### 5. Incremental Implementation
Implement changes incrementally. After each small modification, pause to review its impact and confirm it behaves as expected (and aligns with Rule 3) before adding the next feature.

### 6. Hypothesis-Driven Development
Every new feature/modification begins with a clear, testable hypothesis containing:
- A prediction of the change's impact on realism or emergent behavior (Rules 3 & 4).
- A specific prediction of the resulting console/log output (Rule 2).
- Include a **Validation Protocol**: exact speeds, run-times, and steps needed to verify both the log prediction and behavioral impact before proceeding (Rule 5).

### 7. High Modularity & SOLID Principles
Keep the code highly modular. Each distinct system (e.g., environment, agents, mechanics/systems, rendering, I/O) lives in its own module, class, or function.
- **SOLID (explicit and enforced):**
  - **SRP:** Each module/class has exactly one job. If a second concern appears, split it.
  - **OCP:** Once a module is in use on `main`, treat it as closed for modification. Add behavior via composition/extension (Strategy, Decorator, new classes) rather than editing stable code. If a breaking change is unavoidable, write an ADR and provide a backward-compatible path until deprecation.
  - **LSP:** Implementations must be drop-in replacements for their interfaces/base types. Don't narrow inputs or weaken output guarantees; preserve invariants and error semantics.
  - **ISP:** Prefer small, purpose-built interfaces over "god" interfaces. Callers shouldn't depend on methods they don't use.
  - **DIP:** Depend on abstractions (Protocols/ABCs), not concretes. Inject collaborators via constructors/factories. Only the composition root (`main.py`/wiring) binds interfaces to implementations.
- A module must not depend on another module's internal state—only its public interface or passed-in data.
- Every module has a **data contract**: explicit inputs (types, units), outputs (types, units), side effects, and invariants. State this at the top of the file and mirror it in docstrings.
- All files must include a comment including their path and name at the top of the file.
- Global variables are allowed only for immutable constants (Rule 1).
- Each new module/function must be testable in isolation with synthetic inputs before full integration.

### 8. Scientifically-Grounded Abstractions
If a real-world process is too complex or expensive for 1:1 simulation (Rule 3), use a **scientifically-grounded abstraction**. Document assumptions, simplifications, and limitations in code comments or a design doc.

### 9. Code Style & Documentation
Follow a consistent style guide (e.g., PEP 8). Code should be self-commenting where possible; add comments to explain the **why**, especially for complex abstractions (complements Rule 8).

### 10. Performance-Driven Development
Performance changes are driven by profiling, not guesses.
- Before merging a feature, profile one fixed-seed run for a fixed number of steps. Identify the top two hot functions. Store profiling output in `/profiles`. Filenames include date, seed, step count, and branch name. Keep a simple timing table in the PR notes.
- Use NumPy for array math/vectorized transforms and any operation touching many agents or grid cells at once. Pre-allocate arrays outside loops. Avoid per-element Python loops in hot paths.
- Scalar glue code can use plain Python. Don't wrap tiny scalars in NumPy.
- If a vectorized NumPy path is still slow, consider Numba for small, pure-numeric hot functions. Only add Numba when a profile shows a win and the function has no Python objects.
- Avoid pandas in the core step/tick. Convert to arrays for the loop. Use pandas only in post-run analysis.
- Set a dtype policy. Default `float64` unless memory or profiling proves `float32` helps. Keep dtypes consistent to avoid hidden casts.
- Any PR that materially touches the core loop must include before/after timings for the same seed and step count. If slower beyond an agreed threshold, explain the tradeoff or fix it.

### 11. Deterministic Randomness
All randomness is controlled by a single **master seed**. No code may call random functions directly without using this seeded generator. The master seed initializes all relevant RNGs (Python `random`, NumPy, and any library-specific RNGs). The seed is defined in config (or constants), logged at start of every run, and saved with run outputs. Runs must be fully deterministic given the same seed, configuration, and library versions. Log the exact Python and library versions with outputs. True unpredictability may only be introduced with explicit approval and must be clearly documented in code and commit message.

### 12. Readability First
**Readability first** (humans are the audience). If a reviewer can't understand a module quickly, treat it as a bug. Prefer clarity over cleverness.
- Comments explain **why**, not **what**.
- Public functions/classes have docstrings with inputs/outputs/units/invariants and a short example.
- Long expressions are split and named; nested logic is flattened with early returns where safe.

## 🎨 Credits & Assets

*   **Icons:**
    *   Family Tree icon by [Delapouite](https://delapouite.com/) under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) via [Game-Icons.net](https://game-icons.net/1x1/delapouite/family-tree.html#download).