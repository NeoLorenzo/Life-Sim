# Life-Sim

**Life-Sim** is a modular, extensible life simulation engine built in Python. It simulates the biological, economic, and social trajectory of a single agent within a deterministic, configuration-driven world. The project emphasizes statistical realism, emergent behavior, and strict separation of concerns between simulation logic and visualization.

## 🚀 Current Features (MVP 0.1)

### Core Simulation
*   **Biological Life Cycle:** Agents age annually, suffering natural health decay (randomized) and eventual death based on health metrics.
*   **Stat System:** Tracks core attributes including Health, Happiness, Smarts, Looks, and Age.
*   **Event Logging:** A scrolling on-screen text log records every significant life event (salary, illness, job offers), providing a narrative history.
*   **Game Over State:** Upon death, the simulation locks inputs and displays a final summary, preventing further actions.
*   **Configuration:** All simulation parameters (initial stats, job markets, decay rates, seed) are loaded from `config.json`, ensuring deterministic runs.

### Economy & Career
*   **Currency System:** Agents earn and spend money; starting balance is configurable.
*   **Employment Market:** Agents can search for jobs defined in the configuration. The system presents a random opportunity from the pool.
*   **Qualification Logic:** Job acquisition is gated by stats. High-tier jobs (e.g., Software Engineer) automatically reject applicants with low 'Smarts'.
*   **Income:** Employed agents receive annual salaries automatically upon aging up.
*   **Overtime:** Employed agents can perform manual work actions to earn immediate bonuses (1% of salary).

### Actions & Progression
*   **Study:** Agents can invest time to increase their 'Smarts' stat to qualify for better jobs, at the cost of a small amount of Health (stress).
*   **Medical Care:** Agents can visit a doctor to restore Health, provided they have sufficient funds ($100).
*   **Context-Sensitive Controls:** The UI updates available actions based on the agent's state (e.g., "Work" is only available if employed).

## 🗺️ Roadmap (Planned Features)

The following features are planned to expand the simulation depth into a comprehensive life emulator:

### Phase 1: Deep Stats & Customization
*   **Hyper-Detailed Character Creator:**
    *   **Biographical:** Custom Name, Gender, Country/City of Birth (affecting economy/laws).
    *   **Appearance:** Eye color, hair color/style, skin tone, and facial hair.
*   **Universal Attribute System:**
    *   **Physical:** Height, Weight, Strength, Endurance, Fertility, Libido, Athleticism.
    *   **Personality:** Discipline, Willpower, Karma, Generosity, Craziness, Religiousness.
    *   **Hidden:** Luck, Sexuality (Spectrum), Fertility.
*   **Skill Mastery Engine (0-100 Progression):**
    *   **Musical Instruments:** Voice, Guitar, Piano, Drums, Violin, Saxophone, Bass, Cello, Flute, Harp, Trumpet, Tuba, Banjo, Harmonica, Didgeridoo.
    *   **Martial Arts:** Karate, Judo, Taekwondo, Jiu-Jitsu, Kung Fu, Muay Thai, Boxing, Kickboxing, Wrestling, Krav Maga.
    *   **Licenses & Certifications:** Driving, Pilot (Private/Commercial), Boating, CPR, First Aid.
    *   **Criminal Proficiency:** Stealth, Pickpocketing, Hacking, Safe-cracking.

### Phase 2: Social Web & Relationships
*   **Family Generation:** Procedural creation of parents and siblings with genetic stat inheritance.
*   **Relationship Dynamics:**
    *   **Interactions:** Spend time, conversation, ask for money, argue, insult.
    *   **Status:** Relationship bars (0-100) that fluctuate based on interactions and random events.
*   **Romance:**
    *   **Dating:** Dating apps, blind dates, and random encounters.
    *   **Partnership:** Engagement, marriage (with prenups), and divorce settlements.
*   **Progeny:**
    *   **Reproduction:** Pregnancy mechanics, birth events, and adoption systems.
    *   **Parenting:** Interactions with offspring affecting their future stats.
*   **Social Circles:** Friends, best friends, enemies, and workplace cliques.
*   **Pets:** Adoption (shelter/breeder), exotic pets, and pet interactions/health.

### Phase 3: Assets, Economy & Lifestyle
*   **Real Estate:**
    *   **Market:** Dynamic housing market with varying condition and prices.
    *   **Ownership:** Mortgages, cash purchases, selling, and flipping houses.
    *   **Maintenance:** Upkeep costs, renovations, and random disasters (fires, floods).
*   **Vehicles:** Purchasing new/used cars, maintenance costs, and breakdown events.
*   **Personal Assets:** Jewelry, heirlooms, and musical instruments.
*   **Financial Management:**
    *   **Banking:** Savings accounts, debt management, and student loans.
    *   **Gambling:** Casino games (Blackjack, Horse Racing), Lottery, and addiction mechanics.
    *   **Taxation:** Annual tax rates based on income brackets and location.

### Phase 4: Education, Career & Fame
*   **Education System:**
    *   **Primary/Secondary:** Public vs. Private schools, study habits, extracurriculars.
    *   **Higher Ed:** University majors, scholarships, student loans, and Greek life.
    *   **Graduate:** Law School, Medical School, Business School, and PhD programs.
*   **Advanced Careers:**
    *   **Specialty Paths:** Military service (deployment logic), Politics (campaigns), and Corporate ladders.
    *   **Performance:** Musician (bands/solo), Actor (auditions), and Professional Athlete (drafts/stats).
*   **Fame System:**
    *   **Social Media:** Platforms, followers, viral posts, and verification.
    *   **Publicity:** Talk shows, commercials, photoshoots, and scandals.

### Phase 5: Activities, Crime & Health
*   **Health & Wellness:**
    *   **Medical:** Plastic surgery, fertility treatments, gender reassignment, and alternative medicine.
    *   **Mental Health:** Therapy, psychiatry, and meditation.
    *   **Addiction:** Alcohol and drug dependency mechanics with rehab options.
    *   **Fitness:** Gym, martial arts, and walks.
*   **Crime & Justice:**
    *   **Activities:** Shoplifting, burglary, grand theft auto, embezzlement, and violent crimes.
    *   **Legal System:** Police encounters, lawyers, trials, and sentencing.
    *   **Prison:** Prison riots, gangs, escape attempts, and parole boards.
*   **Leisure:**
    *   **Travel:** Vacations (First class/Economy), cruises, and emigration.
    *   **Hobbies:** Learning instruments, gardening, reading.

### Phase 6: Legacy & Meta-Game
*   **Inheritance:** Wills, estate division, and estate taxes.
*   **Dynasty:** "Continue as Child" mechanic to play through multiple generations.
*   **Achievements:** Tracking ribbons and trophies for specific life outcomes.
*   **Graveyard:** Persistent records of past lives and epitaphs.
*   **Technical:** Save/Load functionality and data visualization dashboards.

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