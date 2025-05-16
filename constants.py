# rally_racer_project/constants.py
# This file contains all the global constant values for the Rally Racer game.

import pygame # Might be needed if any constants use pygame types directly (e.g. pygame.Color)

# --- Screen Dimensions ---
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DIRT_COLOR = (139, 69, 19) # This can now be the 'track' color over grass or for other details
DARK_DIRT_COLOR = (101, 67, 33) # For track details or worn grass
LIGHT_DIRT_COLOR = (188, 143, 143) # Not used in current main, but kept for completeness
MUD_COLOR = (92, 64, 51)
DARK_MUD_COLOR = (70, 50, 40)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200) # Not used in current main
GREEN = (0, 255, 0) # General green, also for next checkpoint indicator
BLUE = (0, 0, 255) # General blue, AI car colors will be more specific
CHECKPOINT_COLOR = (255, 100, 0)
START_FINISH_MARKER_COLOR = (200, 200, 0)
START_FINISH_LINE_COLOR = WHITE
NEXT_CHECKPOINT_INDICATOR_COLOR = GREEN
DUST_COLOR = (160, 120, 90, 100) # RGBA for alpha
MUD_SPLASH_COLOR = (70, 50, 40, 150) # RGBA for alpha
CAR_BODY_COLOR = (200, 0, 0) # Player car color
AI_CAR_BODY_COLOR = (0, 0, 200) # Default/fallback AI car color
CAR_WINDOW_COLOR = (100, 100, 200)
TIRE_COLOR = (40, 40, 40)
SPOILER_COLOR = (60, 60, 60)
SHADOW_COLOR = (0, 0, 0, 80) # RGBA for semi-transparent shadow
RAMP_DEBUG_COLOR = (0, 255, 255, 100) # RGBA for debug
RPM_BAR_COLOR = (0, 200, 0)
RPM_BAR_HIGH_COLOR = (255, 150, 0)
RPM_BAR_MAX_COLOR = (255, 0, 0)
PEDAL_BG_COLOR = (50, 50, 50)
ACCEL_PEDAL_COLOR = (0, 180, 0)
BRAKE_PEDAL_COLOR = (200, 0, 0)
HANDBRAKE_INDICATOR_COLOR = YELLOW
MAP_BG_COLOR = (50, 50, 50, 180) # RGBA for semi-transparent map background
MAP_BORDER_COLOR = (200, 200, 200)
MAP_CAR_COLOR = RED # Player car on map

BUTTON_COLOR = (100, 100, 100)
BUTTON_HOVER_COLOR = (150, 150, 150)
BUTTON_TEXT_COLOR = WHITE

RAMP_COLOR = (160, 160, 170)  # A light metallic gray for the ramp surface
RAMP_BORDER_COLOR = (100, 100, 110) # A darker gray for the border/edges

# NEW COLORS (from previous update)
GRASS_COLOR = (34, 139, 34) # A forest green for the base surface
LIGHT_GRASS_COLOR = (50, 155, 50) # For subtle patterning/texture on grass
HILL_COLOR_NO_GRASS = (139, 119, 101) # A brownish, rocky color for bare hills (visual only)
DARK_HILL_COLOR = (100, 80, 70) # For hill details or borders (visual only)




# List of distinct colors for AI cars
AI_AVAILABLE_COLORS = [
    (0, 150, 255),   # Sky Blue
    (255, 100, 100), # Light Red
    (100, 220, 100), # Light Green
    (255, 180, 0),   # Orange
    (170, 100, 255), # Lavender
    (230, 230, 80),  # Pale Yellow
    (80, 200, 200),  # Teal
    (255, 150, 180), # Pink
    (160, 160, 160), # Medium Gray
    (100, 100, 150)  # Dark Slate Blue
]

# --- Base Car Physics Constants ---
# INCREASED for quicker driving
BASE_MAX_CAR_SPEED = 450.0 # Original: 350.0
BASE_ENGINE_POWER = 200.0  # Original: 150.0
BASE_BRAKE_POWER = 180.0   # Original: 150.0
BASE_FRICTION = 0.93       # Original: 0.92 (higher means less friction)
BASE_DRIFT_FRICTION_MULTIPLIER = 0.95 # Original: 0.94
BASE_HANDBRAKE_FRICTION_MULTIPLIER = 0.89 # Original: 0.88
BASE_HANDBRAKE_SIDE_GRIP_LOSS = 0.88 # Original: 0.90

# --- Car Properties ---
CAR_TURN_RATE = 160.0 # Original: 150.0
MIN_TURN_EFFECTIVENESS = 0.4
MUD_DRAG_MULTIPLIER = 2.8 # Original: 3.0 (how much mud increases drag (friction exponent))
DRIFT_THRESHOLD_ANGLE = 30 # Original: 35 (Degrees difference between heading and velocity to start drift)
MAX_RPM = 7500 # Original: 7000
IDLE_RPM = 850 # Original: 800

# --- Jump Physics ---
AIRBORNE_FRICTION_MULTIPLIER = 0.995 # Original: 0.99 (Very low air resistance)
AIRBORNE_TURN_EFFECTIVENESS = 0.08 # Original: 0.05 (Minimal steering in air)
MIN_JUMP_SPEED_FACTOR = 0.25 # Original: 0.3 (Car speed as factor of max_speed to trigger jump)
# INCREASED for larger jumps
BASE_AIRBORNE_DURATION = 0.50  # Original: 0.25 Seconds
MAX_AIRBORNE_DURATION = 1.2    # Original: 0.5   Seconds
SHADOW_OFFSET_X = 8            # Original: 5
SHADOW_OFFSET_Y = 8            # Original: 5
AIRBORNE_SHADOW_SCALE = 0.5    # Original: 0.6 (Shadow scales down more in air)

# --- Base AI Properties (used for "Medium" and "Random" difficulties) ---
BASE_AI_LOOKAHEAD_FACTOR = 1.5
BASE_AI_TURN_THRESHOLD = 20
BASE_AI_BRAKE_FACTOR = 0.8
BASE_AI_STEER_SHARPNESS = 0.8
BASE_AI_THROTTLE_CONTROL = 0.95
BASE_AI_MUD_REACTION = 0.5

# --- AI Randomness ---
AI_RANDOM_STD_DEV_FACTOR = 0.25

# --- Track / World Properties ---
NUM_MUD_PATCHES = 40 # Original: 50
MIN_MUD_SIZE = 70
MAX_MUD_SIZE = 250
MIN_MUD_VERTICES = 5
MAX_MUD_VERTICES = 10
MUD_RADIUS_VARIATION = 0.4
WORLD_BOUNDS = 4000
MIN_OBJ_SEPARATION = 200 # Original: 250 (Minimum distance between generated objects)

# --- Ramp Properties ---
# INCREASED for more frequent jumps
NUM_RAMPS = 35 # Original: 20
RAMP_WIDTH = 50 # Original: 40
RAMP_HEIGHT = 20 # Original: 15 (This is the 'depth' of the ramp, not jump height)

# --- Particle Properties ---
# Dust
MAX_DUST_PARTICLES = 150
DUST_SPAWN_INTERVAL = 0.03
DUST_LIFETIME = 0.8
DUST_START_SIZE = 5
DUST_END_SIZE = 1
# Mud Splash
MAX_MUD_PARTICLES = 80
MUD_SPAWN_INTERVAL = 0.02
MUD_LIFETIME = 0.6
MUD_START_SIZE = 6
MUD_END_SIZE = 2
MUD_SPAWN_SPEED_THRESHOLD = 50.0

# --- Map Properties ---
MAP_WIDTH = 250
MAP_HEIGHT = 250
MAP_MARGIN = 15
MAP_WORLD_SCALE_X = MAP_WIDTH / (2 * WORLD_BOUNDS) # Scale factor from world to map
MAP_WORLD_SCALE_Y = MAP_HEIGHT / (2 * WORLD_BOUNDS)
MAP_MUD_MARKER_RADIUS = 3
MAP_CHECKPOINT_MARKER_RADIUS = 4
MAP_CAR_MARKER_SIZE = 6 # For the triangular car marker on map

# --- Button Properties ---
SETUP_BUTTON_WIDTH = 200
SETUP_BUTTON_HEIGHT = 50
LAP_BUTTON_SIZE = 40 # Not currently used, but kept
OPTION_BUTTON_WIDTH = 50
OPTION_BUTTON_HEIGHT = 40

# --- UI Properties (Layout for Setup Screen & In-Game HUD) ---
ROW_SPACING = 55
OPTION_Y_START = SCREEN_HEIGHT * 0.18
OPTION_LABEL_X = CENTER_X - 350
OPTION_VALUE_X = CENTER_X - 50
OPTION_MINUS_X = CENTER_X + 150
OPTION_PLUS_X = CENTER_X + 220
RPM_GAUGE_WIDTH = 200; RPM_GAUGE_HEIGHT = 25
ACCEL_PEDAL_WIDTH = 40; ACCEL_PEDAL_HEIGHT = 60
BRAKE_PEDAL_WIDTH = 40; BRAKE_PEDAL_HEIGHT = 60
HANDBRAKE_INDICATOR_POS_X_OFFSET = 340
HANDBRAKE_INDICATOR_POS_Y_OFFSET = SCREEN_HEIGHT - 80
HANDBRAKE_INDICATOR_RADIUS = 12

# --- Course Properties ---
DEFAULT_RACE_LAPS = 3
START_FINISH_LINE = [(-200, -300), (-200, 300)] # World coordinates
START_FINISH_WIDTH = 15 # Visual width on screen
CHECKPOINT_RADIUS = 20 # Collision radius for hitting a checkpoint
CHECKPOINT_ROUNDING_RADIUS = 75 # Radius for AI to consider a checkpoint "rounded"
LINE_CROSSING_DEBOUNCE = 1.0 # Seconds to wait before detecting another line cross

# --- Sound Properties ---
SAMPLE_RATE = 44100
ENGINE_BASE_FREQ = 50 # Original: 60 (Lowered for potentially beefier sound with higher RPM)
SKID_DURATION_MS = 150
BEEP_DURATION_MS = 150
BEEP_FREQ_HIGH = 880
BEEP_FREQ_LOW = 660
ENGINE_MIN_VOL = 0.1
ENGINE_MAX_VOL = 0.8
SKID_VOL = 0.6

# --- Debugging ---
DEBUG_DRAW_RAMPS = False

# --- Game Setup Options (Defaults/Ranges) ---
DEFAULT_TOP_SPEED_INDEX = 2
DEFAULT_GRIP_INDEX = 2
DEFAULT_NUM_CHECKPOINTS = 3
MAX_CHECKPOINTS_ALLOWED = 10
DEFAULT_NUM_AI = 3
MAX_AI_OPPONENTS = 5 # Should ideally not exceed len(AI_AVAILABLE_COLORS)
DEFAULT_DIFFICULTY_INDEX = 1



# --- Hill Generation (Visual Only for now, will become physical) ---
NUM_VISUAL_HILLS = 15       # Number of visual hill patches to generate
MIN_HILL_SIZE = 150         # Min diameter of a hill patch (was 200)
MAX_HILL_SIZE = 500         # Max diameter of a hill patch (was 600)
# MIN_HILL_VERTICES = 5     # No longer needed for circular hills
# MAX_HILL_VERTICES = 10    # No longer needed for circular hills
# HILL_RADIUS_VARIATION = 0.5 # No longer needed for circular hills

HILL_CREST_RADIUS_FACTOR = 0.3 # NEW: For "over the top" jump logic (e.g., crest is 30% of hill radius)


