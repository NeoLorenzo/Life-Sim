# Life-Sim

**Life-Sim** is a modular, extensible life simulation engine built in Python. It simulates the biological, economic, and social trajectory of a single agent within a deterministic, configuration-driven world. The project emphasizes statistical realism, emergent behavior, and strict separation of concerns between simulation logic and visualization.

## 🚀 Current Features (MVP 0.5)

### Core Simulation & Architecture
*   **Deterministic Simulation Loop:**
    *   **Master Seed:** The entire simulation (Python `random`, `numpy.random`) is initialized via a single integer seed defined in `config.json`, ensuring 100% reproducibility for debugging and sharing runs.
    *   **Turn-Based Logic:** The simulation advances in 1-year increments (`process_turn`).
    *   **Event Logging:** A dual-channel logging system writes runtime events to both the console (stdout) and rotating log files (`logs/run_YYYYMMDD_HHMMSS.log`) with the format `Time | Level | Module | Message`.
*   **Configuration-Driven Design:**
    *   **No Magic Numbers:** All gameplay variables (initial stats, costs, salary multipliers) are loaded from `config.json`.
    *   **Static Constants:** Visualization settings (Screen Size, Colors, FPS) are decoupled in `constants.py`.
*   **Multi-Agent Architecture:**
    *   **Unified Entity Model:** The `Agent` class has been refactored to support both the **Player** and **NPCs** (Non-Player Characters). All agents share the same biological DNA (Attributes, Health, Inventory), distinguished only by an `is_player` flag and unique UUIDs.
    *   **The "Truman Show" Optimization:** To maintain performance, the simulation uses a dual-update loop. The Player receives full simulation fidelity (events, salary, happiness), while NPCs run on a lightweight "Lazy Evaluation" loop that processes only critical biological functions (Aging, Health Decay, Death Checks) to keep the world alive without CPU overhead.

### Identity & Biology
*   **Procedural Generation:**
    *   **Bio-Data:** Agents are initialized with a First Name, Last Name, Gender, Country, and City drawn from configurable pools.
    *   **Appearance:** Tracks Eye Color, Hair Color, Skin Tone.
    *   **Family Generation:** The simulation automatically generates a Mother and Father at startup. Their ages, jobs, and initial wealth are procedurally generated relative to the player, creating immediate social context (e.g., "Teen Parents" vs. "Older Parents").
    *   **Anthropometry:**
        *   **Height:** Dynamic growth system. Agents start small (~50cm), grow towards a **Genetic Potential** (Male: 150-200cm, Female: 140-180cm) until age 20, and experience spinal compression (shrinkage) after age 60.
        *   **Physique:** Weight is no longer static. It is derived from Height, Gender, and Athleticism using a **Lean Body Mass Index (LBMI)** model.
*   **Universal Attribute System (0-100 Scale):**
    *   **Physical:** Strength, Athleticism, Endurance, Fertility, Libido.
    *   **Personality:** Discipline, Willpower, Generosity, Religiousness, Craziness.
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
    *   **Natural Entropy:** NPCs over age 50 experience slight random health decay annually, ensuring natural death occurs variably between ages 85-100 rather than strictly at the mathematical cap.

### Economy & Career
*   **Job Market:**
    *   **Data Structure:** Jobs are defined in `config.json` with a `title`, `salary`, and `min_smarts`.
    *   **Application Logic:** The "Find Job" action picks a random job from the pool. Success is determined strictly by `Agent.smarts >= Job.min_smarts`.
    *   **Age Restriction:** Agents cannot apply for jobs until **Age 16**.
    *   **Income:** Salaries are added to `Agent.money` automatically during the `process_turn` (Age Up) phase.
*   **Active Income (Overtime):**
    *   **Mechanic:** Employed agents can manually "Work Overtime."
    *   **Reward:** Immediate cash bonus equal to **1%** of the annual salary.
    *   **Constraint:** Action is blocked if the agent is unemployed.

### Actions & Progression
*   **Education (Study):**
    *   **Effect:** Increases Smarts by a random value of **2 to 5**.
    *   **Cost:** Decreases Health by **1** (simulating stress/sedentary lifestyle).
    *   **Cap:** Smarts is clamped at 100.
*   **Healthcare (Doctor):**
    *   **Cost:** Flat fee of **$100**.
    *   **Effect:** Restores Health by a random value of **10 to 20** (clamped to the current `max_health`).
    *   **Constraints:** Action fails if `Agent.money < 100`.
*   **Toggle Attributes:**
    *   A UI-only action that pauses the log view to inspect the full list of 15+ agent attributes (Identity, Physical, Personality, Skills).

### User Interface & Visualization
*   **Technical Specs:**
    *   **Resolution:** Fixed 1600x900 window.
    *   **Framerate:** Capped at 60 FPS.
    *   **Theme:** Dark Mode (Background: RGB 20,20,20; Panels: RGB 40,40,40).
*   **Three-Panel Layout:**
    *   **Left Panel (300px):** Real-time dashboard showing Name, Age, Money, Job, Vitals (Health/Happiness/Smarts/Looks), and Physical Energy.
    *   **Center Panel (Variable):**
        *   **Advanced Narrative Engine:** Replaced generic start messages with a **Novelistic Story Generator**. The engine synthesizes Weather, City Atmosphere, Socio-Economic Status (Wealth vs. Marital Happiness), Parental Age Gaps, and Personality Quirks to generate a unique, cohesive opening paragraph for every life (e.g., "Born during a storm to a 'Crazy' father checking for tracking chips").
        *   **Smart Text Rendering:** Implemented word-wrapping to ensure long narrative events fit cleanly within the panel without cutoff.
        *   **Interactive History:** The log is structured hierarchically by Year/Age. Users can click year headers (e.g., `[-] Age 5`) to expand or collapse historical details.
        *   **Universal Attribute Modal:** An overlay rendering detailed columns for Identity, Physical Stats, and Personality. This modal can now inspect **any** agent (Player or NPC) to view their hidden stats.
    *   **Right Panel (300px):**
        *   **Tabbed Navigation:** Actions are organized into switchable categories (**Main**, **Social**, **Assets**).
        *   **Dynamic Visibility:** Buttons appear/disappear based on context (e.g., "Find Job" hidden <16, "Work Overtime" hidden if unemployed).
        *   **Auto-Layout:** The interface automatically restacks buttons to fill gaps when items are hidden.
        *   **Social Dashboard:** The Social Tab now features a **Relationship List**. It renders dynamic cards for known contacts (Parents) displaying Name, Status (Alive/Deceased), and a color-coded Relationship Bar.
        *   **Interactive Cards:** Each relationship card includes "Attributes" (to view the NPC's stats) and "Interact" buttons.
        *   **Styling:** Buttons feature rounded corners and hover-responsive darkening (RGB 80,80,80).

## 🗺️ Roadmap (Planned Features)

The following features are planned to expand the simulation depth into a comprehensive life emulator:

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
*   **Alternative Medicine:**
    *   **Witch Doctors:** A high-risk medical option.
    *   **RNG Outcomes:** Can cure incurable diseases (like Cancer) instantly, have no effect, or result in immediate death (e.g., "You died after swallowing a toad's eye").
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
*   **The Scenario Engine (Moral Dilemmas):**
    *   **Random Pop-ups:** A system that interrupts the "Age Up" flow with multiple-choice scenarios.
    *   **Moral Choices:** *Example:* "You find a wallet with $100." (Keep it / Return it / Leave it).
    *   **Conflict Resolution:** *Example:* "A bully calls you a name." (Report him / Attack him / Ignore him).
    *   **Impact:** Choices directly affect Karma, Happiness, and Health.
*   **Genotype vs. Phenotype:**
    *   **Genetic Potential:** Agents spawn with attribute ranges.
    *   **Realized Attributes:** Stats grow based on environment.
*   **Developmental Stages:**
    *   **Infancy:** Motor skills.
    *   **Childhood:** Language, curiosity.
    *   **School Age:** Socialization, bullying.
    *   **Adolescence:** Puberty, rebellion.
*   **Emergent Identity:**
    *   **Discovery:** Sexuality/Religiousness emerge dynamically.
    *   **Core Memories:** Events permanently buffing/debuffing personality.

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

### 6. Scope of Reality: Strictly Material
*   **Constraint:** No supernatural, paranormal, or sci-fi elements (e.g., Ghosts, Aliens, Cryptids, Hauntings).
*   **Abstraction:** The simulation is grounded in **Deterministic Realism**.
    *   Events are strictly biological, sociological, or statistical.
    *   "Luck" is a mathematical probability modifier, not a magical force.
    *   *Reasoning:* Excluding paranormal logic reduces code complexity (no need for "Exorcism" mechanics or "Ghost Encounter" RNG) and maintains a consistent, grounded tone focused on real-life simulation.

### 7. Progression: Sandbox over Gamification
*   **Constraint:** No "Achievements," "Ribbons," "Badges," or global leaderboards.
*   **Abstraction:** The focus is on **Intrinsic Motivation**.
    *   The "Goal" is defined by the player (e.g., "I want to be a billionaire" or "I want to have 10 kids"), not by a checklist provided by the engine.
    *   We avoid tracking meta-data across save files to keep the architecture modular and focused on the current agent's lifecycle.
    *   *Reasoning:* This prevents "Checklist Fatigue" and encourages players to experiment with the sandbox mechanics rather than optimizing their life solely to unlock a badge.

### 8. The "Faux-Conomy": Static vs. Dynamic
*   **Constraint:** No supply-and-demand logic, stock market simulation, or global trade physics.
*   **Abstraction:** The economy is **Reference-Based**.
    *   **Base Values:** Every item (House, Car, Diamond Ring) has a static `Base_Price` in the config files.
    *   **Multipliers:** Prices are calculated at runtime: `Base_Price * Inflation_Multiplier * Country_Cost_of_Living_Multiplier`.
    *   **Real Estate:** Housing markets do not crash or boom based on inventory. They simply follow a randomized noise curve (e.g., `Current_Value = Previous_Value * random(0.95, 1.08)`).
    *   *Reasoning:* Building a real economic engine is a separate game entirely. This system ensures prices *feel* dynamic without requiring a math degree to balance.

### 9. Legal & Medical: Stat-Check Resolution
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