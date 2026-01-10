# Life-Sim

**Life-Sim** is a modular, extensible life simulation engine built in Python. It simulates the biological, economic, and social trajectory of a single agent within a deterministic, configuration-driven world. The project emphasizes statistical realism, emergent behavior, and strict separation of concerns between simulation logic and visualization.

## 🚀 Current Features (MVP 0.1)

### Core Simulation & Identity
*   **Biological Life Cycle:** Agents age annually, suffering natural health decay and eventual death.
*   **Procedural Identity:** Agents are generated with specific Names, Genders, Countries of Origin, and Cities based on configuration pools.
*   **Appearance System:** Tracks physical traits including Eye Color, Hair Color, Skin Tone, Height (cm), and Weight (kg).
*   **Universal Attribute System:**
    *   **Physical:** Strength, Athleticism, Endurance, Fertility, Libido.
    *   **Personality:** Discipline, Willpower, Generosity, Religiousness, Craziness.
    *   **Hidden:** Karma, Luck, Sexuality.
*   **Derived Metrics:** Calculates dynamic stats like Body Fat % and Lean Mass based on Weight and Athleticism.

### Economy & Career
*   **Currency System:** Agents earn and spend money; starting balance is configurable.
*   **Employment Market:** Agents can search for jobs defined in the configuration.
*   **Qualification Logic:** Job acquisition is gated by stats. High-tier jobs (e.g., Software Engineer) automatically reject applicants with low 'Smarts'.
*   **Income:** Employed agents receive annual salaries automatically upon aging up.
*   **Overtime:** Employed agents can perform manual work actions to earn immediate bonuses (1% of salary).

### Actions & Progression
*   **Study:** Agents can invest time to increase their 'Smarts' stat to qualify for better jobs, at the cost of a small amount of Health (stress).
*   **Medical Care:** Agents can visit a doctor to restore Health, provided they have sufficient funds.
*   **Context-Sensitive Controls:** The UI updates available actions based on the agent's state (e.g., "Work" is only available if employed).

### User Interface & Visualization
*   **Tabbed Interface:**
    *   **Overview Tab:** Displays core stats (Age, Money, Job), current actions, and the narrative event log.
    *   **Attributes Tab:** A detailed, multi-column inspection screen showing the full biographical, physical, and personality profile of the agent.
*   **Event Logging:** A scrolling on-screen text log records every significant life event (salary, illness, job offers).
*   **Game Over State:** Upon death, the simulation locks inputs and displays a final summary.

## 🗺️ Roadmap (Planned Features)

The following features are planned to expand the simulation depth into a comprehensive life emulator:

### Phase 0.5: UI Overhaul & UX Polish
*   **Full-Screen Layout:**
    *   **Responsive Design:** The application runs in full-screen mode (or maximized window), utilizing the entire display area.
    *   **Three-Panel Architecture:**
        *   **Left Panel (Status):** Fixed sidebar containing the Agent's Portrait (placeholder), Core Stats (Health, Happiness, etc.), and Financial Summary.
        *   **Center Panel (Narrative):** The primary focus. A large, scrollable history feed that resembles a social media timeline or chat log.
            *   **Rich Text:** Events are color-coded (e.g., Red for Danger, Green for Money).
            *   **Interactive Elements:** Past years are grouped; clicking a year expands/collapses its details.
        *   **Right Panel (Action Hub):** A dynamic menu system for "Activities," "Assets," "Relationships," and "Career."
            *   **Contextual Buttons:** The "Age Up" button is prominent and always accessible at the bottom.
*   **Navigation & Controls:**
    *   **Mouse Support:** Full click/scroll support for the history log and menus (moving away from keyboard-only shortcuts).
    *   **Modal Windows:** Pop-up dialogs for complex interactions (e.g., "Visit Doctor" opens a modal with treatment options and prices).
*   **Visual Polish:**
    *   **Theming:** Consistent color palette (Dark Mode default) with distinct visual hierarchies.
    *   **Typography:** Use of legible, scalable fonts for the narrative log to ensure readability on high-res screens.

### Phase 1: Genetics, Growth & Skills
*   **Aging & Mortality:**
    *   **Declining Vitality:** Maximum Health capacity decreases annually (e.g., Max Health is 100 at age 20, but only 60 at age 80).
    *   **The Century Limit:** A hard mortality cap ensures Maximum Health reaches 0 at age 100, guaranteeing death if it hasn't occurred naturally.
    *   **Frailty:** As the Health Cap lowers, minor events (flu, stress) become increasingly lethal due to the reduced health buffer.
*   **Genetics Engine:**
    *   **Height Potential:** Agents are born with a genetic max height. They grow towards this limit annually until adulthood, and slowly shrink during seniority.
    *   **Dynamic Physiology:** Weight and muscle mass fluctuate dynamically based on Age, Athleticism, and Metabolism.
*   **Skill Mastery Mechanics:**
    *   **Practice System:** Logic to learn and level up specific skills (0-100) via time allocation.
    *   **Content Implementation:**
        *   **Instruments:** Guitar, Piano, Violin, etc.
        *   **Martial Arts:** Karate, Jiu-Jitsu, Boxing, etc.
        *   **Licenses:** Driving, Pilot, Boating.
*   **Manual Character Creator:** A UI screen to manually select Name, Appearance, and Attributes before starting the simulation.

### Phase 2: Social Web & Relationships
*   **Family Generation:** Procedural creation of parents, stepparents, and siblings with genetic stat inheritance.
*   **Relationship Dynamics:**
    *   **Interactions:** Spend time, conversation, ask for money, argue, insult, prank, rumor spreading.
    *   **Status:** Relationship bars (0-100) that fluctuate based on interactions and random events.
*   **Romance:**
    *   **Dating:** Dating apps, blind dates, hookups, and random encounters.
    *   **Partnership:** Engagement, marriage (with prenups), eloping, and divorce settlements.
    *   **Cheating:** Affairs, paternity tests, and confrontation mechanics.
*   **Progeny:**
    *   **Reproduction:** Pregnancy mechanics, birth events, IVF, sperm donors, surrogacy, and adoption systems.
    *   **Parenting:** Interactions with offspring affecting their future stats; disowning children.
*   **Social Circles:** Friends, best friends, enemies, workplace cliques, and supervisors.
*   **Pets:** Adoption (shelter/breeder), exotic pets (tigers, monkeys), pet interactions, and veterinary health.

### Phase 3: Assets, Economy & Lifestyle
*   **Real Estate & Landlord System:**
    *   **Market:** Dynamic housing market with varying condition and prices.
    *   **Ownership:** Mortgages, cash purchases, selling, and flipping houses.
    *   **Landlord:** Renting out properties, screening tenants, evictions, and handling maintenance requests.
    *   **Upgrades:** Adding pools, gyms, or renovations to increase value.
*   **Vehicles:** Purchasing new/used cars, boats, and aircraft; maintenance costs and breakdown events.
*   **Personal Assets:**
    *   **Jewelry:** Buying/selling rings, necklaces (market fluctuation).
    *   **Heirlooms:** Rare items passed down through generations.
    *   **Museum:** Curating a collection of taxidermy or rare artifacts.
*   **Financial Management:**
    *   **Banking:** Savings accounts, debt management, and student loans.
    *   **Gambling:** Casino games (Blackjack, Horse Racing), Lottery, and addiction mechanics.
    *   **Taxation:** Annual tax rates based on income brackets and location; tax evasion risks.

### Phase 4: Education, Career & Fame
*   **Education System:**
    *   **Primary/Secondary:** Public vs. Private schools, study habits, extracurriculars, cheating on tests, and popularity.
    *   **Higher Ed:** University majors, scholarships, student loans, Greek life (Fraternities/Sororities).
    *   **Graduate:** Law School, Medical School, Business School, Pharmacy, Nursing, and PhD programs.
*   **Advanced Careers:**
    *   **Specialty Paths:** Military service (deployment logic/rank), Politics (campaigns/elections), and Corporate ladders.
    *   **Performance:** Musician (bands/solo/contracts), Actor (auditions/agents), and Professional Athlete (drafts/stats/championships).
    *   **Modeling:** Auditions, photoshoots, and runway gigs.
*   **Fame System:**
    *   **Social Media:** Platforms, followers, viral posts, verification, and monetization.
    *   **Publicity:** Talk shows, commercials, photoshoots, scandals, and writing books.

### Phase 5: Activities, Crime & Health
*   **Health & Wellness:**
    *   **Medical:** Plastic surgery (botched risks), fertility treatments, gender reassignment, and alternative medicine (acupuncture/chiropractor).
    *   **Mental Health:** Therapy, psychiatry, and meditation.
    *   **Addiction:** Alcohol and drug dependency mechanics with rehab options.
    *   **Fitness:** Gym, martial arts, walks, and gardening.
    *   **Salon & Spa:** Tanning, manicures, and massages.
*   **Crime & Justice:**
    *   **Activities:** Shoplifting, burglary, grand theft auto, embezzlement, bank robbery, train robbery, and murder.
    *   **Legal System:** Police encounters, lawyers (public defender vs expensive), trials, and sentencing.
    *   **Prison:** Prison riots, gangs, escape attempts, appeals, and parole boards.
*   **Leisure:**
    *   **Travel:** Vacations (First class/Economy), cruises, and emigration (legal/illegal).
    *   **Hobbies:** Learning instruments, reading books, clubbing, and cinema.

### Phase 6: Legacy & Meta-Game
*   **Inheritance:** Wills, estate division, charity donations, and estate taxes.
*   **Dynasty:** "Continue as Child" mechanic to play through multiple generations.
*   **Achievements:** Tracking ribbons (e.g., "Mediocre", "Loaded", "Lustful") and trophies for specific life outcomes.
*   **Graveyard:** Persistent records of past lives and epitaphs.
*   **Technical:** Save/Load functionality, data visualization dashboards, and "God Mode" (editing NPC stats).

### Phase 7: Developmental Psychology & Genetics
*   **Genotype vs. Phenotype System:**
    *   **Genetic Potential:** Agents spawn with a "Genetic Range" for attributes.
    *   **Realized Attributes:** Actual stats start low and grow based on environmental factors within genetic bounds.
*   **Developmental Stages (0-18 Years):**
    *   **Infancy (0-2):** Motor skill development, "Trust vs. Mistrust".
    *   **Early Childhood (3-6):** Language acquisition, curiosity events.
    *   **School Age (7-12):** Socialization, academic foundations, and bullying.
    *   **Adolescence (13-18):** Puberty mechanics, rebellion, and risk-taking.
*   **Emergent Identity:**
    *   **Discovery Mechanics:** Traits like Sexuality and Religiousness emerge dynamically.
    *   **Core Memories:** Significant childhood events that permanently buff/debuff personality.

### Phase 8: Special Careers & Organizations
*   **Royalty:**
    *   **Titles:** Born into or marrying into royalty (Baron to King/Queen).
    *   **Duties:** Public service, respect meter, laws, and execution power.
    *   **Exile:** Abdication or being overthrown.
*   **Organized Crime (Mafia):**
    *   **Hierarchy:** Joining a family, rising from Soldier to Godfather.
    *   **Rackets:** Extortion, whacking, ratting out the family, and turf wars.
*   **Business Tycoon:**
    *   **Startup:** Creating a company, naming it, and choosing a sector.
    *   **Management:** Product design, marketing, opening factories, and selling the company.
*   **Cults:**
    *   **Leadership:** Starting a commune, recruiting followers, and choosing a doctrine.
    *   **Events:** Ceremonies, compounds, and standoffs with authorities.
*   **Secret Agent:**
    *   **Espionage:** Infiltrating enemy networks, hacking, and assassination missions.
*   **Astronaut:**
    *   **Space Academy:** Flight training and fitness tests.
    *   **Missions:** Spacewalks, research, and alien encounters.
*   **Street Hustler:**
    *   **Life on the Streets:** Busking, panhandling, and street scams (Three-card Monte).

### Phase 9: Interactive Systems & Mini-Games
*   **Skill-Based Challenges:**
    *   **Burglary:** Maze-based mini-game to avoid dogs/owners and steal loot.
    *   **Prison Escape:** Grid-based puzzle to evade guards.
    *   **Military Deployment:** Minesweeper-style logic game for survival.
    *   **Intelligence:** IQ Tests and memory patterns.
*   **Supernatural Events:**
    *   **Paranormal:** Haunted houses, exorcisms, and ghost encounters.
    *   **Sci-Fi:** Time travel (Age reversal) and alien abductions.

## ⚖️ Design Philosophy & Abstractions

To maintain playability and focus on emergent storytelling, **Life-Sim** deliberately abstracts specific real-world complexities. We prioritize *decision-making* over *micromanagement*.

### 1. Time Management: The "Macro-Schedule"
*   **Constraint:** Players do **not** play through individual days, hours, or minutes. There is no "eat, sleep, pee" loop.
*   **Abstraction:** Time is managed via a **Weekly Schedule**.
    *   The player allocates their 168 weekly hours into buckets (e.g., 40h Work, 56h Sleep, 14h Skill Practice, 58h Leisure).
    *   The simulation calculates the *net effect* of this schedule annually (or monthly).
    *   *Example:* Allocating only 30h to Sleep results in a massive annual Health penalty, without requiring the player to manually click "Sleep" every night.

### 2. Biological Needs: Auto-Regulation
*   **Constraint:** We do not simulate hunger, thirst, bladder, or hygiene meters.
*   **Abstraction:** These are bundled into **Cost of Living** and **Health Decay**.
    *   If a player has money, "Food" is automatically purchased and consumed.
    *   If a player is broke, Health decays rapidly due to "Malnutrition."
    *   Hygiene is a modifier on the "Looks" stat, maintained by a "Grooming" time allocation in the schedule.

### 3. Economy: Aggregated Cash Flow
*   **Constraint:** No manual grocery shopping, utility bill payments, or tax filing.
*   **Abstraction:** Expenses are aggregated into a single **Monthly Outflow**.
    *   **Cost of Living:** Derived from location + house quality + family size.
    *   **Taxes:** Automatically deducted from salary before it hits the player's balance.
    *   **Inflation:** Applied globally to prices each year.

### 4. Social Interaction: Intent vs. Dialogue
*   **Constraint:** No branching dialogue trees for every conversation.
*   **Abstraction:** Interactions are **Intent-Based**.
    *   Player chooses an intent: *Compliment, Insult, Ask for Money, Flirt*.
    *   The engine calculates the outcome based on Stats (Smarts/Looks), Relationship Score, and RNG.
    *   We simulate the *result* of the conversation, not the conversation itself.

### 5. Geography: Node-Based Movement
*   **Constraint:** No open-world walking or driving physics.
*   **Abstraction:** The world is a collection of **Nodes** (Home, Work, Gym, Park).
    *   Travel is instant but incurs a "Commute Time" penalty in the Weekly Schedule based on the distance between nodes (e.g., moving to a suburb increases Commute hours, reducing Leisure hours).

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
4.  **Controls:**
    *   `SPACE`: Age Up (Next Year)
    *   `J`: Find Job
    *   `S`: Study
    *   `W`: Work Overtime
    *   `D`: Visit Doctor