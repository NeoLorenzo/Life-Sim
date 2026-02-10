# life_sim/constants.py
"""
Application Constants.
Static values that do not change between simulation runs.
"""

# Window Settings
SCREEN_WIDTH = 2048
SCREEN_HEIGHT = 1088
WINDOW_TITLE = "Life-Sim MVP 0.7"
FPS = 60

# Layout Dimensions
PANEL_LEFT_WIDTH = 250  # Reduced from 300 to make space for vertical AP bar
PANEL_RIGHT_WIDTH = 300
AP_BAR_WIDTH = 30  # Width for vertical AP bar between panels
AP_BAR_HEIGHT_PERCENTAGE = 0.6  # AP bar height as 60% of screen height
# Center panel takes the remaining width

# Colors (R, G, B)
COLOR_BG = (20, 20, 20)           # Main Window Background
COLOR_PANEL_BG = (40, 40, 40)     # Side Panels
COLOR_LOG_BG = (10, 10, 10)       # Center Log Background
COLOR_BORDER = (60, 60, 60)       # Panel Borders

COLOR_TEXT = (220, 220, 220)
COLOR_TEXT_DIM = (150, 150, 150)
COLOR_ACCENT = (100, 200, 100)
COLOR_DEATH = (200, 50, 50)

COLOR_LOG_POSITIVE = (100, 255, 100)
COLOR_LOG_NEGATIVE = (255, 100, 100)
COLOR_LOG_HEADER = (100, 200, 255)

COLOR_BTN_IDLE = (60, 60, 60)
COLOR_BTN_HOVER = (80, 80, 80)
COLOR_BTN_CLICK = (100, 100, 100)
COLOR_BG_FALLBACK = (30, 30, 40)

# UI Settings
FONT_SIZE_MAIN = 20
FONT_SIZE_HEADER = 24
FONT_SIZE_LOG = 18
LOG_LINE_HEIGHT = 24
LOG_PADDING_TOP = 20  # Padding from top of panel to first log entry
UI_OPACITY_PANEL = 230
UI_OPACITY_CENTER = 200

# Wealth Tiers
WEALTH_TIERS = [10_000, 100_000, 1_000_000, 10_000_000]

# Time Settings
START_YEAR = 2025
MONTHS = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]

# File Paths
LOG_DIR = "logs"
CONFIG_FILE = "config.json"
ASSETS_DIR = "assets"
ICON_FT_FILENAME = "icon_ft.png"
ASSETS_BG_DIR = "assets/backgrounds"

# Social Graph Physics
GRAPH_REPULSION = 500.0  # Strength of nodes pushing apart
GRAPH_CENTER_GRAVITY = 0.90 # Pull towards screen center
GRAPH_FRICTION = 0.91     # Velocity damping (0.0 - 1.0)
GRAPH_SPEED = 1.0         # Global speed multiplier
GRAPH_ATTRACTION = 2.0    # Spring strength for connected nodes

# Social Graph Relationship Force Multipliers
GRAPH_WEAK_BOND_THRESHOLD = 30    # Relationship score for weak bonds
GRAPH_MODERATE_BOND_THRESHOLD = 70 # Relationship score for moderate bonds
GRAPH_WEAK_ATTRACTION_MIN = 0.5   # Minimum attraction multiplier for weak bonds
GRAPH_WEAK_ATTRACTION_MAX = 2.0   # Maximum attraction multiplier for weak bonds
GRAPH_MODERATE_ATTRACTION_MIN = 2.0 # Minimum attraction multiplier for moderate bonds
GRAPH_MODERATE_ATTRACTION_MAX = 6.0 # Maximum attraction multiplier for moderate bonds
GRAPH_STRONG_ATTRACTION_MIN = 6.0  # Minimum attraction multiplier for strong bonds
GRAPH_STRONG_ATTRACTION_MAX = 10.0 # Maximum attraction multiplier for strong bonds
GRAPH_NEGATIVE_REPULSION_MAX = 2.0 # Maximum repulsion multiplier for negative relationships
GRAPH_MIN_DISTANCE = 0.1          # Minimum distance for force calculations
GRAPH_TIME_STEP = 0.01            # Physics time step
GRAPH_BOUNDARY_PADDING = 10        # Padding from screen edges

# Relationship Settings
RELATIONSHIP_MIN = -100
RELATIONSHIP_MAX = 100

# Relationship Colors
COLOR_REL_ENEMY = (220, 20, 20)     # Deep Red
COLOR_REL_DISLIKE = (200, 100, 50)  # Orange
COLOR_REL_NEUTRAL = (150, 150, 150) # Gray
COLOR_REL_FRIEND = (100, 200, 100)  # Green
COLOR_REL_BEST = (50, 255, 50)      # Bright Green

# ---------------------------------------------------------------------------
# Affinity Engine — Psychometric Compatibility Tuning
# ---------------------------------------------------------------------------
# Actor-effect threshold: personality sum above this triggers a score modifier.
# 70 chosen because Big Five facets score 0-20 each across 6 facets (max 120);
# 70 represents ~58% of max, the point at which a trait is reliably dominant
# rather than merely average.
AFFINITY_ACTOR_THRESHOLD      = 70

# Actor-effect weight: score change per point above the threshold.
# 0.5 keeps individual personality from overwhelming dyadic compatibility;
# at max trait sum (120) the bonus/penalty is ±25, leaving room for pair effects.
AFFINITY_ACTOR_WEIGHT         = 0.5

# Dyadic similarity threshold: max trait-sum delta that still produces a bonus.
# 20 points (~17% of the 0-120 range) is the window of "close enough" similarity
# before the effect flips from attraction to repulsion.
AFFINITY_DYADIC_THRESHOLD     = 20

# Dyadic weights per trait — higher weight = more influence on final score.
# Openness and Conscientiousness govern core values and daily-life compatibility,
# so they are weighted equally and higher than Extraversion, which governs social
# energy style — a real friction source but not a dealbreaker.
AFFINITY_OPENNESS_WEIGHT      = 0.8
AFFINITY_CONSCIENTIOUSNESS_WEIGHT = 0.8
AFFINITY_EXTRAVERSION_WEIGHT  = 0.5

# Minimum absolute effect magnitude to warrant a breakdown label in the UI.
# Below this the contribution is noise; surfacing it would clutter tooltips.
AFFINITY_LABEL_THRESHOLD      = 5

# Hard clamp bounds — documented invariant: scores are strictly [-100, +100].
AFFINITY_SCORE_MIN            = -100
AFFINITY_SCORE_MAX            = 100

# Affinity Weights (Psychometrics)
AFFINITY_WEIGHT_ACTOR_N = 1.0   # Neuroticism penalty (Actor)
AFFINITY_WEIGHT_ACTOR_A = 1.0   # Agreeableness bonus (Actor)
AFFINITY_WEIGHT_DYADIC_O = 0.5  # Openness difference penalty (Dyadic)
AFFINITY_WEIGHT_DYADIC_C = 0.5  # Conscientiousness difference penalty (Dyadic)

# Health Constants
HEALTH_CHILDHOOD_MAX_AGE = 20   # Age when childhood growth ends
HEALTH_PRIME_MAX_AGE = 50       # Age when prime period ends
HEALTH_BASE_CHILD = 70          # Base health for children
HEALTH_GROWTH_RATE = 1.5        # Health growth per year in childhood
HEALTH_PRIME_VALUE = 100        # Health value during prime years
HEALTH_SENESCENCE_DIVISOR = 25  # Divisor for senescence decay calculation

# Time Management
AP_MAX_DAILY = 24.0             # Maximum action points per day
AP_SLEEP_DEFAULT = 8.0           # Default sleep hours required
AP_GRANULARITY = 0.5             # Action point granularity for scheduling
MIN_SLEEP_PERMITTED = 4.0        # Minimum sleep hours allowed

# School Time (Realistic age-based 5-day week)
# Different age groups have different daily school hours
# Values represent average daily time including weekends
SCHOOL_HOURS_EARLY_YEARS = 3.0    # Ages 3-4: Nursery/Reception (half-days)
SCHOOL_HOURS_PRIMARY = 4.5        # Ages 5-10: Primary school
SCHOOL_HOURS_SECONDARY = 6.0      # Ages 11-16: Secondary school  
SCHOOL_HOURS_SIXTH_FORM = 6.5     # Ages 17-18: Sixth form/IB

# Default fallback (was original 5.0)
SCHOOL_HOURS_DAILY = 5.0         
SCHOOL_HOURS_SESSION = 7.0       # Actual hours per school day (for calculations)

# Medical Costs
DOCTOR_VISIT_COST = 100         # Cost to visit doctor
DOCTOR_RECOVERY_MIN = 10        # Minimum health recovery from doctor
DOCTOR_RECOVERY_MAX = 20        # Maximum health recovery from doctor

# Reproduction Ages
MOTHER_YOUNG_AGE = 20           # Age threshold for "young mother" description

# ---------------------------------------------------------------------------
# Physical Attributes System
# ---------------------------------------------------------------------------
COORDINATION_ATTRIBUTES = ["agility", "balance", "coordination", "reaction_time"]
PERFORMANCE_ATTRIBUTES = ["flexibility", "speed", "power"]

# ---------------------------------------------------------------------------
# Temperament System
# ---------------------------------------------------------------------------
TEMPERAMENT_TRAITS = ["Activity", "Regularity", "Approach_Withdrawal", "Adaptability", 
                      "Threshold", "Intensity", "Mood", "Distractibility", "Persistence"]

PLASTICITY_DECAY = {0: 1.0, 1: 0.6, 2: 0.3}

TEMPERAMENT_DEFAULT_VALUE = 50.0

# ---------------------------------------------------------------------------
# Cognitive Aptitude System
# ---------------------------------------------------------------------------
APTITUDES = ["Analytical Reasoning", "Verbal Abilities", "Spatial Abilities", "Working Memory", "Long-term Memory", "Secondary Cognitive"]
APTITUDE_MIN = 0
APTITUDE_MAX = 180