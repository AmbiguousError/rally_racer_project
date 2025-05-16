# rally_racer_project/constants.py
# This file contains all the global constant values for the Rally Racer game.

import pygame

# --- Screen Dimensions ---
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# --- Updated Pastel Color Palette (Directly assigned to original names where applicable) ---

# Core UI & General
WHITE = (250, 250, 250)                     # Slightly off-white
BLACK = (40, 40, 45)                        # Very dark grey for text, borders
GRAY = (160, 165, 170)                      # Medium pastel grey
LIGHT_GRAY = (200, 205, 210)                # Lighter pastel grey

# Environment & Track Elements
GRASS_COLOR = (140, 190, 140)               # Main grass surface (New constant for clarity)
LIGHT_GRASS_COLOR = (170, 210, 170)         # Texture lines on grass (New constant)
DIRT_COLOR = (180, 150, 120)                # General dirt/off-road patches (Pastel Value)
DARK_DIRT_COLOR = (150, 120, 90)            # Darker dirt (Pastel Value)
MUD_COLOR = (130, 110, 100)                 # Pastel mud
DARK_MUD_COLOR = (100, 85, 75)              # Pastel mud border
HILL_COLOR_NO_GRASS = (170, 150, 130)       # Pastel rocky hill color (New constant)
DARK_HILL_COLOR = (140, 120, 100)           # Pastel rocky hill border (New constant)
ROAD_COLOR = (150, 155, 160)                # Pastel asphalt/road (New constant)
ROAD_BORDER_COLOR = (120, 125, 130)         # Pastel road border (New constant)
RAMP_COLOR = (190, 195, 200)                # Pastel ramp (light grey/off-white)
RAMP_BORDER_COLOR = (150, 155, 160)         # Pastel ramp border
CHECKPOINT_COLOR = (255, 170, 100)          # Pastel checkpoint (soft orange)
START_FINISH_MARKER_COLOR = (240, 240, 150) # Pastel S/F gate (pale yellow)
START_FINISH_LINE_COLOR = WHITE             # Keep S/F line high contrast (using new WHITE)
NEXT_CHECKPOINT_INDICATOR_COLOR = (120, 220, 120) # Softer vibrant green

# Cars & Effects
CAR_BODY_COLOR = (255, 130, 130)            # Player car (Pastel Salmon Red)
AI_CAR_BODY_COLOR = (176, 196, 222)         # Fallback AI color if list is exhausted (Pastel Grey Blue)
CAR_WINDOW_COLOR = (170, 190, 220)          # Pastel car windows
TIRE_COLOR = (80, 85, 90)                   # Dark Grey for tires
SPOILER_COLOR = (130, 135, 140)             # Medium Grey for spoiler
SHADOW_COLOR = (40, 40, 45, 80)             # Dark grey shadow (RGBA)
DUST_COLOR = (190, 170, 150, 100)           # Pastel dust particles (RGBA)
MUD_SPLASH_COLOR = (110, 90, 80, 150)       # Pastel mud splash particles (RGBA)
TIRE_TRACK_COLOR = (140, 110, 90, 100)      # Pastel tire track (RGBA, softer brown) (New Constant)

AI_AVAILABLE_COLORS = [ # New pastel list for AI cars
    (173, 216, 230), # Light Blue
    (255, 192, 203), # Pink
    (221, 160, 221), # Plum (Pastel Purple)
    (152, 251, 152), # Pale Green / Mint
    (255, 218, 185), # Peach / Navajo White
    (255, 250, 170), # Pale Yellow
    (175, 225, 225), # Pastel Teal / Pale Turquoise
    (210, 180, 140), # Tan / Soft Beige
    (238, 221, 130), # Soft Gold
    (205, 170, 170)  # Dusty Rose
]

# UI Specific Elements
RPM_BAR_COLOR = (130, 210, 130)             # Low RPM (Pastel Green)
RPM_BAR_HIGH_COLOR = (255, 200, 100)        # Mid RPM (Pastel Orange/Yellow)
RPM_BAR_MAX_COLOR = (255, 130, 130)         # High RPM (Pastel Red/Salmon)
PEDAL_BG_COLOR = (100, 105, 110)            # BG for pedal indicators
ACCEL_PEDAL_COLOR = (120, 200, 120)         # Accelerator fill
BRAKE_PEDAL_COLOR = (240, 110, 110)         # Brake fill
HANDBRAKE_INDICATOR_COLOR = (255, 250, 160) # Handbrake active (Pastel Pale Yellow)
MAP_BG_COLOR = (100, 105, 110, 180)         # Map background (RGBA)
MAP_BORDER_COLOR = (170, 175, 180)          # Map border
MAP_CAR_COLOR = CAR_BODY_COLOR              # Player car on map uses new player car color

BUTTON_COLOR = (160, 170, 180)              # UI Buttons
BUTTON_HOVER_COLOR = (190, 200, 210)        # UI Button Hover
BUTTON_TEXT_COLOR = BLACK                   # Text on buttons (using new dark grey/black for contrast)

# Debug Colors
RAMP_DEBUG_COLOR = (0, 220, 220, 100)       # Cyanish, for ramp debug (can keep vibrant)

# --- Base Car Physics Constants ---
BASE_MAX_CAR_SPEED = 450.0 
BASE_ENGINE_POWER = 200.0  
BASE_BRAKE_POWER = 180.0   
BASE_FRICTION = 0.93       
BASE_DRIFT_FRICTION_MULTIPLIER = 0.95 
BASE_HANDBRAKE_FRICTION_MULTIPLIER = 0.89 
BASE_HANDBRAKE_SIDE_GRIP_LOSS = 0.88 

CAR_TURN_RATE = 160.0 
MIN_TURN_EFFECTIVENESS = 0.4
MUD_DRAG_MULTIPLIER = 2.8 # Exponent for how mud affects base friction calculation
DRIFT_THRESHOLD_ANGLE = 30 
MAX_RPM = 7500 
IDLE_RPM = 850 

AIRBORNE_FRICTION_MULTIPLIER = 0.995 
AIRBORNE_TURN_EFFECTIVENESS = 0.08 
MIN_JUMP_SPEED_FACTOR = 0.25 
BASE_AIRBORNE_DURATION = 0.50  
MAX_AIRBORNE_DURATION = 1.2    
SHADOW_OFFSET_X = 8            
SHADOW_OFFSET_Y = 8            
AIRBORNE_SHADOW_SCALE = 0.5    

BASE_AI_LOOKAHEAD_FACTOR = 1.5
BASE_AI_TURN_THRESHOLD = 20
BASE_AI_BRAKE_FACTOR = 0.8
BASE_AI_STEER_SHARPNESS = 0.8
BASE_AI_THROTTLE_CONTROL = 0.95
BASE_AI_MUD_REACTION = 0.5
AI_RANDOM_STD_DEV_FACTOR = 0.25

# --- Track / World Properties ---
NUM_MUD_PATCHES = 40 
MIN_MUD_SIZE = 70
MAX_MUD_SIZE = 250
MIN_MUD_VERTICES = 5 
MAX_MUD_VERTICES = 10
MUD_RADIUS_VARIATION = 0.4 
WORLD_BOUNDS = 4000
MIN_OBJ_SEPARATION = 200 

# --- Ramp Properties (Updated for Circular Ramps) ---
NUM_RAMPS = 30 
RAMP_MIN_RADIUS = 30
RAMP_MAX_RADIUS = 50
# RAMP_WIDTH, RAMP_HEIGHT are obsolete

# --- Particle Properties ---
MAX_DUST_PARTICLES = 150
DUST_SPAWN_INTERVAL = 0.03; DUST_LIFETIME = 0.8
DUST_START_SIZE = 5; DUST_END_SIZE = 1
MAX_MUD_PARTICLES = 80
MUD_SPAWN_INTERVAL = 0.02; MUD_LIFETIME = 0.6
MUD_START_SIZE = 6; MUD_END_SIZE = 2
MUD_SPAWN_SPEED_THRESHOLD = 50.0

# --- Map Properties ---
MAP_WIDTH = 250; MAP_HEIGHT = 250; MAP_MARGIN = 15
MAP_WORLD_SCALE_X = MAP_WIDTH / (2 * WORLD_BOUNDS)
MAP_WORLD_SCALE_Y = MAP_HEIGHT / (2 * WORLD_BOUNDS)
MAP_MUD_MARKER_RADIUS = 3; MAP_CHECKPOINT_MARKER_RADIUS = 4; MAP_CAR_MARKER_SIZE = 6

# --- UI Properties (Layout for Setup Screen & In-Game HUD) ---
SETUP_BUTTON_WIDTH = 200; SETUP_BUTTON_HEIGHT = 50
OPTION_BUTTON_WIDTH = 50; OPTION_BUTTON_HEIGHT = 40
ROW_SPACING = 55; OPTION_Y_START = SCREEN_HEIGHT * 0.18
OPTION_LABEL_X = CENTER_X - 350; OPTION_VALUE_X = CENTER_X - 50
OPTION_MINUS_X = CENTER_X + 150; OPTION_PLUS_X = CENTER_X + 220
RPM_GAUGE_WIDTH = 200; RPM_GAUGE_HEIGHT = 25
ACCEL_PEDAL_WIDTH = 40; ACCEL_PEDAL_HEIGHT = 60
BRAKE_PEDAL_WIDTH = 40; BRAKE_PEDAL_HEIGHT = 60
HANDBRAKE_INDICATOR_POS_X_OFFSET = 340 
HANDBRAKE_INDICATOR_POS_Y_OFFSET = SCREEN_HEIGHT - 80 
HANDBRAKE_INDICATOR_RADIUS = 12

# --- Course Properties ---
DEFAULT_RACE_LAPS = 3
START_FINISH_LINE = [(-200, -300), (-200, 300)]
START_FINISH_WIDTH = 15
CHECKPOINT_RADIUS = 20
CHECKPOINT_ROUNDING_RADIUS = 75
LINE_CROSSING_DEBOUNCE = 1.0

# --- Sound Properties ---
SAMPLE_RATE = 44100; ENGINE_BASE_FREQ = 50 
SKID_DURATION_MS = 150; BEEP_DURATION_MS = 150
BEEP_FREQ_HIGH = 880; BEEP_FREQ_LOW = 660
ENGINE_MIN_VOL = 0.1; ENGINE_MAX_VOL = 0.8; SKID_VOL = 0.6

# --- Debugging ---
DEBUG_DRAW_RAMPS = False

# --- Game Setup Options (Defaults/Ranges) ---
DEFAULT_TOP_SPEED_INDEX = 2
DEFAULT_GRIP_INDEX = 2
DEFAULT_NUM_CHECKPOINTS = 3
MAX_CHECKPOINTS_ALLOWED = 10
DEFAULT_NUM_AI = 3
MAX_AI_OPPONENTS = 5 
DEFAULT_DIFFICULTY_INDEX = 1

# --- Hill Generation (Visual Only for now, will become physical) ---
NUM_VISUAL_HILLS = 15 
MIN_HILL_SIZE = 150   # Diameter
MAX_HILL_SIZE = 500   # Diameter
HILL_CREST_RADIUS_FACTOR = 0.3 

# --- Tire Track Constants ---
TIRE_TRACK_RADIUS = 4                
TIRE_TRACK_MIN_SPEED = 30            
TIRE_TRACK_OFFSET_REAR = 15          
TIRE_TRACK_OFFSET_SIDE = 9           
# TIRE_TRACK_COLOR is defined in the main pastel palette section

# --- Road Properties ---
ROAD_WIDTH = 100  
ROAD_BORDER_WIDTH = 0 # Set to 0 to remove road border
# ROAD_COLOR & ROAD_BORDER_COLOR are defined in the main pastel palette section

# --- Roundabout Properties ---
CREATE_ROUNDABOUTS = True       
ROUNDABOUT_CENTERLINE_RADIUS = 120 
ROUNDABOUT_DETAIL_SEGMENTS = 16   

# --- Surface Physics Modifiers ---
ROAD_FRICTION_MULTIPLIER = 1.15  # Road is grippy
GRASS_FRICTION_MULTIPLIER = 0.75 # Was 0.85 - Less grip on grass
GRASS_SPEED_DAMPENING = 0.95   # Was 0.98 - More speed loss on grass
MUD_FRICTION_MULTIPLIER = 0.6  # Was 0.7 - Even less grip in mud
MUD_SPEED_DAMPENING = 0.85     # Was 0.90 - Significant speed loss in mud