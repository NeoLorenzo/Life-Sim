# life_sim/constants.py
"""
Application Constants.
Static values that do not change between simulation runs.
"""

# Window Settings
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
WINDOW_TITLE = "Life-Sim MVP 0.5"
FPS = 60

# Layout Dimensions
PANEL_LEFT_WIDTH = 300
PANEL_RIGHT_WIDTH = 300
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

# UI Settings
FONT_SIZE_MAIN = 20
FONT_SIZE_HEADER = 24
FONT_SIZE_LOG = 18
LOG_LINE_HEIGHT = 24

# Time Settings
START_YEAR = 2025
MONTHS = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]

# File Paths
LOG_DIR = "logs"
CONFIG_FILE = "config.json"
ASSETS_DIR = "assets"
ICON_FT_FILENAME = "icon_ft.png"

# Social Graph Physics
GRAPH_REPULSION = 10000.0  # Strength of nodes pushing apart
GRAPH_CENTER_GRAVITY = 0.90 # Pull towards screen center
GRAPH_FRICTION = 0.91     # Velocity damping (0.0 - 1.0)
GRAPH_SPEED = 1.0         # Global speed multiplier
GRAPH_ATTRACTION = 0.01   # Spring strength for connected nodes

# Relationship Settings
RELATIONSHIP_MIN = -100
RELATIONSHIP_MAX = 100

# Relationship Colors
COLOR_REL_ENEMY = (220, 20, 20)     # Deep Red
COLOR_REL_DISLIKE = (200, 100, 50)  # Orange
COLOR_REL_NEUTRAL = (150, 150, 150) # Gray
COLOR_REL_FRIEND = (100, 200, 100)  # Green
COLOR_REL_BEST = (50, 255, 50)      # Bright Green

# Affinity Weights (Psychometrics)
AFFINITY_WEIGHT_ACTOR_N = 0.5   # Neuroticism penalty (Actor)
AFFINITY_WEIGHT_ACTOR_A = 0.5   # Agreeableness bonus (Actor)
AFFINITY_WEIGHT_DYADIC_O = 0.25 # Openness difference penalty (Dyadic)
AFFINITY_WEIGHT_DYADIC_C = 0.25 # Conscientiousness difference penalty (Dyadic)