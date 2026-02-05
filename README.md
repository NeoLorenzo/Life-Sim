# Life-Sim

**Life-Sim** is a comprehensive, modular life simulation engine built in Python. It simulates the biological, economic, social, and cognitive trajectory of a human agent within a deterministic, configuration-driven world. The project emphasizes statistical realism, emergent behavior, and strict separation of concerns between simulation logic and visualization.

## 🎯 Current Implementation Status (Complete)

The simulation is a fully-featured life emulator with the following major systems implemented:

### ✅ Core Simulation Systems
- **Deterministic World Engine**: Seed-based reproducibility with monthly turn progression
- **Multi-Agent Architecture**: Player + NPCs with identical biological/economic rules
- **Advanced Genetics & Inheritance**: Multi-generational family trees with DNA-based trait transmission
- **Sophisticated Psychology**: Big Five personality model with infant temperament system
- **Cognitive Aptitude System**: Six-domain intelligence modeling with developmental curves
- **Dynamic Health & Aging**: Realistic mortality, growth, and senescence
- **Economic Simulation**: Jobs, salaries, wealth accumulation, and tier-based classification
- **Education System**: Complete academic pipeline with subject-based performance tracking
- **Relationship Engine**: Psychometric compatibility with complex social networks
- **Event System**: Contextual life events with choice-driven outcomes

### ✅ Advanced User Interface
- **Dynamic Background System**: Seasonal/wealth/location-aware visual environments with aspect-ratio-preserving scaling
- **Transparent UI Panels**: Alpha-blended interfaces with differential opacity
- **Interactive Visualizations**: Family trees and social graphs with physics simulation
- **Performance-Optimized Rendering**: Spatial indexing, viewport culling, and advanced caching
- **Responsive Layout**: Three-panel design with context-aware component visibility
- **Fully Resizable Window**: Dynamic window resizing with automatic UI adaptation and background scaling

### ✅ Technical Excellence
- **13 Core Modules**: Comprehensive simulation and rendering architecture
- **Configuration-Driven**: 289-line JSON config with all gameplay parameters
- **Performance Optimized**: Maintains 60 FPS with 200+ agents
- **Modular Design**: SOLID principles with clear separation of concerns
- **Extensible Architecture**: Plugin-ready systems for future enhancements

## 📚 Table of Contents

- [Project Structure](#-project-structure)
- [Core Modules](#core-modules)
  - [state.py - Data Models](#-statepy-module-structure)
  - [logic.py - Simulation Engine](#️-logicpy-module-structure)
  - [affinity.py - Relationship Engine](#-affinitypy-module-structure)
  - [social.py - Social Data Structures](#-socialpy-module-structure)
  - [school.py - Education System](#-schoolpy-module-structure)
  - [Rendering Package](#-rendering-package-structure)
- [Background System](#-background-system-structure)
- [Simulation Flow](#simulation-flow)
  - [Monthly Cycle](#monthly-simulation-cycle)
  - [State Mutation Contracts](#state-mutation-contracts)
- [Current Features](#-current-features-mvp-05)
- [Cognitive Aptitude System](#-cognitive-aptitude-system)
- [Development Tools & Settings](#️-development-tools--settings)
- [Planned Features](#-roadmap-planned-features)
- [Design Philosophy](#-design-philosophy--abstractions)
- [Architecture Decisions](#-key-architectural-decisions--trade-offs)
- [Installation & Usage](#️-installation--usage)
- [Development Standards](#-development-rules--standards)
- [Credits](#-credits--assets)

## 📁 Project Structure

```
Life-Sim/
├── main.py                    # Entry point and application bootstrap
├── config.json               # Simulation parameters and game configuration
├── constants.py              # Application constants and static settings
├── logging_setup.py          # Logging configuration and utilities
├── assets/                   # Static assets (icons, images, backgrounds)
│   ├── backgrounds/          # Dynamic background images for seasonal/wealth variation
│   └── icon_ft.png           # Application icon
├── logs/                     # Runtime log files (rotating)
├── life_sim/                 # Core simulation package
│   ├── __init__.py
│   ├── simulation/           # Simulation logic and state management
│   │   ├── __init__.py
│   │   ├── state.py          # Main simulation state and agent classes
│   │   ├── logic.py          # Core simulation loop and turn processing
│   │   ├── affinity.py       # Relationship and personality calculations
│   │   ├── social.py         # Social interactions and relationships
│   │   ├── school.py         # Education system and academic logic
│   │   └── events.py         # Event system and modal interactions
│   └── rendering/            # User interface and visualization
│       ├── __init__.py
│       ├── renderer.py       # Main UI renderer and layout management
│       ├── ui.py             # UI components and widgets
│       ├── background.py     # Dynamic background system and resource management
│       ├── family_tree.py    # Interactive family tree visualization
│       ├── social_graph.py   # Social network visualization
│       └── modals.py         # Modal dialog system
├── README.md                 # This file
├── LICENSE                   # MIT License
└── .gitignore               # Git ignore patterns
```

### Complete System Overview
- **7 Simulation Modules**: Core game logic, state management, relationships, education, events
- **6 Rendering Modules**: UI system, background management, visualizations, modals
- **Configuration-Driven**: All gameplay parameters externalized to `config.json`
- **Modular Architecture**: Clear separation of concerns with SOLID principles
- **Performance Optimized**: Advanced caching, spatial indexing, and viewport culling

### Architecture Overview
- **Entry Point**: `main.py` initializes the simulation, loads configuration, and starts the main game loop
- **Configuration**: `config.json` contains all simulation parameters (jobs, education, personality traits, etc.)
- **Simulation Core**: The `life_sim/simulation/` package handles all game logic, agent behavior, and state management
- **Rendering Layer**: The `life_sim/rendering/` package manages the Pygame-based UI, visualizations, and user interactions
- **Modular Design**: Each system (agents, relationships, education, rendering) is isolated in its own module following SOLID principles

## 📋 Core Modules

<details>
<summary><strong>state.py - Data Models</strong></summary>

The `state.py` module contains the core data models for the simulation, managing both individual agents and the global simulation state.

<details>
<summary><strong>Agent Class</strong></summary>

The `Agent` class represents all human entities (Player and NPCs) with a unified architecture:

<details>
<summary><strong>Core Identity & Biology</strong></summary>

- Basic bio-data: name, gender, age (stored as months), country, city
- Physical stats: health, happiness, IQ (Gaussian distribution), looks, money
- **Form Assignment**: `form` attribute for school form tracking (A, B, C, D)
- Genetic system: supports both procedurally generated "lineage heads" and inherited "descendants"

</details>

<details>
<summary><strong>Extended Attributes</strong></summary>

- Physical: strength, athleticism, endurance
- Personality: Big Five model (OCEAN) with 5 main traits and 30 sub-facets
- Hormonal curves: fertility and libido with genotype/phenotype separation
- Hidden traits: sexuality

</details>

<details>
<summary><strong>Life Systems</strong></summary>

- Academic: subject-based performance (Math, Science, Language Arts, History)
- Economic: job status, salary, monthly income processing
- Social: relationship network with affinity-based scoring and modifiers
- Time Management: Action Point (AP) system for daily activities

</details>

<details>
<summary><strong>State Management</strong></summary>

- Unique UUID and `is_player` flag for entity distinction
- Dynamic physique calculations (height, weight, BMI based on genetics and athleticism)
- Age-based progression with growth, puberty, and senescence phases

</details>

<details>
<summary><strong>Key Methods</strong></summary>

- `__init__()`: Initialize agent with config or inherited traits, including optional `form` parameter
- `_init_lineage_head()`: Generate traits for first-generation agents
- `_init_descendant()`: Inherit traits from parents using genetic formulas
- `_recalculate_max_health()`: Age-based health capacity calculation
- `_recalculate_hormones()`: Puberty and aging effects on fertility/libido
- `_recalculate_physique()`: Calculate weight, BMI from height and athleticism
- `get_attr_value()`: Unified attribute access for UI rendering
- `get_personality_sum()`: Calculate Big 5 trait totals

</details>

</details>

<details>
<summary><strong>SimState Class</strong></summary>

The `SimState` class serves as the central container for the entire simulation world:

<details>
<summary><strong>Core Responsibilities</strong></summary>

- **World Container**: Holds all agents (player + NPCs) and global systems
- **Time Management**: Tracks months, years, and calendar progression
- **School System**: Manages educational institutions and enrollment
- **Family Generation**: Creates multi-generational family trees
- **Narrative Engine**: Generates contextual birth and life event stories
- **Class Population**: Generates 80-student cohorts with form assignments

</details>

<details>
<summary><strong>Key Attributes</strong></summary>

- `player`: The main Agent controlled by the user
- `npcs`: Dictionary of all non-player agents (uid → Agent)
- `school_system`: Global education system instance
- `month_index`: Current month (0-11, where 0 = January)
- `year`: Current simulation year
- `history`: Log of all life events organized by year
- `config`: Reference to global configuration data

</details>

<details>
<summary><strong>Key Methods</strong></summary>

- `populate_classmates()`: Generates 79 classmates for total of 80 students with form assignments
- `_assign_form_to_student()`: Helper function for form assignment (A, B, C, D)
- `_link_agents()`: Creates bidirectional relationships with optional modifiers
- `_setup_family_and_player()`: Generates multi-generational family trees
- `_create_npc()`: Instantiates and registers new NPCs
- `start_new_year()`: Archives current year and starts new one
- `__init__()`: Initialize simulation world and generate family
- `add_log()`: Add events to the history buffer with color coding

</details>

<details>
<summary><strong>Initialization Process</strong></summary>

1. Load configuration and create school system
2. Set random start month for variety
3. Generate complete family tree (grandparents → parents → player)
4. Initialize player's relationships with all family members
5. Generate narrative birth story based on family context
6. Populate school classmates if player is enrolled

</details>

</details>

</details>

<details>
<summary><strong>⚙️ logic.py - Simulation Engine</strong></summary>

The `logic.py` module contains the core simulation engine that processes turns, handles agent actions, and manages the deterministic progression of the simulation world.

<details>
<summary><strong>Core Turn Processing</strong></summary>

**`process_turn(sim_state: SimState)`**
The main simulation loop that advances time by one month:

<details>
<summary><strong>Execution Order</strong></summary>

1. **Global Time Advancement**: Increment month counter, handle year rollover, log new year
2. **Player Processing**: Apply monthly updates to the player agent
3. **NPC Processing**: Apply updates to all NPCs, simulate their routines, handle death notifications
4. **Global Systems**: Process school systems and other world-level mechanics

</details>

<details>
<summary><strong>Key Design Principles</strong></summary>

- **Unified Loop**: Player and NPCs share identical biological/economic rules
- **Deterministic Order**: Critical for reproducible simulation results
- **Death Handling**: Automatic relationship updates when known NPCs die

</details>

</details>

<details>
<summary><strong>Agent Processing Functions</strong></summary>

**`_process_agent_monthly(sim_state, agent)`**
Applies comprehensive monthly updates to a single agent:

<details>
<summary><strong>A. Biological Updates</strong></summary>

- **Aging**: Increment `age_months` and detect birthdays
- **Annual Recalculation**: On birthdays, recalculate health capacity and hormones
- **Natural Entropy**: Seniors (50+) experience random health decay (0-3 points)

</details>

<details>
<summary><strong>B. Physical Development</strong></summary>

- **Growth Phase** (≤20 years): 20% chance monthly to grow 1cm toward genetic potential
- **Shrinkage Phase** (>60 years): 3% chance monthly to lose 1cm
- **Physique Update**: Recalculate weight, BMI, and body composition

</details>

<details>
<summary><strong>C. Time Management Reset</strong></summary>

- **AP Reset**: Clear used action points for new month
- **Sleep Recalculation**: Update sleep requirements based on age from config

</details>

<details>
<summary><strong>D. Economic Processing</strong></summary>

- **Salary Distribution**: Monthly payment (annual salary ÷ 12)
- **Player Logging**: Salary income logged for player, debug-only for NPCs

</details>

<details>
<summary><strong>E. Mortality Check</strong></summary>

- **Health Capping**: Enforce biological maximum health limits
- **Death Detection**: Mark agents as deceased when health ≤ 0

</details>

**`_simulate_npc_routine(npc)`**
Simulates NPC daily time allocation to maintain valid state:

<details>
<summary><strong>Time Allocation</strong></summary>

1. **Sleep** (Maintenance): Deduct required sleep hours
2. **Obligations** (Locked): Work (8h) or School (7h) if enrolled/employed
3. **Free Time**: Remaining AP for future AI decision-making

</details>

</details>

<details>
<summary><strong>Player Action Functions</strong></summary>

**`work(sim_state: SimState)`**
Handles overtime work for employed players:
- **Prerequisites**: Must be alive and employed
- **Payment**: 1% of annual salary as overtime bonus
- **Validation**: Checks employment status before processing

**`find_job(sim_state: SimState)`**
Manages job seeking for unemployed players:
- **Age Restriction**: Only available at age 16+
- **Random Selection**: Picks random job from configuration pool
- **Guaranteed Success**: Current implementation always succeeds

**`visit_doctor(sim_state: SimState)`**
Processes medical care for health restoration:
- **Cost Check**: Requires sufficient funds ($100)
- **Healing**: Random recovery (10-20 health points)
- **Health Capping**: Cannot exceed agent's maximum health capacity

</details>

<details>
<summary><strong>Integration Points</strong></summary>

**Main Loop Integration** (`main.py`)
- **Action Mapping**: UI actions mapped to logic functions via action IDs
- **State Updates**: Functions directly modify `sim_state` object
- **Logging**: All actions generate appropriate log entries

**Deterministic Behavior**
- **No Randomness in Core Logic**: All randomization uses seeded RNG
- **Reproducible Results**: Same seed + actions = identical outcomes
- **Debug Support**: Comprehensive logging for troubleshooting

</details>

<details>
<summary><strong>Error Handling & Validation</strong></summary>

**Safety Checks**
- **Life Status**: All functions verify agent is alive before processing
- **Prerequisites**: Actions validate required conditions (employment, funds, age)
- **State Consistency**: Maintains valid agent states after each operation

**Graceful Failures**
- **Informative Messages**: Clear feedback when actions cannot be performed
- **State Preservation**: Failed actions don't modify simulation state
- **Logging**: All failures logged for debugging

</details>

</details>

<details>
<summary><strong>🧠 affinity.py - Relationship Engine</strong></summary>

The `affinity.py` module contains the psychometric compatibility engine that calculates natural relationships between agents based on their Big Five personality traits. This system forms the foundation of all social interactions in the simulation.

### Data Contract
- **Inputs**: Two Agent objects with working `get_personality_sum(trait)` method
- **Outputs**: Integer score in `[-100, +100]` and optional list of `(label, value)` pairs
- **Side effects**: None (pure functions)
- **Invariants**:
  - **Symmetric**: `affinity(A, B) == affinity(B, A)`
  - **Bounded**: Score strictly clamped to `[AFFINITY_SCORE_MIN, AFFINITY_SCORE_MAX]`
  - **Additive**: All effects combine linearly

<details>
<summary><strong>Core Affinity Functions</strong></summary>

**Dual-Function Architecture:**

**`calculate_affinity(agent_a, agent_b)`** - **Lean Performance Path**
- **Purpose**: Calculates psychometric compatibility without building breakdown
- **Usage**: Bulk initialization (e.g., populating 80 classmates = 3,160 pairs)
- **Performance**: Zero allocations, identical math to breakdown version
- **Returns**: Integer compatibility score clamped to `[AFFINITY_SCORE_MIN, AFFINITY_SCORE_MAX]`

**`get_affinity_breakdown(agent_a, agent_b)`** - **Detailed Analysis Path**
- **Purpose**: Calculates full psychometric compatibility with labeled breakdown
- **Usage**: Social graph tooltips, debugging, player insight
- **Performance**: Includes list operations and label formatting
- **Returns**: Tuple of `(final_score, breakdown_list)` where breakdown contains only effects exceeding `AFFINITY_LABEL_THRESHOLD`

</details>

<details>
<summary><strong>Affinity Calculation Model</strong></summary>

The system uses a **Gravity Model** approach: `Total_Score = Base_Affinity + Sum(Active_Modifiers)`

**1. Actor Effects (Individual Traits)**
These affect how an agent relates to *anyone*:

**Neuroticism (The "Grump" Factor)**
- **Threshold**: `AFFINITY_ACTOR_THRESHOLD`+ points trigger penalties
- **Formula**: `-(Neuroticism - AFFINITY_ACTOR_THRESHOLD) * AFFINITY_ACTOR_WEIGHT`
- **Rationale**: High neuroticism agents universally drag down relationships; weighted at 0.5x so even max Neuroticism (120) only contributes -25, leaving dyadic compatibility as primary driver

**Agreeableness (The "Nice" Factor)**
- **Threshold**: `AFFINITY_ACTOR_THRESHOLD`+ points trigger bonuses
- **Formula**: `(Agreeableness - AFFINITY_ACTOR_THRESHOLD) * AFFINITY_ACTOR_WEIGHT`
- **Rationale**: High agreeableness provides universal social lubrication; symmetric with Neuroticism in structure and weight for meaningful cancellation

**2. Dyadic Effects (Similarity/Homophily)**
These compare traits between two agents using: `(AFFINITY_DYADIC_THRESHOLD - Delta) * WEIGHT`

**Openness (Shared Interests vs. Value Clash)**
- **Weight**: `AFFINITY_OPENNESS_WEIGHT` (0.8 - highest priority)
- **Positive**: "Shared Interests" when difference < `AFFINITY_DYADIC_THRESHOLD`
- **Negative**: "Value Clash" when difference > `AFFINITY_DYADIC_THRESHOLD`
- **Rationale**: Core value alignment is strongest predictor of long-term relationship viability

**Conscientiousness (Lifestyle Sync vs. Clash)**
- **Weight**: `AFFINITY_CONSCIENTIOUSNESS_WEIGHT` (0.8 - equal priority with Openness)
- **Positive**: "Lifestyle Sync" for similar organization levels
- **Negative**: "Lifestyle Clash" for different life approaches
- **Rationale**: People with incompatible routines grind against each other constantly

**Extraversion (Energy Match vs. Mismatch)**
- **Weight**: `AFFINITY_EXTRAVERSION_WEIGHT` (0.5 - lower priority)
- **Positive**: "Energy Match" for similar social energy levels
- **Negative**: **"Energy Mismatch"** for different energy levels (previously invisible in tooltips)
- **Rationale**: Energy mismatch creates friction but rarely breaks otherwise well-matched relationships

</details>

<details>
<summary><strong>Score Calculation Process</strong></summary>

**Performance-Optimized Dual Paths**

**For Bulk Initialization** (`calculate_affinity`):
1. **Actor Effects**: Apply Neuroticism/Agreeableness thresholds using constants
2. **Dyadic Effects**: Compute similarity for Openness, Conscientiousness, Extraversion
3. **Final Clamp**: `max(AFFINITY_SCORE_MIN, min(AFFINITY_SCORE_MAX, rounded_score))`
4. **Zero Allocations**: No list building, no label formatting, minimal branching

**For Detailed Analysis** (`get_affinity_breakdown`):
1. **Initialize**: Start with score = 0.0, empty breakdown list
2. **Actor Effects**: Apply individual trait modifiers for both agents
3. **Dyadic Effects**: Calculate similarity/difference penalties and bonuses
4. **Categorize Effects**: Label significant effects (> `AFFINITY_LABEL_THRESHOLD`) for UI display
5. **Final Clamp**: Round and clamp to `[AFFINITY_SCORE_MIN, AFFINITY_SCORE_MAX]`

**Breakdown Categories**
- **Positive Labels**: "Shared Interests (Openness)", "Lifestyle Sync (Order)", "Energy Match"
- **Negative Labels**: "Value Clash (Openness)", "Lifestyle Clash (Order)", **"Energy Mismatch"** (new)
- **Individual Labels**: "{Name}'s Neuroticism", "{Name}'s Agreeableness"
- **Filtering**: Only effects exceeding `AFFINITY_LABEL_THRESHOLD` appear in breakdown

</details>

<details>
<summary><strong>Integration Points</strong></summary>

**Family Generation** (`state.py`)
- **Spouse Matching**: Base marriage score (40) + affinity + history variance
- **Parent-Child**: Biological imperative (50) + affinity
- **Sibling Bonds**: Base sibling score (20) + affinity
- **In-Law Relationships**: Pure affinity-based scoring

**School System** (`state.py`)
- **Classmate Networks**: All students in a cohort are linked using affinity
- **Relationship Types**: 
  - >20 affinity: "Acquaintance"
  - -20 to 20: "Classmate" 
  - <-20: "Rival"

**Social Graph Visualization** (`social_graph.py`)
- **Gradient Color System**: Node and edge colors use smooth gradient interpolation
- **Form-Based Visualization**: Students in same form receive visual relationship bonuses
- **Interactive Tooltips**: Real-time affinity breakdown with gradient-coded scores
- **Advanced Navigation**: Pan, zoom, and drag interactions with physics simulation

**Color Gradient System**
- **Node Colors**: Light Gray (0) → Green (+100) for positive, Light Gray (0) → Red (-100) for negative
- **Edge Colors**: Matching gradient system for visual consistency
- **Tooltip Integration**: All relationship scores use same gradient logic
- **Neutral Baseline**: Score of 0 displays as neutral light gray (200, 200, 200)

**Form-Based Features**
- **Same Form Visualization**: Students in same form show enhanced relationships
- **Modifier Display**: "Same Form" (+10) modifiers shown in detailed tooltips
- **Cohort Organization**: Visual grouping by form assignments
- **Social Cohesion**: Enhanced visual feedback for form-based relationships

</details>

<details>
<summary><strong>Design Principles</strong></summary>

**Psychometric Foundation**
- **Big Five Model**: Based on established OCEAN personality psychology
- **Research-Backed**: Weightings reflect real-world relationship research
- **Deterministic**: Same personality profiles always produce identical results

**Mathematical Properties**
- **Symmetric**: `affinity(A, B) == affinity(B, A)`
- **Bounded**: Scores strictly clamped to [-100, +100]
- **Additive**: Multiple effects combine linearly for predictable behavior

**Game Balance**
- **Mean Reversion**: Extreme personalities have strong effects but don't dominate
- **Threshold-Based**: Effects only trigger beyond meaningful personality levels
- **Weight Hierarchy**: Core values (Openness, Conscientiousness) weighted higher than social energy

</details>

<details>
<summary><strong>Extensibility</strong></summary>

**Future Enhancements**
- **Cultural Factors**: Could add cultural compatibility modifiers
- **Age Preferences**: Age-based attraction/repulsion factors
- **Situational Modifiers**: Context-dependent affinity adjustments
- **Learning System**: Agents could adapt based on relationship success/failure

<details>
<summary><strong>Performance Considerations</strong></summary>

**Optimized for Scale**
- **Dual-Function Design**: `calculate_affinity` for bulk (3,160+ pairs), `get_affinity_breakdown` for UI
- **Zero Allocations in Hot Path**: Bulk initialization avoids list operations completely
- **Constants-Driven**: All thresholds/tuning in `constants.py` for cache locality
- **Symmetric Math**: Same calculation for `affinity(A,B)` and `affinity(B,A)` enables memoization

**Quantitative Impact**
- **80 classmates**: 3,160 relationship calculations during initialization
- **Memory Saved**: ~2-5 MB by avoiding unnecessary list allocations
- **Performance**: Microseconds per pair, but significant at population scale
- **Maintenance**: Byte-for-byte identical math ensures consistency between functions

**Pure Function Properties**
- **No Side Effects**: Safe for parallelization and caching
- **Deterministic**: Same personalities + seed = identical results
- **Thread-Safe**: No shared state modifications

</details>

</details>

</details>

<details>
<summary><strong>👥 social.py - Social Data Structures</strong></summary>

The `social.py` module defines the data structures that manage social connections and relationship dynamics between agents. It provides the foundational classes for representing how agents relate to each other through a flexible modifier system.

<details>
<summary><strong>Core Data Structures</strong></summary>

**`@dataclass Modifier`**
Represents temporary or permanent factors that affect relationship scores:

**Key Attributes**
- `name`: String identifier for the modifier (e.g., "Maternal Bond", "Marriage", "Same Form", "Argument")
- `value`: Numeric impact on relationship score (positive or negative)
- `duration`: Time remaining in months (-1 for permanent modifiers)
- `decay`: Monthly reduction rate for time-based modifiers

**Use Cases**
- **Permanent Bonds**: Marriage (+60), Maternal/Paternal Bond (+80)
- **Form-Based**: "Same Form" (+10) for students in the same school form
- **Temporary Effects**: "Recent Argument" (-20, duration: 3 months)
- **Decaying Effects**: "New Romance" (+30, decay: -5 per month)

**`Relationship` Class**
Represents a social connection between two agents with dynamic scoring:

**Core Properties**
- `owner_uid`: UUID of the agent who owns this relationship
- `target_uid`: UUID of the agent this relationship points to
- `rel_type`: Relationship type ("Friend", "Spouse", "Classmate", "Rival", etc.)
- `target_name`: Human-readable name of the target agent
- `is_alive`: Boolean indicating if target agent is still living
- `base_affinity`: Natural psychometric compatibility score
- `modifiers`: List of active Modifier objects

**Dynamic Scoring System**
- `modifiers`: List of active Modifier objects affecting the relationship
- `cached_score`: Calculated total score (base_affinity + sum(modifiers))
- `total_score`: Property accessor for the current relationship value

</details>

<details>
<summary><strong>Relationship Mechanics</strong></summary>

**Score Calculation Formula**
```
Total Score = Base Affinity + Σ(Active Modifiers)
Final Score = clamp(Total Score, -100, +100)
```

**Modifier Management**
- **Add/Update**: `add_modifier()` creates new modifiers or overwrites existing ones
- **Automatic Recalculation**: Score updates immediately when modifiers change
- **Decay Processing**: Time-based modifiers can decrease in value over time
- **Permanent vs. Temporary**: Distinguished by duration (-1 = permanent)

**Score Range & Interpretation**
- **-100 to -20**: Strongly negative (Enemy, Nemesis)
- **-20 to 20**: Neutral/Weak (Acquaintance, Stranger)
- **20 to 60**: Positive (Friend, Good Relationship)
- **60 to 100**: Very Positive (Best Friend, Close Family)

</details>

<details>
<summary><strong>Key Methods</strong></summary>

**`add_modifier(name, value, duration=-1, decay=0.0)`**
Manages relationship modifiers with intelligent updates:
- **Overwrite Logic**: Replaces existing modifiers with same name
- **Immediate Recalculation**: Updates cached score automatically
- **Flexible Duration**: Supports both permanent and temporary effects

**`recalculate()`**
Core scoring algorithm:
- **Summation**: Adds base affinity to all active modifier values
- **Clamping**: Ensures final score stays within [-100, +100] bounds
- **Caching**: Stores result for efficient repeated access

</details>

<details>
<summary><strong>Legacy Compatibility</strong></summary>

**Dictionary Interface**
Provides backward compatibility with existing code:
- `__getitem__()`: Allows dictionary-style access (rel["value"], rel["type"])
- `__setitem__()`: Limited write access for specific properties
- **Migration Path**: Smooth transition from old dict-based to object-oriented design

**Supported Keys**
- `"value"`: Returns cached_score
- `"type"`: Returns rel_type
- `"name"`: Returns target_name
- `"is_alive"`: Returns is_alive status

</details>

<details>
<summary><strong>Integration Points</strong></summary>

**Affinity Engine Integration**
- **Base Scores**: Receives initial compatibility from `affinity.calculate_affinity()`
- **Dynamic Adjustment**: Modifiers can enhance or diminish natural compatibility
- **Bidirectional**: Each agent maintains their own relationship object

**Family Generation** (`state.py`)
- **Structural Bonds**: Uses permanent modifiers for family relationships
- **Inheritance**: Parent-child bonds get +50 biological imperative
- **Marriage**: Spouse relationships combine affinity with +60 marriage bond

**Social Systems**
- **Network Formation**: Classmates, coworkers, and community members
- **Event Processing**: Life events can add/remove modifiers
- **Temporal Dynamics**: Relationships evolve through modifier changes

</details>

<details>
<summary><strong>Design Principles</strong></summary>

**Separation of Concerns**
- **Data Structure Only**: Contains no game logic, pure data management
- **Reusable Components**: Modifier system works for any relationship type
- **Clear Boundaries**: Distinct from affinity calculation and social logic

**Performance Optimization**
- **Cached Scoring**: Avoids recalculation when modifiers haven't changed
- **Lightweight Objects**: Minimal memory footprint per relationship
- **Efficient Updates**: Only recalculates when modifiers are modified

**Extensibility**
- **Flexible Modifier System**: Easy to add new relationship effects
- **Type Agnostic**: Works for any relationship category
- **Temporal Support**: Built-in support for time-based relationship changes

</details>

<details>
<summary><strong>Usage Patterns</strong></summary>

**Family Relationships**
```python
# Mother-child bond
rel.add_modifier("Maternal Bond", 80, duration=-1)  # Permanent
```

**Social Events**
```python
# Recent argument
rel.add_modifier("Argument", -20, duration=3)  # 3 months
```

**Life Changes**
```python
# Marriage bonus
rel.add_modifier("Marriage", 60, duration=-1)  # Permanent
```

**Temporary Effects**
```python
# New friendship bloom
rel.add_modifier("New Friendship", 30, decay=5.0)  # Decays over time
```

</details>

<details>
<summary><strong>📅 events.py - Event System</strong></summary>

The `events.py` module manages the monthly event system, handling triggers, user choices, and effect application.

### Data Contract
- **Inputs**: `SimState` and `config.json` event definitions
- **Outputs**: `EventInstance` objects for the UI, state mutations upon resolution
- **Side Effects**: Modifies agent stats, relationships, flags, and history

<details>
<summary><strong>Core Components</strong></summary>

**`EventManager` Class**
- **Singleton Controller**: Manages the lifecycle of events from loading to resolution.
- **Trigger Evaluation**: Checks age, month, stats, and flags against event definitions.
- **Deterministic RNG**: Uses a seeded random instance derived from the master seed + total months lived.
- **Resolution Logic**: Applies complex effects (stats, flags, school subjects) based on user choices.

**`Event` & `EventInstance`**
- **Event**: Static definition loaded from config (ID, title, requirements).
- **EventInstance**: Runtime object representing an active event waiting for input.

</details>

<details>
<summary><strong>Event Mechanics</strong></summary>

**Triggering Flow**
1.  **Age Up**: Player advances the month.
2.  **Evaluation**: `EventManager` scans valid events for the new age/month.
3.  **Priority**: Highest priority event wins (if multiple qualify).
4.  **Blocking**: Simulation pauses, and the UI displays the `EventModal`.

**Configuration Schema**
- **Triggers**: `min_age`, `max_age`, `month`, `required_flags`, `required_stats`.
- **UI Types**: `single_select` (Radio) or `multi_select` (Checkbox).
- **Constraints**: `min_selections`, `max_selections` (e.g., for Subject Selection).
- **Effects**: Modify stats, relationships, add flags, or set special data (e.g., school subjects).

</details>
</details>

</details>

## Monthly Simulation Cycle

The simulation advances in **1-month increments** when the player clicks "Age Up (+1 Month)". Each turn follows a deterministic order of operations:

<details>
<summary><strong>1. Global Time Advancement</strong></summary>

- Increment month counter and handle year rollover
- Update simulation date (Month/Year) for timeline tracking

</details>

<details>
<summary><strong>2. Agent Processing (Player & NPCs)</strong></summary>

All agents (Player and NPCs) process the same monthly sequence:

**A. Biological Updates**
- Age increment (monthly aging)
- Birthday check: annual biological recalculation (health capacity, hormones)
- **Temperament-to-Personality Transition:** At age 3, temperament crystallizes into permanent Big 5 personality
- **Plasticity Decay:** Infants (0-2) experience age-based plasticity reduction (100% → 60% → 30%)
- Natural entropy: seniors (50+) experience random health decay

**B. Physical Development**
- Height growth for children/teens (stochastic, 20% chance/month)
- Age-related shrinkage for seniors (60+, 3% chance/month)
- Physique recalculation (weight, BMI based on genetics and athleticism)

**C. Time Management Reset**
- Action Points (AP) reset to full 24.0 daily budget
- Sleep needs recalculated based on age bracket from config
- Locked AP allocated for mandatory obligations (School/Work)

**D. Economic Processing**
- Monthly salary distribution (annual salary ÷ 12)
- Income added to agent's money balance

</details>

<details>
<summary><strong>3. NPC-Specific Processing</strong></summary>

- Automated routine: NPCs auto-spend AP on mandatory tasks
- Death notifications: Player informed when known NPCs die

</details>

<details>
<summary><strong>4. Global System Updates</strong></summary>

- **School System**: Academic progress, enrollment, graduation
- Subject grades updated based on natural aptitude
- Monthly change tracking for performance visualization

</details>

<details>
<summary><strong>5. Mortality Check</strong></summary>

- Health clamped to maximum capacity
- Death condition: agents marked as deceased if health ≤ 0
- Player death ends the simulation; NPC deaths trigger relationship updates

</details>

<details>
<summary><strong>Key Design Principles</strong></summary>

- **Unified Loop**: Player and NPCs share identical biological/economic rules
- **Deterministic**: Same seed + actions = identical outcomes
- **Order Preservation**: Critical for reproducible simulation results
- **Separation of Concerns**: Global systems (school) process after individual agents

</details>

## State Mutation Contracts

This section documents exactly how state changes flow through the simulation, which methods modify which parts of the state, and the order of operations during monthly turns. Understanding these contracts is critical for preventing unexpected side effects when adding new features.

<details>
<summary><strong>Core Monthly Turn Process</strong></summary>

The simulation follows a strict deterministic order during each monthly turn (`process_turn()`):

#### 1. Global Time Advancement
**Function**: `process_turn()` (lines 24-29)
**State Modified**: `SimState.month_index`, `SimState.year`
**Conditions**: Always executes
**Effects**:
- Increments `month_index` (0-11, where 0 = January)
- On year rollover (month_index > 11): resets to 0 and increments `year`
- Logs "Happy New Year!" message

#### 2. Player Processing
**Function**: `_process_agent_monthly(sim_state, player)` (lines 31-32)
**State Modified**: Player agent attributes
**Conditions**: Player must be alive (`player.is_alive == True`)

#### 3. NPC Processing
**Function**: `_process_agent_monthly(sim_state, npc)` + `_simulate_npc_routine(npc)` (lines 34-48)
**State Modified**: All NPC agents + player relationships
**Conditions**: NPC must be alive
**Side Effects**: Updates player relationships when known NPCs die

#### 4. Global System Updates
**Function**: `school.process_school_turn(sim_state)` (line 51)
**State Modified**: School system, agent academic performance
**Conditions**: Always executes

</details>

<details>
<summary><strong>Agent State Mutation Functions</strong></summary>

#### `_process_agent_monthly(sim_state, agent)`
**Location**: `logic.py` lines 55-117
**Applies To**: All agents (player + NPCs)
**State Modifications**:

**A. Biological Updates**
- `agent.age_months += 1` (always)
- Birthday detection: `agent.age_months % 12 == 0`
  - Calls `agent._recalculate_max_health()` (modifies `agent.max_health`)
  - Calls `agent._recalculate_hormones()` (modifies `agent.fertility`, `agent.libido`)
  - Seniors (age > 50): `agent.health -= random.randint(0, 3)`

**B. Physical Development**
- Growth (age ≤ 20, height < potential): 20% chance `agent.height_cm += 1`
- Shrinkage (age > 60): 3% chance `agent.height_cm -= 1`
- Calls `agent._recalculate_physique()` (modifies `agent.lean_mass`, `agent.weight_kg`, `agent.bmi`)

**C. Time Management Reset**
- `agent.ap_used = 0.0` (reset monthly budget)
- Calls `agent._recalculate_ap_needs()` (modifies `agent.ap_sleep`)

**D. Economic Processing**
- If employed: `agent.money += int(agent.job['salary'] / 12)`

**E. Mortality Check**
- Enforces health cap: `agent.health = min(agent.health, agent.max_health)`
- Death detection: `agent.is_alive = False` if `agent.health <= 0`

#### `_simulate_npc_routine(npc)`
**Location**: `logic.py` lines 118-140
**Applies To**: NPCs only
**State Modifications**:
- `npc.ap_used += npc.ap_sleep` (sleep allocation)
- `npc.ap_locked = 8.0` if employed, `7.0` if in school, `0.0` otherwise
- `npc.ap_used += npc.ap_locked` (obligation allocation)

</details>

<details>
<summary><strong>Player Action Functions (State Mutating)</strong></summary>

#### `work(sim_state)`
**Location**: `logic.py` lines 141-156
**Prerequisites**: Player alive + employed
**State Modifications**:
- `player.money += int(player.job['salary'] * 0.01)` (1% overtime bonus)
**Pure**: No - modifies player money

#### `find_job(sim_state)`
**Location**: `logic.py` lines 157-174
**Prerequisites**: Player alive + unemployed
**State Modifications**:
- `player.job = random.choice(jobs)` (assigns new job)
**Pure**: No - modifies player job

#### `visit_doctor(sim_state)`
**Location**: `logic.py` lines 175-193
**Prerequisites**: Player alive + sufficient money ($100)
**State Modifications**:
- `player.money -= constants.DOCTOR_VISIT_COST` (deducts cost)
- `player.health = min(player.max_health, player.health + recovery)` (heals)
**Pure**: No - modifies player money and health

</details>

<details>
<summary><strong>Agent Internal State Mutators</strong></summary>

#### `Agent._recalculate_max_health()`
**Location**: `state.py` lines 278-298
**Trigger**: Birthdays, age changes
**State Modifications**:
- `agent.max_health` (age-based capacity calculation)
- `agent.health` (clamped to new maximum if exceeded)
**Pure**: No - modifies agent health state

#### `Agent._recalculate_hormones()`
**Location**: `state.py` lines 377-435
**Trigger**: Birthdays, age changes
**State Modifications**:
- `agent.fertility` (age/gender-based calculation)
- `agent.libido` (age/gender-based calculation)
**Pure**: No - modifies agent hormonal state

#### `Agent._recalculate_physique()`
**Location**: `state.py` lines 437-465
**Trigger**: Height changes, athleticism changes
**State Modifications**:
- `agent.lean_mass` (calculated from height and athleticism)
- `agent.weight_kg` (calculated from lean mass and body fat)
- `agent.bmi` (calculated from weight and height)
**Pure**: No - modifies agent physique state

#### `Agent._recalculate_ap_needs()`
**Location**: `state.py` lines 467-483
**Trigger**: Birthdays, configuration changes
**State Modifications**:
- `agent.ap_sleep` (age-based sleep requirements from config)
**Pure**: No - modifies agent time management state

</details>

<details>
<summary><strong>SimState State Mutators</strong></summary>

#### `SimState._link_agents()`
**Location**: `state.py` lines 1249-1267
**Trigger**: Family generation, relationship creation
**State Modifications**:
- `agent_a.relationships[agent_b.uid]` (creates relationship object)
- `agent_b.relationships[agent_a.uid]` (creates reciprocal relationship)
**Pure**: No - modifies relationship networks

#### `SimState.start_new_year()`
**Location**: `state.py` lines 1269-1280
**Trigger**: Player birthdays
**State Modifications**:
- `self.history` (archives previous year)
- `self.current_year_data` (creates new year structure)
**Pure**: No - modifies historical data

#### `SimState.add_log()`
**Location**: `state.py` lines 1282-1286
**Trigger**: Events, actions, notifications
**State Modifications**:
- `self.current_year_data["events"]` (adds event log entry)
**Pure**: No - modifies event history

#### `EventManager.apply_resolution()`
**Location**: `events.py`
**Trigger**: User confirms event choice
**State Modifications**:
- `sim_state.player.*` (Stats, Money, Relationships based on effects)
- `sim_state.flags` (Adds new narrative flags)
- `sim_state.event_history` (Logs event ID)
- `sim_state.pending_event` (Clears active event)
**Pure**: No - modifies player state and history

</details>

<details>
<summary><strong>Pure Functions (No Side Effects)</strong></summary>

These functions are safe to call anywhere without担心 state mutations:

#### `affinity.calculate_affinity(agent_a, agent_b)`
**Location**: `affinity.py` lines 89-94
**Returns**: Integer compatibility score (-100 to +100)
**Pure**: Yes - only reads agent personality data

#### `affinity.get_affinity_breakdown(agent_a, agent_b)`
**Location**: `affinity.py` lines 11-87
**Returns**: Tuple of (score, breakdown_list)
**Pure**: Yes - only reads agent personality data

#### `Agent.get_attr_value(name)`
**Location**: `state.py` lines 234-271
**Returns**: Attribute value by string name
**Pure**: Yes - only reads agent data

#### `Agent.get_personality_sum(trait)`
**Location**: `state.py` lines 334-336
**Returns**: Sum of personality facet values
**Pure**: Yes - only reads personality data

#### `Agent.age` (property)
**Location**: `state.py` lines 273-276
**Returns**: Age in years (calculated from age_months)
**Pure**: Yes - computed property, no state change

#### `Agent.free_ap` (property)
**Location**: `state.py` lines 485-488
**Returns**: Available action points
**Pure**: Yes - computed property, no state change

</details>

<details>
<summary><strong>State Mutation Dependencies</strong></summary>

#### Critical Order Dependencies
1. **Aging must precede health recalculation**: `age_months` increment affects `_recalculate_max_health()`
2. **Health recalculation must precede mortality check**: New `max_health` affects death detection
3. **AP reset must precede NPC routine**: Fresh AP budget needed for `_simulate_npc_routine()`
4. **School processing must follow agent updates**: Academic performance depends on current agent state

#### Safe Modification Patterns
- **Adding new agent attributes**: Initialize in `Agent.__init__()`, update in appropriate `_recalculate_*()` method
- **Adding new monthly processes**: Add to `_process_agent_monthly()` after existing updates
- **Adding new player actions**: Follow pattern of `work()`, `find_job()`, `visit_doctor()` - check prerequisites, modify state, log results
- **Adding new pure functions**: Place in appropriate module (affinity.py for calculations, state.py for accessors)

#### Dangerous Patterns to Avoid
- **Modifying state in pure functions**: Breaks deterministic behavior
- **Skipping life status checks**: Can cause operations on dead agents
- **Modifying relationships outside `_link_agents()`**: Bypasses bidirectional consistency
- **Direct health modifications without clamping**: Can exceed biological limits

</details>

<details>
<summary><strong>Debugging State Mutations</strong></summary>

When debugging unexpected state changes:

1. **Check turn order**: Verify the change happens in the expected phase
2. **Verify life status**: Ensure `agent.is_alive` checks are present
3. **Check bidirectional relationships**: Ensure both sides of relationships are updated
4. **Validate health bounds**: Ensure health stays within `[0, max_health]` range
5. **Log all mutations**: Use `sim_state.add_log()` for state-changing operations

This contract ensures predictable simulation behavior and helps engineers understand the full impact of their code changes on the simulation state.

</details>

<details>
<summary><strong>🏫 school.py - Education System</strong></summary>

The `school.py` module manages the educational system, including school institutions, form assignments, and academic progression. It provides the infrastructure for organizing students into forms and tracking their educational journey.

<details>
<summary><strong>School Class</strong></summary>

The `School` class represents an educational institution with form-based organization:

**Core Properties**
- `id`: Unique school identifier from configuration
- `name`: School name (e.g., "Springfield High School")
- `type`: School type (e.g., "High School", "Elementary")
- `start_month`/`end_month`: Academic year calendar bounds
- `forms_per_year`: Number of forms per grade level (typically 4: A, B, C, D)
- `class_capacity`: Maximum students per form
- `student_forms`: Dictionary tracking student_id → form_letter assignments

**Key Methods**
- `get_grade_info(index)`: Returns grade information by index
- `get_random_form_label()`: Returns random form letter (A, B, C, D)
- `enroll_student(student_id, form=None)`: Enrolls student in specific or random form
- `get_form_students(form_letter)`: Returns list of student IDs in given form

</details>

<details>
<summary><strong>Form Assignment System</strong></summary>

**Student Tracking**
- **Central Registry**: `student_forms` dictionary maintains all student assignments
- **Flexible Enrollment**: Students can be assigned to specific forms or random placement
- **Query Support**: Easy retrieval of all students in a particular form

**Form Distribution Logic**
- **Even Allocation**: Students distributed across available forms
- **Capacity Management**: Respects `forms_per_year` and `class_capacity` constraints
- **Random Assignment**: When no specific form requested, uses weighted random selection

</details>

<details>
<summary><strong>Academic System Integration</strong></summary>

**Monthly Processing** (`process_school_turn()`)
- **Player & NPC Processing**: Handles all enrolled agents each month
- **Academic Progress**: Updates subject grades based on natural aptitude
- **Session Management**: Tracks school year start/end and enrollment periods

**Enrollment Logic** (`_handle_school_start()`)
- **Age-Based Enrollment**: Automatically enrolls eligible students at appropriate grade levels
- **Form Assignment**: Assigns students to forms using school's random form selection
- **Session Activation**: Starts academic sessions at beginning of school year

**Academic Performance** (`_handle_school_end()`)
- **Grade Evaluation**: Determines passing/failing based on performance threshold (>20)
- **Progression Logic**: Advances students to next grade or handles graduation
- **Form Preservation**: Students maintain their form assignment when advancing grades

</details>

<details>
<summary><strong>School Year Calendar</strong></summary>

**Academic Timeline**
- **Start Month**: Beginning of academic year (typically September)
- **End Month**: End of academic year (typically June)
- **Session Management**: `is_in_session` flag tracks active learning periods
- **Summer Break**: Automatic session end with performance evaluation

**Grade Structure**
- **Multi-Stage Education**: Supports primary, secondary, and higher education stages
- **Linear Progression**: Students advance through grades based on age and performance
- **Form Consistency**: Students remain in same form throughout their time at the school

</details>

<details>
<summary><strong>Integration Points</strong></summary>

**State Management** (`state.py`)
- **Class Population**: `populate_classmates()` generates 80-student cohorts
- **Form Assignment**: Uses school's form tracking system for student organization
- **Academic Enrollment**: Automatic enrollment when players reach eligible age

**Agent Education**
- **Subject Performance**: Monthly grade updates based on natural aptitude
- **Progress Tracking**: Monthly change tracking for performance visualization
- **Form-Based Social Structure**: Students in same form receive relationship bonuses

**Configuration System**
- **School Definitions**: Loaded from `config.json` education section
- **Structural Parameters**: Forms per year, class capacity, academic calendar
- **Grade Progression**: Age-based grade level assignments and requirements

</details>

<details>
<summary><strong>Design Principles</strong></summary>

**Modular Architecture**
- **Separation of Concerns**: School logic isolated from agent state management
- **Configuration-Driven**: School structure defined in external configuration files
- **Extensible Design**: Easy to add new school types or academic systems

**Deterministic Behavior**
- **Reproducible Enrollment**: Same configuration produces identical form assignments
- **Predictable Progression**: Academic advancement follows defined rules
- **Consistent Calendar**: Academic year timing is fixed and reproducible

**Performance Optimization**
- **Efficient Lookups**: Dictionary-based form tracking for O(1) student queries
- **Batch Processing**: Monthly updates process all enrolled students efficiently
- **Minimal State**: Lightweight school objects with essential tracking data

</details>

</details>

<details>
<summary><strong>🎨 Rendering Package Structure</strong></summary>

The rendering system uses Pygame to create a responsive three-panel layout with modular UI components:

<details>
<summary><strong>UI Architecture</strong></summary>

**Main Renderer (`renderer.py`)**
- **Resizable Window**: Dynamic window resizing with `pygame.RESIZABLE` flag and automatic UI adaptation
- **Three-Panel Layout**: Responsive layout with Left (300px), Center (variable), Right (300px) panels
- **Layout Management**: Real-time panel recalculation on window resize events
- **Event Hub**: Central event handling with priority-based modal system
- **State Management**: Tracks viewing modes (agent attributes, family tree, social graph)
- **UI Initialization**: Creates tabs, buttons, and manages dynamic visibility rules

**Core UI Components (`ui.py`)**
- **Button**: Interactive buttons with hover states and action IDs
- **LogPanel**: Scrollable, word-wrapped event history with collapsible year headers and responsive resizing
- **APBar**: 24-segment visual representation of daily Action Point budget
- **Responsive Design**: All UI components adapt to window size changes with proper validation

**`modals.py` - Event System UI**
- **EventModal**: A specialized overlay for handling multiple-choice events.
    - **Dynamic Layout**: Automatically adjusts height based on description length and choice count.
    - **Selection Logic**: Supports both single-select (radio) and multi-select (checkbox) paradigms.
    - **Validation**: Enforces `min/max` selection constraints before enabling the "Confirm" button.
    - **Visual Feedback**: Highlights selected options and displays effect previews (if configured).

**Interactive Visualizations**
- **FamilyTreeLayout**: Layered graph with pan/zoom, node interaction, and relationship-based positioning
- **SocialGraphLayout**: Real-time force-directed physics simulation with filtering controls

</details>

<details>
<summary><strong>UI Component Interaction</strong></summary>

**Event Flow**
1. **Main Loop** (`main.py`) passes events to `Renderer.handle_event()`
2. **Priority System**: Modals (social graph, family tree, attributes) → Tabs → Buttons → Dynamic elements
3. **Action Processing**: Returns action IDs to main loop for simulation state changes

**State Synchronization**
- **Read-Only Access**: UI components read from `sim_state` for rendering
- **Event-Driven Updates**: Main loop processes actions and updates simulation state
- **Render Cycle**: `Renderer.render()` called each frame with updated state

**Dynamic Visibility**
- **Context Rules**: Buttons appear/disappear based on agent state (age, job status, etc.)
- **Auto-Layout**: UI elements reflow when visibility changes
- **Modal Management**: Center panel switches between log, modals, and visualizations

**Interactive Features**
- **Tooltips**: Hover information for grades and relationships
- **Pinning System**: Click attribute cards to pin them to the dashboard
- **Real-time Physics**: Social graph updates continuously when open
- **Infinite Canvas**: Family tree and social graph support pan/zoom navigation

</details>

<details>
<summary><strong>Design Principles</strong></summary>

- **Separation of Concerns**: Rendering logic isolated from simulation state
- **Event-Driven**: UI actions flow through main loop for state consistency
- **Component Reusability**: Modular widgets for consistent behavior
- **Performance Optimized:** Vectorized viewport culling, pre-rendered node surfaces, and zero-allocation draw loops
- **Advanced Social Graph Optimizations:**
  - **Spatial Indexing**: 150x150 pixel grid cells for O(1) visibility queries on large graphs
  - **Viewport Culling**: Dynamic bounds checking with zoom-level padding to skip off-screen elements
  - **Edge Color Caching**: Pre-calculated edge colors and widths during build() instead of per-frame computation
  - **Label Surface Caching**: Cached font.render() results to avoid repeated text rendering
  - **Batch Drawing**: Grouped edges and nodes by color to reduce pygame state changes
  - **Zoom-Based Label Opacity**: Labels fade out smoothly between 0.8x and 0.4x zoom levels
  - **Performance Impact**: Maintains 60 FPS with 200+ agents when zoomed in

</details>

</details>

<details>
<summary><strong>🖼️ Background System Structure</strong></summary>

The `background.py` module contains the dynamic background system that provides contextual visual environments based on game state.

<details>
<summary><strong>ResourceManager Class</strong></summary>

Handles efficient loading and caching of background images:

**Core Responsibilities**
- **Image Caching**: Maintains in-memory cache of loaded backgrounds to avoid repeated disk I/O
- **Automatic Scaling**: Scales all images to screen dimensions (SCREEN_WIDTH × SCREEN_HEIGHT)
- **Performance Optimization**: Uses `.convert()` for optimal Pygame rendering performance
- **Error Handling**: Graceful fallback when image files are missing

**Key Methods**
- `get_image(filename)`: Load and cache background images with error handling
- `clear_cache()`: Clear all cached images (useful for memory management)

**Technical Features**
- **Lazy Loading**: Images only loaded when first requested
- **Path Construction**: Uses `constants.ASSETS_BG_DIR` for consistent file organization
- **Logging Integration**: Warning messages for missing files with full error context

</details>

<details>
<summary><strong>BackgroundManager Class</strong></summary>

Manages intelligent background selection based on simulation state:

**Core Logic**
- **Location Detection**: Determines appropriate location (hospital/home) based on player age and birth month
- **Wealth Tier Calculation**: Computes family wealth tier including parental wealth for minors
- **Season Determination**: Maps current month to appropriate season using deterministic logic
- **Dynamic Filename Generation**: Constructs target filenames using `{location}_tier{tier}_{season}.png` pattern

**Key Methods**
- `_get_season(month_index)`: Convert month index (0-11) to season string
- `_get_wealth_tier(sim_state)`: Calculate wealth tier (1-5) based on total family wealth
- `update(sim_state)`: Update background based on current game state
- `draw(screen)`: Render current background or fallback color

**Intelligent Features**
- **Birth Month Logic**: Hospital background only shows during player's birth month (year 0, birth month)
- **Logic Fix**: Corrected from checking `month_index == 0` to `month_index == birth_month_index` for accurate birth timing
- **Family Wealth Inclusion**: For players under 18, includes parents' wealth in tier calculation
- **Immediate Updates**: Background updates immediately after turn processing to prevent lag
- **Fallback Support**: Uses `constants.COLOR_BG_FALLBACK` when images unavailable

**Integration Points**
- **Main Loop**: Updated in `main.py` after turn processing for immediate state reflection
  - **Explicit Call**: `renderer.background_manager.update(sim_state)` called after `logic.process_turn()`
  - **Purpose**: Prevents one-frame lag in background switching after state changes
- **Renderer Integration**: Called at start of `Renderer.render()` for consistent display
- **Configuration**: Uses `constants.WEALTH_TIERS` for tier thresholds and opacity settings

**Configuration Support**
- **Visual Settings**: `config.json` includes `visuals` section with:
  - `enable_dynamic_backgrounds`: Toggle for background system (default: true)
  - `debug_draw_bounds`: Debug option for boundary visualization (default: false)
- **Constants**: All key values defined in `constants.py`:
  - `UI_OPACITY_PANEL = 230`: Side panel transparency level
  - `UI_OPACITY_CENTER = 200`: Center panel transparency level
  - `WEALTH_TIERS = [10_000, 100_000, 1_000_000, 10_000_000]`: Wealth thresholds
  - `COLOR_BG_FALLBACK = (30, 30, 40)`: Fallback background color
  - `ASSETS_BG_DIR = "assets/backgrounds"`: Background image directory
  - **Screen Settings**: `SCREEN_WIDTH = 2048`, `SCREEN_HEIGHT = 1088`, `FPS = 60`
  - **Layout**: `PANEL_LEFT_WIDTH = 300`, `PANEL_RIGHT_WIDTH = 300`
  - **Social Graph Physics**: Complete physics constants for force simulation
  - **Affinity Engine**: All psychometric compatibility tuning parameters
  - **Health System**: Age-based health capacity and decay constants
  - **Time Management**: `AP_MAX_DAILY = 24.0`, sleep requirements
  - **Medical Costs**: `DOCTOR_VISIT_COST = 100`, recovery ranges
  - **Temperament System**: `TEMPERAMENT_TRAITS`, `PLASTICITY_DECAY` mapping
  - **Cognitive Aptitudes**: `APTITUDES = ["ANA", "VER", "SPA", "MEM_W", "MEM_L", "SEC"]`

</details>

<details>
<summary><strong>Season Mapping Logic</strong></summary>

Deterministic season calculation matching both background and narrative systems:

**Season Definitions**
- **Winter**: Months 11, 0, 1 (December, January, February)
- **Spring**: Months 2, 3, 4 (March, April, May)  
- **Summer**: Months 5, 6, 7 (June, July, August)
- **Autumn**: Months 8, 9, 10 (September, October, November)

**Consistency Features**
- **Narrative Sync**: Birth narrative uses same season logic as background system
- **Deterministic**: Same month always produces same season regardless of year
- **Global Application**: Used by both background selection and story generation
- **Implementation Detail**: Both systems use identical month-to-season mapping in `state.py` and `background.py`

</details>

<details>
<summary><strong>Wealth Tier System</strong></summary>

Five-tier wealth classification for background selection:

**Tier Structure**
- **Tier 1**: < $10,000 (Struggling)
- **Tier 2**: $10,000 - $99,999 (Lower Class)
- **Tier 3**: $100,000 - $999,999 (Middle Class)  
- **Tier 4**: $1,000,000 - $9,999,999 (Upper Class)
- **Tier 5**: $10,000,000+ (Wealthy)

**Calculation Logic**
- **Player Wealth**: Base calculation from player's money
- **Parental Inclusion**: For players under 18, adds both parents' wealth if available
- **Relationship Parsing**: Searches player relationships for "Mother" and "Father" types
- **Threshold Comparison**: Compares total against `constants.WEALTH_TIERS` array

**Visual Impact**
- **Environmental Context**: Higher tiers show more luxurious backgrounds
- **Progressive Feedback**: Visual representation of economic progression
- **Family Context**: Reflects total family economic status, not just player's

</details>

<details>
<summary><strong>Performance & Optimization</strong></summary>

**Caching Strategy**
- **Memory Efficiency**: Images cached after first load to avoid repeated disk access
- **Screen Scaling**: Images pre-scaled to screen resolution during loading
- **Surface Conversion**: Optimized Pygame surfaces for faster rendering

**Update Efficiency**
- **Conditional Updates**: Background only changes when filename differs from current
- **State-Based Logic**: Deterministic selection prevents unnecessary reloads
- **Error Resilience**: Graceful degradation when assets missing

**Integration Performance**
- **Zero Lag**: Explicit updates in main loop prevent one-frame delays
- **Minimal Overhead**: Efficient state checking and filename comparison
- **Resource Management**: Cache clearing capability for memory control

</details>

</details>

<details>
<summary><strong>🖥️ Window Resizing</strong></summary>

The application features a comprehensive window resizing system that provides a professional, responsive user experience:

### Core Features

**Dynamic Window Management**
- **Resizable Window**: Enabled via `pygame.RESIZABLE` flag in display initialization
- **Real-time Resize Events**: Handles `pygame.VIDEORESIZE` events for immediate UI adaptation
- **Layout Recalculation**: Automatic panel positioning updates on window dimension changes
- **Component Rebuilding**: Smart rebuilding of UI elements only when necessary

**Background Scaling System**
- **Aspect Ratio Preservation**: Maintains original image proportions during scaling
- **Cover Mode**: Scales images to fill entire window without letterboxing (no black bars)
- **Centered Positioning**: Images are always centered regardless of aspect ratio differences
- **Smart Cropping**: Automatically crops excess portions while preserving important content
- **Performance Caching**: Dimension-specific image caching for optimal performance

**UI Component Adaptation**
- **Panel Layout**: Three-panel design with fixed side panels (300px) and responsive center panel
- **Button Management**: Automatic clearing and recreation of buttons on resize to prevent duplication
- **Social Graph**: Dynamic rebuilding with new center panel bounds and automatic recentering
- **Log Panel**: Responsive text wrapping and position updates for new dimensions
- **Modal Positioning**: All modals automatically center based on current window size

### Technical Implementation

**Event Handling Flow**
1. `pygame.VIDEORESIZE` event triggers `_handle_resize(w, h)`
2. Updates display mode with new dimensions: `pygame.display.set_mode((w, h), pygame.RESIZABLE)`
3. Calls `_update_layout()` to recalculate all panel positions
4. Sets rebuild flags for components that need regeneration (social graph, UI structure)
5. Components automatically rebuild in next render cycle

**Layout Management**
- **Dynamic Center Panel**: Width/height calculated as `screen_width - left_panel - right_panel`
- **Fixed Side Panels**: Left and right panels maintain 300px width but adjust height
- **Minimum Validation**: Prevents invalid surface creation with dimension bounds checking
- **Smart Rebuilding**: Only rebuilds components when actually needed for performance

**Background Scaling Algorithm**
- **Ratio Calculation**: `scale_ratio = max(width_ratio, height_ratio)` for cover mode
- **Dimension Scaling**: `new_width = original_width * scale_ratio`, `new_height = original_height * scale_ratio`
- **Center Cropping**: Crop from `(new_width-screen_width)//2, (new_height-screen_height)//2`
- **Letterbox Elimination**: No black bars regardless of window proportions

### Performance Optimizations

- **Conditional Rebuilding**: UI elements only rebuild when dimensions actually change
- **Smart Caching**: Background images cached with dimension-specific keys
- **Flag System**: Prevents unnecessary rebuilds with boolean flags
- **Minimal Overhead**: Resize operations are lightweight and non-blocking

</details>

## 🚀 Current Features (MVP 0.1)

<details>
<summary><strong>Core Simulation & Architecture</strong></summary>

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
*   **Formative Years Event System:**
    *   **Monthly Triggers:** Deterministic event checks occur immediately after aging up, pausing the simulation for user input.
    *   **Configurable Content:** Events are fully defined in `config.json`, supporting complex triggers (Age, Month, Stats, Flags).
    *   **Flexible UI:**
        *   **Single Choice:** Standard life scenarios (e.g., "First Words").
        *   **Multi-Choice:** Complex selections like **IGCSE Subject Selection** (Choose 6-8 subjects).
        *   **Infant-Specific Events:** Age-targeted events with temperament effects (e.g., "Strange Noise" for ages 0-2)
    *   **Enhanced Effect System:** 
        *   **Stats Effects:** Traditional modifications to Happiness, Health, etc.
        *   **Temperament Effects:** Age 0-2 events can modify infant temperament traits directly
        *   **Plasticity Scaling:** All temperament effects are multiplied by the agent's current plasticity value (100% → 60% → 30% → 0%)
        *   **Range Clamping:** Temperament values automatically clamped to 0-100 range with decimal precision
        *   **Developmental Impact:** Early choices shape personality formation through the crystallization process
        *   **Logging Integration:** Detailed logging of temperament changes with before/after values
        *   **Example Event:** "Strange Noise" (ages 0-2) offers choices like "Cry loudly" (+Intensity, -Mood) or "Investigate" (+Approach_Withdrawal)
    *   **History Tracking:** Prevents "Once per Lifetime" events from repeating and enables chain events via flags.

</details>

<details>
<summary><strong>Identity & Biology</strong></summary>

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
            *   **Enhanced Calculation System** *(Updated with constants-driven tuning)*:
            *   **Actor Effects**: 
                *   *Neuroticism*: Threshold-based penalty above `AFFINITY_ACTOR_THRESHOLD` (70), scaling at `AFFINITY_ACTOR_WEIGHT` (0.5x).
                *   *Agreeableness*: Threshold-based bonus above `AFFINITY_ACTOR_THRESHOLD`, same weight.
            *   **Dyadic Effects**: 
                *   *Openness*: Shared interests vs. value clashes using `(AFFINITY_DYADIC_THRESHOLD - delta) * AFFINITY_OPENNESS_WEIGHT`.
                *   *Conscientiousness*: Lifestyle sync vs. clashes using `(AFFINITY_DYADIC_THRESHOLD - delta) * AFFINITY_CONSCIENTIOUSNESS_WEIGHT`.
                *   *Extraversion*: Energy match/mismatch using `(AFFINITY_DYADIC_THRESHOLD - delta) * AFFINITY_EXTRAVERSION_WEIGHT`.
            *   **Complete Negative Labeling**: All negative effects now properly labeled in tooltips, including the previously missing "Energy Mismatch" for Extraversion differences.
            *   **Performance-Optimized Paths**: Dual-function architecture with `calculate_affinity()` for bulk initialization (zero allocations) and `get_affinity_breakdown()` for detailed UI tooltips.
            *   **Constants-Driven Tuning**: All thresholds, weights, and bounds moved to `constants.py` for easy balancing without touching core logic.
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
    *   **Hidden:** Sexuality (Hetero/Homo/Bi).
*   **Infant Temperament System:**
    *   **Developmental Psychology:** The simulation implements a scientifically-grounded temperament system for infants (age 0-2) that transitions to the Big 5 personality model at age 3.
    *   **Age-Based Architecture:**
        *   **Infants (0-2 years):** Possess **temperament traits** (9 traits, 0-100 scale) that represent early behavioral tendencies.
        *   **Children (3+ years):** Develop **Big 5 personality** (30 facets, 0-20 scale) that becomes their permanent psychological profile.
        *   **Age 3 Transition:** Temperament crystallizes into Big 5 personality through a sophisticated mapping process.
    *   **Temperament Traits (0-100 Scale):**
        *   **Activity:** General energy level and pace of behavior
        *   **Regularity:** Consistency of biological functions (eating, sleeping)
        *   **Approach_Withdrawal:** Tendency to approach vs. withdraw from new situations
        *   **Adaptability:** Ease of adjusting to environmental changes
        *   **Threshold:** Sensitivity to stimulation (inverse mapping to Neuroticism)
        *   **Intensity:** Strength of emotional responses
        *   **Mood:** General emotional disposition (positive/negative)
        *   **Distractibility:** Ease of attention focus
        *   **Persistence:** Ability to maintain effort despite difficulty
    *   **Genetic Inheritance:**
        *   **Parental Blending:** Infant temperament combines 70% parental Big 5 traits with 30% random variation
        *   **Trait Mapping:** Specific temperament traits map to parental Big 5 traits (e.g., Activity → Extraversion)
        *   **Pure Random:** Infants without parents receive purely random temperament (Gaussian distribution)
        *   **Default Values:** Initial temperament traits start at `TEMPERAMENT_DEFAULT_VALUE` (50.0) before genetic blending
    *   **Plasticity Decay System:**
        *   **Age 0:** 100% plasticity (maximum susceptibility to change)
        *   **Age 1:** 60% plasticity (moderate susceptibility)
        *   **Age 2:** 30% plasticity (low susceptibility)
        *   **Age 3+:** 0% plasticity (personality locked)
    *   **Temperament-to-Personality Crystallization:**
        *   **Comprehensive Mapping System:** Direct conversion from temperament traits to Big 5 facets
        *   **Scale Conversion:** 0-100 temperament → 0-20 facet values
        *   **Inverse Mapping:** Low Threshold → High Neuroticism Vulnerability (Threshold 0-100 → Vulnerability 20-0)
        *   **Specific Trait Mappings:**
            *   **Activity** → Extraversion['Activity'] (Energy level)
            *   **Regularity** → Conscientiousness['Order'] (Organization)
            *   **Mood** → Extraversion['Positive Emotions'] (Emotional disposition)
            *   **Adaptability** → Agreeableness['Compliance'] (Flexibility)
            *   **Threshold** → Neuroticism['Vulnerability'] (Sensitivity, inverse)
            *   **Intensity** → Extraversion['Excitement'] (Emotional strength)
            *   **Persistence** → Conscientiousness['Self-Discipline'] (Effort maintenance)
            *   **Approach_Withdrawal** → Extraversion['Warmth'] (Social approach)
            *   **Distractibility** → Openness['Ideas'] (Attention focus)
        *   **State Transition:** `temperament` → None, `personality` → Big 5 structure, `plasticity` → 0.0
    *   **Event Integration:**
        *   **Infant-Specific Events:** Age 0-2 events can modify temperament traits directly
        *   **Plasticity Scaling:** Event effects are multiplied by current plasticity value
        *   **Range Clamping:** All temperament values remain within 0-100 bounds
    *   **UI Adaptation:**
        *   **Conditional Display:** Attributes modal shows temperament for infants, Big 5 for children
        *   **3×3 Grid:** Infant temperament traits displayed in organized grid layout
        *   **Seamless Transition:** UI automatically switches from temperament to personality at age 3
    *   **Affinity System Integration:**
        *   **Neutral Affinity:** Infants return neutral affinity scores (0) to prevent relationship errors
        *   **Safe Access:** All systems properly handle agents without Big 5 personality
        *   **Developmental Realism:** Infants don't form complex relationships until personality develops
    *   **Enhanced Agent Class Methods:**
        *   **`get_personality_sum()`**: Returns neutral fallback (50) for agents without Big 5 personality instead of 0
        *   **`get_attr_value()`**: Enhanced to retrieve temperament values for infants, with proper trait name matching
        *   **`_generate_infant_temperament()`**: Generates temperament traits with parental blending or pure random
        *   **`crystallize_personality()`**: Converts temperament to Big 5 personality using comprehensive mapping system
        *   **Age-Based Initialization**: Automatically chooses temperament vs. personality based on agent age
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

</details>

<details>
<summary><strong>Economy & Career</strong></summary>

*   **Job Market:**
    *   **Data Structure:** Jobs are defined in `config.json` with a `title` and `salary`.
    *   **Application Logic:** The "Find Job" action picks a random job from the pool. Success is currently guaranteed (requirements removed for IQ refactor).
    *   **Age Restriction:** Agents cannot apply for jobs until **Age 16**.
    *   **Income:** Salaries are distributed monthly (`Salary / 12`) during the `process_turn` phase, simulating realistic cash flow.
    *   **NPC Savings Initialization:** Upon generation, adult NPCs are assigned a starting cash balance calculated as `10% of Salary * Years Worked (Age - 18)`, simulating prior life savings.

</details>

<details>
<summary><strong>Education System</strong></summary>

*   **Comprehensive School Configuration:**
    *   **Detailed Structure:** Configurable forms per year (4 forms: A, B, C, D) with 20 students per form
    *   **Stage-Based Subjects:** Different subject lists for each educational stage:
        *   **Early Years:** Literacy, Numeracy, Creative Play
        *   **Primary:** Math, English, Science, History, Art
        *   **Secondary:** Mathematics, English, Biology, Chemistry, Physics, History, Geography, Art, Music, PE
        *   **Sixth Form:** Empty (filled by IGCSE/IB choices)
    *   **IGCSE Curriculum:** Core subjects (Mathematics, English, Science) and electives (History, Geography, Art, Music, Computer Science, Business Studies, Foreign Language)
    *   **IB Framework:** Six subject groups (Language, Language Acquisition, Individuals & Societies, Sciences, Mathematics, Arts)
*   **School UI Integration:**
    *   **Dedicated School Tab:** New tab in the right panel that only appears when the agent is enrolled in school
    *   **Context-Aware Visibility:** School tab and buttons automatically hide when not enrolled or during summer break
    *   **School Actions:** View Grades, View Classmates, Study Hard, Skip Class (with proper session state checking)
*   **Persistent School Entity:**
    *   **The Royal British College of Lisbon:** The simulation now instantiates a specific school object with defined metadata (Tuition: €18,000, Uniform Policy, Location).
    *   **Hierarchical Structure:** Grades are no longer a flat list but are grouped into logical **Stages** (Early Years, Primary, Secondary, Sixth Form), allowing for future rule differentiation (e.g., Uniforms optional in Sixth Form).
*   **The Cohort System:**
    *   **Form Assignment:** Upon enrollment, agents are assigned to a specific **Form** (e.g., "Year 7**B**").
    *   **Static Groups:** This assignment is persistent. If a player starts in the "B" stream, they remain in the "B" stream until graduation, simulating a stable peer group.
    *   **Structure:** Configured for **4 Forms per Year** (A, B, C, D) with a capacity of **20 students** each.
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

</details>

<details>
<summary><strong>Actions & Progression</strong></summary>

*   **Healthcare (Doctor):**
    *   **Cost:** Flat fee of **$100**.
    *   **Effect:** Restores Health by a random value of **10 to 20** (clamped to the current `max_health`).
    *   **Constraints:** Action fails if `Agent.money < 100`.
*   **Toggle Attributes:**
    *   A UI-only action that pauses the log view to inspect the full list of 15+ agent attributes (Identity, Physical, Personality, Skills).

</details>

<details>
<summary><strong>User Interface & Visualization</strong></summary>

*   **Technical Specs:**
    *   **Resolution**: Fully resizable window with dynamic UI adaptation
    *   **Framerate**: Capped at 60 FPS
    *   **Theme**: Dark Mode with **Transparent UI Panels** allowing dynamic backgrounds to show through
*   **Dynamic Background System:**
    *   **Intelligent Background Selection:** Backgrounds change based on player's age, location, wealth tier, and current season
    *   **Location-Based Logic:** 
        *   **Hospital:** Shows only during birth month (year 0, player's birth month)
        *   **Home:** Default location for all other months
    *   **Wealth Tier System:** 5-tier wealth classification based on total family wealth:
        *   **Tier 1:** < $10,000 (Struggling)
        *   **Tier 2:** $10,000 - $99,999 (Lower Class) 
        *   **Tier 3:** $100,000 - $999,999 (Middle Class)
        *   **Tier 4:** $1,000,000 - $9,999,999 (Upper Class)
        *   **Tier 5:** $10,000,000+ (Wealthy)
    *   **Seasonal Variation:** Backgrounds change with seasons using deterministic month mapping:
        *   **Winter:** December, January, February
        *   **Spring:** March, April, May
        *   **Summer:** June, July, August
        *   **Autumn:** September, October, November
    *   **Resource Management:** Efficient image caching and loading system with fallback support
    *   **Aspect Ratio Preservation**: Cover mode scaling eliminates letterboxing by filling entire window
    *   **Smart Cropping**: Images are centered and cropped to maintain proportions while filling screen
    *   **Narrative Consistency**: Birth narrative season matches background season for immersive experience
    *   **Filename Convention**: `{location}_tier{tier}_{season}.png` (e.g., `hospital_tier2_winter.png`)
*   **Transparent UI System:**
    *   **Alpha-Blended Panels:** All UI panels use transparency to allow background visibility
    *   **Differential Opacity:** Side panels (230 alpha) are less transparent than center panels (200 alpha) for readability
    *   **Consistent Implementation:** Left panel, right panel, center modals, and log panel all use transparency
    *   **Visual Depth:** Maintains border rendering for clear UI separation while allowing background show-through
    *   **Technical Implementation:**
        *   **Helper Method:** `_draw_panel_background(rect, alpha)` creates temporary surfaces with alpha blending
        *   **Surface Creation:** Uses `pygame.Surface()` with `set_alpha()` for transparency control
        *   **Color Scheme:** Dark grey (20, 20, 20) backgrounds for optimal contrast with text
        *   **Border Preservation:** Original border drawing logic maintained for UI clarity
    *   **Component Coverage:**
        *   **Left Panel:** `_draw_left_panel()` uses `UI_OPACITY_PANEL` (230)
        *   **Right Panel:** `_draw_right_panel()` uses `UI_OPACITY_PANEL` (230)
        *   **Center Modals:** Social graph, attributes, family tree use `UI_OPACITY_CENTER` (200)
        *   **Log Panel:** `LogPanel.draw()` uses `UI_OPACITY_CENTER` (200) for transparency
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
                *   **Advanced Physics Engine**: A real-time **Force-Directed Graph** simulation using NumPy with dynamic force scaling.
                *   **Responsive Layout**: Automatically rebuilds and recenters when window is resized
                *   **Dynamic Bounds**: Adapts to new center panel dimensions without user intervention
                    *   **Attraction Scaling:** The spring force between nodes is weighted by relationship strength using tiered multipliers (Weak: 0.5x-2.0x, Moderate: 2.0x-6.0x, Strong: 6.0x-10.0x), causing close-knit families and spouses to snap together into tight clusters.
                    *   **Hostile Repulsion:** Negative relationships (Enemies) act as active repulsors. The engine transforms the spring force into a repulsive force, ensuring that rivals and enemies actively push away from each other on the canvas.
                    *   **Balanced Forces:** Carefully tuned repulsion (50.0) and attraction (2.0) constants ensure relationship-based forces have meaningful impact without overwhelming the physics.
                *   **Advanced Navigation & Interaction:**
                    *   **Zoom Controls:** Mouse wheel zoom in/out (0.7x to 5.0x) centered on the modal, with nodes and edges scaling proportionally. Labels fade out smoothly between 1.5x and 1.3x zoom to reduce clutter at lower magnifications.
                    *   **Infinite Canvas Panning:** Click and drag background to pan around the graph.
                    *   **Physics Interaction:** Users can drag nodes to fling them around the canvas; the physics engine reacts elastically.
                    *   **Precise Hover Detection:** Hover mechanics properly account for zoom level, ensuring accurate node and edge selection at any magnification.
                *   **Network Visualization:**
                    *   **Nodes:** Represent agents. The Player is distinct (White), while NPCs use a continuous color gradient based on relationship score: Light Gray at 0 (neutral/stranger), interpolating to Bright Green at +100 (closest bonds) and Deep Red at -100 (enemies).
                    *   **Edges:** Dynamic lines representing relationships. **Thickness** scales linearly with relationship intensity from 1px (weak) to 4px (strong). **Color** uses linear interpolation between Gray (Neutral), Bright Green (Best Friend), and Deep Red (Nemesis).
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
        *   **Tabbed Navigation:** Actions are organized into switchable categories (**Main**, **School**, **Social**, **Assets**).
        *   **Dynamic Visibility:** Buttons appear/disappear based on context (e.g., "Find Job" hidden <16, "Work Overtime" hidden if unemployed, School tab hidden when not enrolled).
        *   **Auto-Layout:** The interface automatically restacks buttons to fill gaps when items are hidden.
        *   **School Integration:** Dedicated School tab with education-specific actions that only appears during enrollment.
        *   **Social Dashboard:** The Social Tab now features a **Relationship List**.
        *   **Bi-directional Relationship Bars:** UI cards now feature a center-aligned bar.
            *   **Positive:** Fills **Green to the right** (0 to 100).
            *   **Negative:** Fills **Red to the left** (0 to -100).
            *   **Visual Feedback:** This provides immediate visual identification of social standing, distinguishing between a "strained" relationship (short red bar) and a "nemesis" (full red bar).
        *   **Interactive Cards:** Each relationship card includes "Attributes" (to view the NPC's stats), a **Family Tree Icon** (graphical button), and "Interact" buttons.
        *   **Styling:** Buttons feature rounded corners and hover-responsive darkening (RGB 80,80,80). The primary action button is now labeled "Age Up (+1 Month)".

</details>

## 🧠 Cognitive Aptitude System

<details>
<summary><strong>Advanced Cognitive Modeling</strong></summary>

The simulation now features a sophisticated cognitive aptitude system that replaces the simple IQ attribute with a multi-dimensional model of intelligence based on established cognitive psychology research.

### Core Architecture

*   **Six Cognitive Domains:** Each agent has six distinct aptitudes that model different aspects of intelligence:
    *   **ANA (Analytical Reasoning):** Logical deduction, problem-solving, mathematical thinking
    *   **VER (Verbal Abilities):** Language comprehension, vocabulary, verbal fluency
    *   **SPA (Spatial Abilities):** Mental rotation, visualization, spatial reasoning
    *   **MEM_W (Working Memory):** Short-term memory, cognitive capacity, attention
    *   **MEM_L (Long-term Memory):** Knowledge retention, recall, learning
    *   **SEC (Secondary Cognitive):** General cognitive abilities, processing speed

*   **Genotype vs. Phenotype Model:**
    *   **Genotype:** Inherited cognitive potential (0-180 scale)
    *   **Phenotype:** Currently expressed cognitive ability (0-180 scale)
    *   **Plasticity:** Neural adaptability factor for future learning systems

### Developmental Psychology Integration

*   **Fluid vs. Crystallized Intelligence:**
    *   **Fluid Aptitudes** (ANA, SPA, MEM_W): Peak in early adulthood (age 20-30), then decline
    *   **Crystallized Aptitudes** (VER, MEM_L, SEC): Increase slowly throughout life, maintain longer

*   **Age-Based Development Curves:**
    *   **Infancy (0-2):** Very low expression (10-20% of potential)
    *   **Childhood (3-12):** Rapid development, reaching 60-80% of potential
    *   **Adolescence (13-19):** Final maturation, reaching 90-100% of potential
    *   **Adulthood (20-50):** Peak performance with gradual changes
    *   **Maturity (50-90):** Differential decline based on fluid/crystallized nature

### Heritability & Genetics

*   **Lineage Head Generation:** First-generation agents receive random aptitude scores (Gaussian distribution, μ=100, σ=15)
*   **Inheritance Model:** Descendants inherit aptitudes through mid-parent genotype averaging:
    *   Child's genotype = (Father's genotype + Mother's genotype) / 2 + Gaussian variance
    *   Configurable heritability standard deviation (default: 10)
    *   Values clamped to valid range (0-180)

### UI Integration

*   **Cognitive Profile Column:** New 5th column in attributes modal displaying all six aptitudes
*   **Visual Progress Bars:** Color-coded indicators showing current aptitude levels
*   **Age-Appropriate Display:** Values reflect developmental stage of the agent
*   **IQ Integration:** Legacy IQ property calculated as average of all aptitude phenotypes

### Configuration

```json
{
    "aptitudes": {
        "definitions": {
            "ANA": {"mean": 100, "sd": 15},
            "VER": {"mean": 100, "sd": 15},
            "SPA": {"mean": 100, "sd": 15},
            "MEM_W": {"mean": 100, "sd": 15},
            "MEM_L": {"mean": 100, "sd": 15},
            "SEC": {"mean": 100, "sd": 15}
        },
        "heritability_sd": 10,
        "development_curves": {
            "fluid": [[0, 0.2], [10, 0.8], [20, 1.0], [60, 0.9], [90, 0.7]],
            "crystallized": [[0, 0.1], [15, 0.6], [30, 0.9], [50, 1.0], [90, 0.95]]
        },
        "personality_modifiers": {
            "SEC": {"Extraversion": 0.1, "Agreeableness": 0.1}
        }
    }
}
```

</details>

## 🛠️ Development Tools & Settings

<details>
<summary><strong>Development Configuration Options</strong></summary>

The simulation includes development-focused configuration options to facilitate testing and debugging.

### Event System Control

*   **Development Mode:** Configurable setting to disable all events for uninterrupted testing
*   **Usage:** Set `"disable_events": true` in the development section of config.json
*   **Benefits:**
    *   Uninterrupted aging and development testing
    *   Observe cognitive development across different ages
    *   Performance testing without event system overhead
    *   Rapid iteration on features

### Configuration Structure

```json
{
    "development": {
        "disable_events": true  // Set to false to enable events for normal gameplay
    }
}
```

### Debug Logging

*   **Event Disabled Message:** Debug log entry when events are disabled
*   **Normal Operation:** Standard event processing when disabled is false
*   **Non-Intrusive:** Setting doesn't affect other game systems

### Testing Scenarios

*   **Aptitude Development:** Age through multiple years to observe cognitive changes
*   **Performance Testing:** Test game mechanics without event interruptions
*   **Feature Validation:** Verify new systems work without event interference
*   **Quick Iteration:** Rapidly test changes without waiting for event resolutions

</details>

## 🗺️ Roadmap (Planned Features)

The following features are planned to expand the simulation depth into a comprehensive life emulator:

<details>
<summary><strong>Core Mechanics: Dynamic Action Point (AP) System</strong></summary>

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

</details>

<details>
<summary><strong>UX Polish & Advanced UI</strong></summary>

*   **Advanced Visualization:**
    *   **Agent Portrait:** A visual representation in the Left Panel based on appearance stats.
*   **Dynamic Menus:**
    *   **Responsive Design:** Support for true full-screen resizing.

</details>

<details>
<summary><strong>Genetics, Growth & Identity</strong></summary>

*   **Legal Identity & Transition:**
    *   **Name Changes:** Ability to visit the courthouse to legally change First or Last name (e.g., to evade a bad reputation or after marriage).
    *   **Gender Identity:** A dedicated identity tab to socially transition (Transgender/Non-Binary) independent of medical surgery. This affects pronouns in the log and relationship reactions from conservative family members.
*   **Medical Transition Protocol:**
    *   **Hormone Replacement Therapy (HRT):** A recurring medical action required for at least 3 years before Gender Reassignment Surgery becomes unlocked.
    *   **Social Consequences:** While on HRT but pre-surgery, family relationship stats fluctuate based on their "Religiousness" and "Generosity."
*   **Dietary System:**
    *   **Diet Plans:** Selectable lifestyles with monthly costs and stat impacts:
        *   *Vegan/Vegetarian:* Increases Health, slight relationship friction with certain NPCs.
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
*   **Identity Services:**
    *   **Legal Name Change:** Ability to visit the courthouse to change First or Last name (requires fee and no criminal record).
    *   **Gender Identity:** A dedicated identity tab allowing agents to socially transition (pronouns/identity) independent of medical reassignment surgery.
*   **Geopolitical Economy:**
    *   **Socialized Services:** Logic checking the `Country_ID`. If the agent is born in specific countries (e.g., UK, Canada, Norway), "Visit Doctor" and "University" actions are free (tax-funded). In others (USA), they incur high costs.
    *   **Royalty RNG:** In monarchies (Japan, UK, Saudi Arabia, etc.), a tiny RNG chance to be born into the Royal Family, overriding standard parents with Royal NPCs.

</details>

<details>
<summary><strong>Social Web & Relationships</strong></summary>

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

</details>

<details>
<summary><strong>Assets, Economy & Lifestyle</strong></summary>

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

</details>

<details>
<summary><strong>Education, Career & Fame</strong></summary>

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

</details>

<details>
<summary><strong>Activities, Crime & Health</strong></summary>

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
        *   *Examples:* Vegan (High Health), Keto (Weight Loss), Liquid Diet (High Risk), "Hot Cheetos" Diet (Health decay).
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

</details>

<details>
<summary><strong>Legacy & Meta-Game</strong></summary>

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

</details>

<details>
<summary><strong>Psychology, Scenarios & Genetics</strong></summary>

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

</details>

<details>
<summary><strong>Special Careers & Organizations</strong></summary>

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

</details>

<details>
<summary><strong>Interactive Systems & Mini-Games</strong></summary>

*   **Skill-Based Challenges:**
    *   **Burglary:** Maze-based stealth game.
    *   **Prison Escape:** Grid-based puzzle.
    *   **Military Deployment:** Minesweeper logic.
    *   **Intelligence:** IQ/Memory tests.
*   **The "Rat" Collection:** A push-your-luck mini-game for informants trying to record mafia conversations.

</details>

<details>
<summary><strong>⚖️ Design Philosophy & Abstractions</strong></summary>

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
    *   Random chance mechanics are not implemented as the simulation focuses on deterministic realism.
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

</details>

<details>
<summary><strong>🏗️ Key Architectural Decisions & Trade-offs</strong></summary>

These foundational technical decisions shape the simulation's behavior, performance, and development philosophy. Each choice represents a deliberate trade-off between competing priorities.

### 1. Framework Choice: Why Pygame?
*   **Decision:** Use Pygame as the rendering and input framework instead of alternatives like Tkinter, PyQt, or web-based solutions.
*   **Trade-offs:**
    *   **Pros:** 
        *   **Fine-grained Control:** Direct pixel-level rendering enables custom visualizations (family trees, social graphs) that would be difficult in standard widget toolkits.
        *   **Performance:** Hardware-accelerated 2D rendering handles complex UI elements and animations smoothly.
        *   **Simplicity:** Minimal dependencies (just Pygame + NumPy) reduces installation complexity.
        *   **Event Model:** Immediate, low-latency input handling suitable for interactive simulations.
    *   **Cons:**
        *   **Manual Layout:** No automatic widget positioning or responsive layouts - everything must be manually positioned.
        *   **No Native Widgets:** Must implement all UI components (buttons, scrollbars, tooltips) from scratch.
        *   **Desktop-Only:** Cannot run in browsers without additional layers like Pygbag.
*   **Rationale:** Pygame strikes the optimal balance between control and simplicity for a research-focused simulation. The need for custom visualizations (force-directed social graphs, layered family trees) outweighs the convenience of pre-built widgets.

### 2. Time Granularity: Why Monthly Ticks?
*   **Decision:** Advance simulation time in 1-month increments rather than daily, hourly, or real-time progression.
*   **Trade-offs:**
    *   **Pros:**
        *   **Meaningful Decisions:** Each month represents a significant life chapter (school progress, career changes, relationship evolution).
        *   **Performance:** Fewer simulation ticks = faster computation, especially with large NPC populations.
        *   **Data Management:** Monthly intervals align with real-world reporting periods (salaries, academic grades, biological milestones).
        *   **Player Agency:** Turn-based approach allows thoughtful decision-making rather than reactive gameplay.
    *   **Cons:**
        *   **Temporal Resolution:** Cannot model short-term events (daily routines, weekly schedules, emergency responses).
        *   **Realism Loss:** Some life processes (illness progression, job hunting) happen on shorter timescales in reality.
        *   **Action Density:** Multiple activities must be abstracted into monthly outcomes rather than individual events.
*   **Rationale:** Monthly ticks provide the sweet spot between meaningful progression and computational efficiency. The Action Point (AP) system simulates daily time allocation within each monthly turn, preserving short-term decision-making while maintaining long-term pacing.

### 3. Simulation Model: Why Deterministic with Seeded RNG?
*   **Decision:** Use a deterministic simulation model where identical seeds + actions produce identical outcomes, rather than fully stochastic or purely procedural systems.
*   **Trade-offs:**
    *   **Pros:**
        *   **Reproducibility:** Critical for debugging, testing, and scientific analysis. Bugs can be reliably reproduced and verified.
        *   **Shareability:** Players can share seeds to experience identical life scenarios, enabling community comparison.
        *   **Testing:** Automated tests can verify specific life outcomes given known inputs and seeds.
        *   **Analysis:** Researchers can study the impact of single variables while holding all else constant.
    *   **Cons:**
        *   **Predictability:** Knowledge of the seed reduces surprise and discovery for repeat players.
        *   **Limited Emergence:** True randomness can create unexpected emergent behaviors that deterministic systems cannot.
        *   **Implementation Complexity:** Requires careful state management and consistent RNG usage across all modules.
*   **Rationale:** Determinism enables Life-Sim to function as both a game and a research tool. The stochastic elements (personality-based RNG, random events) provide variety within a reproducible framework. Player choices remain the primary source of divergence, not random chance.

### 4. Architecture: Monolithic vs. Microservices
*   **Decision:** Use a single-process monolithic architecture instead of distributed microservices or multi-process designs.
*   **Trade-offs:**
    *   **Pros:**
        *   **Simplicity:** No network communication, service discovery, or distributed state management.
        *   **Performance:** Direct function calls with no serialization or network overhead.
        *   **Debugging:** Single process enables straightforward debugging and profiling.
        *   **Deployment:** Single executable file with minimal runtime dependencies.
    *   **Cons:**
        *   **Scalability:** Limited to single-core performance (though NumPy provides some parallelization).
        *   **Modularity:** Larger codebase in a single process requires stricter discipline to maintain separation of concerns.
        *   **Fault Isolation:** A crash in any module brings down the entire simulation.
*   **Rationale:** For a single-player life simulation, the complexity of distributed systems outweighs any benefits. The simulation's computational needs fit comfortably within modern single-threaded performance, and the Action Point system naturally provides opportunities for future parallelization if needed.

### 5. Data Model: In-Memory vs. Persistent State
*   **Decision:** Keep the entire simulation state in memory during runtime with periodic save points, rather than database-driven persistence.
*   **Trade-offs:**
    *   **Pros:**
        *   **Speed:** Direct memory access is orders of magnitude faster than database queries.
        *   **Simplicity:** No ORM, migrations, or query optimization to manage.
        *   **Consistency:** All state changes happen in a single transaction (the monthly turn).
        *   **Flexibility:** Complex object graphs (relationships, family trees) are easier to navigate in memory.
    *   **Cons:**
        *   **Memory Usage:** Large populations consume significant RAM.
        *   **Durability:** Crashes can lose unsaved progress.
        *   **Scalability:** Limited to what fits in available memory.
*   **Rationale:** Life simulations require constant access to interconnected relationship data and agent states. The performance benefits of in-memory access outweigh the persistence advantages of databases for this use case. The monthly turn structure provides natural save points.

</details>

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

### Development Mode

For testing and development, you can disable events to allow uninterrupted aging and feature testing:

1.  **Open `config.json`**
2.  **Set development mode:**
    ```json
    {
        "development": {
            "disable_events": true
        }
    }
    ```
3.  **Run simulation** - Events will be disabled, allowing continuous aging without interruptions

**Note:** The current configuration has events disabled for development. Set `"disable_events": false` to enable normal gameplay with events.

**Benefits:**
- Test aptitude development across different ages
- Performance testing without event overhead
- Rapid feature iteration without event interruptions

<details>
<summary><strong>📋 Development Rules & Standards</strong></summary>

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

</details>

## 📊 Profiling & Performance Optimization

### Overview
Performance optimization in Life-Sim is driven by profiling data, not assumptions. This section covers profiling tools, performance analysis, and optimization strategies.

<details>
<summary><strong>Profiling Tools & Methodology</strong></summary>

#### 1. Built-in Profiling Framework
The simulation includes comprehensive profiling capabilities:

- **Real-time Profiler**: Live FPS monitoring and function timing display
- **cProfile Integration**: Detailed function call analysis
- **Performance Metrics**: Frame-by-frame timing data collection

#### 2. Profiling Workflow
1. **Baseline Measurement**: Profile before making changes
2. **Hot Path Identification**: Find top 2-3 time-consuming functions
3. **Targeted Optimization**: Focus on high-impact areas
4. **Validation**: Verify improvements with before/after comparisons

</details>

<details>
<summary><strong>Social Graph Standalone Profiler</strong></summary>

#### Overview
The `social_graph_standalone.py` script demonstrates advanced profiling techniques with real-time performance monitoring.

#### Features

**Real-time Performance Display:**
- Live FPS counter with color-coded performance indicators
- Function-level timing breakdown (milliseconds per call)
- Percentage load distribution across functions
- Node and edge count tracking

**Profiling Capabilities:**
- Decorator-based function profiling
- cProfile integration for deep analysis
- Statistical reporting (min/max/average timing)
- Frame-by-frame performance logging

**Performance Insights:**
- **Drawing Operations**: Typically 35-40% of frame time
- **Physics Calculations**: 30-40% of frame time  
- **Event Handling**: <20% of frame time
- **Agent Creation**: One-time cost, scales with agent count

#### Usage
```bash
# Run with default 10 agents
python social_graph_standalone.py

# Easy configuration - just change one line:
NUM_AGENTS = 25  # Scale from 5-50 agents
```

#### Controls
- **Mouse Wheel**: Zoom in/out
- **Left Click + Drag**: Pan view or drag nodes
- **P Key**: Toggle real-time profiler
- **Space**: Reset view
- **R**: Rebuild graph
- **ESC**: Exit

#### Key Performance Optimizations

**1. NumPy Vectorization:**
```python
# Repulsion — pairwise forces over all nodes (vectorized)
diff = self.pos[:, np.newaxis, :] - self.pos[np.newaxis, :, :]
forces = diff * force_mag[:, :, np.newaxis]
total_force = np.sum(forces, axis=1)

# Attraction — fully vectorized over all edges using cached index arrays.
# Piecewise factor (Weak/Moderate/Strong tiers) computed via boolean masks;
# forces scattered back to nodes with np.add.at (no Python loop).
delta = self.pos[self._edge_u] - self.pos[self._edge_v]
dist  = np.linalg.norm(delta, axis=1)
# ... piecewise factor via boolean masks ...
np.add.at(total_force, v_idx,  force)
np.add.at(total_force, u_idx, -force)
```

**2. Efficient Data Structures:**
- NumPy arrays for position/velocity vectors
- Pre-allocated workspace arrays for edge-visibility culling (`_edge_vis_u_pos`, `_edge_vis_min`, etc.) reused every frame via `np.take(..., out=)` and `np.minimum(..., out=)`
- Cached edge-endpoint lists (`_edge_u_list`, `_edge_v_list`) and radii array (`_radii_arr`) built once in `build()`, eliminating per-frame list-to-array conversion and tuple unpacking
- Pre-allocated label `Rect` objects (`_label_rects`) mutated in-place each frame instead of `get_rect()` allocations
- Spatial indexing for collision detection

**3. Rendering Optimizations:**
- Single-pass drawing using pre-rendered node surfaces (blit replaces per-frame `draw.circle`)
- Vectorized viewport culling: NumPy boolean masks over all nodes and edges, with pre-allocated workspace arrays reused via `out=` parameters (zero per-frame allocation)
- Python-side hot-loop optimization: all NumPy arrays converted to plain lists via `.tolist()` before iteration; all attribute lookups bound to locals (eliminates `LOAD_ATTR` overhead per iteration)
- Zoom-gated caches: scaled edge widths and label `Rect` objects pre-computed on zoom change, mutated in-place each frame

#### Profiling Output Example
```
REAL-TIME PROFILER
FPS: 60.3
Nodes: 18, Edges: 61
SocialGraph.draw: 0.6ms (35.2%)     ← Green/Yellow/Red
SocialGraph.update_physics: 0.7ms (41.1%)
SocialGraph.handle_event: 0.3ms (17.6%)
create_fully_connected_agents: 3.1ms (6.1%)
```

</details>

<details>
<summary><strong>Performance Guidelines</strong></summary>

#### Core Loop Optimization
1. **Profile First**: Always measure before optimizing
2. **Vectorize Operations**: Use NumPy for batch calculations
3. **Minimize Python Loops**: Avoid per-element iteration in hot paths
4. **Pre-allocate Memory**: Avoid dynamic allocation in loops
5. **Cache Calculations**: Store expensive computations

#### Scaling Strategies
- **Spatial Partitioning**: For large agent counts (>100)
- **Level of Detail**: Reduce detail for distant elements
- **Async Operations**: Offload non-critical calculations
- **Memory Pooling**: Reuse objects to reduce GC pressure

#### Monitoring & Metrics
- **FPS Targets**: 60 FPS for smooth interaction
- **Frame Budget**: Allocate time per system (physics: 33%, rendering: 50%, other: 17%)
- **Memory Usage**: Monitor for leaks and excessive allocation
- **Function Call Counts**: Identify unexpected call frequency

</details>

## 🎨 Credits & Assets

*   **Icons:**
    *   Family Tree icon by [Delapouite](https://delapouite.com/) under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) via [Game-Icons.net](https://game-icons.net/1x1/delapouite/family-tree.html#download).