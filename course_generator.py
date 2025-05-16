# rally_racer_project/course_generator.py
# This file contains functions for generating the race course elements like checkpoints,
# mud patches, ramps, and visual hills.

import random
import math
import pygame # For pygame.Rect if used in VisualHill internal calculations

# Assuming constants.py and utils.py are in the parent directory or project root is in PYTHONPATH
# If running main.py from the project root, these imports should work.
import constants as const
from utils import distance_sq # For checking distances between objects

# Assuming Checkpoint, MudPatch, and Ramp classes are in classes.track_elements
# If using classes/__init__.py to expose them:
from classes import Checkpoint, MudPatch, Ramp
# Or directly:
# from classes.track_elements import Checkpoint, MudPatch, Ramp


def is_too_close(new_pos, existing_objects, min_dist_sq):
    """
    Helper function to check if a new position is too close to any existing objects.
    Each object in existing_objects is expected to have world_x and world_y attributes.
    """
    for obj in existing_objects:
        # getattr is used to safely access attributes, defaulting if not present
        # (though they should be for objects like Checkpoint, MudPatch, Ramp, VisualHill)
        obj_pos = (getattr(obj, 'world_x', new_pos[0]), getattr(obj, 'world_y', new_pos[1]))
        if distance_sq(new_pos, obj_pos) < min_dist_sq:
            return True
    return False

# --- NEW: VisualHill Class ---
# --- VisualHill Class (Updated) ---
# rally_racer_project/course_generator.py
# ... (imports and other functions like is_too_close, generate_random_checkpoints etc.)

# --- VisualHill Class (Updated for Circular Shape) ---
class VisualHill:
    """
    Represents a physical hill patch on the track, now circular.
    """
    def __init__(self, world_x, world_y, diameter): # Size is now diameter
        self.world_x = world_x
        self.world_y = world_y
        self.diameter = diameter
        self.radius = diameter / 2.0
        self.color = const.HILL_COLOR_NO_GRASS
        self.border_color = const.DARK_HILL_COLOR

        # For "over the top" jump mechanic (Phase 2)
        self.crest_radius = self.radius * const.HILL_CREST_RADIUS_FACTOR

        # Bounding rectangle for culling or broad-phase collision
        self.rect = pygame.Rect(
            self.world_x - self.radius,
            self.world_y - self.radius,
            self.diameter,
            self.diameter
        )

    # _generate_random_points is no longer needed

    # _calculate_bounding_rect is implicitly handled by self.rect in __init__

    def draw(self, surface, camera_offset_x, camera_offset_y):
        """
        Draws the circular hill on the given surface, relative to the camera.
        """
        screen_x = int(self.world_x - camera_offset_x + const.CENTER_X)
        screen_y = int(self.world_y - camera_offset_y + const.CENTER_Y)
        screen_radius = int(self.radius) # Assuming no world-to-screen scaling for radius here for simplicity

        # Basic culling: check if the bounding box of the hill is on screen
        screen_rect_approx = self.rect.move(
            -camera_offset_x + const.CENTER_X,
            -camera_offset_y + const.CENTER_Y
        )
        # Further culling: if circle itself is off-screen
        if not (-screen_radius < screen_x < const.SCREEN_WIDTH + screen_radius and \
                -screen_radius < screen_y < const.SCREEN_HEIGHT + screen_radius):
            if not screen_rect_approx.colliderect(surface.get_rect()): # Double check with rect for edge cases
                 return # Hill is off-screen

        pygame.draw.circle(surface, self.color, (screen_x, screen_y), screen_radius)
        pygame.draw.circle(surface, self.border_color, (screen_x, screen_y), screen_radius, 2) # Border

    def check_collision(self, car_world_rect):
        """
        Checks for collision between the car's world rectangle and the hill's bounding rectangle.
        This is a broad-phase check.
        """
        return self.rect.colliderect(car_world_rect)

    def check_crest_collision(self, car_center_x, car_center_y):
        """
        Checks if the car's center is within the hill's crest radius.
        Used for the "over the top" jump mechanic.
        Returns True if car center is inside the crest.
        """
        dist_sq_to_center = distance_sq((car_center_x, car_center_y), (self.world_x, self.world_y))
        return dist_sq_to_center < (self.crest_radius ** 2)

# generate_random_hills function would remain mostly the same,
# but when it creates VisualHill, it passes 'size' which is now treated as diameter.
# The spacing logic using 'half_size' would correctly use 'size / 2.0'.

# def generate_random_hills(count, existing_objects, start_finish_line_coords, course_checkpoint_coords_list):
#     ...
#     # Inside the loop:
#     size = random.uniform(const.MIN_HILL_SIZE, const.MAX_HILL_SIZE) # This is diameter
#     # ... positioning logic ...
#     hills.append(VisualHill(wx, wy, size)) # Pass diameter
#     ...
# The existing generate_random_hills should work fine with this change in VisualHill's constructor.

    # <<< NEW METHOD >>>
    def check_collision(self, car_world_rect):
        """
        Checks for collision between the car's world rectangle and the hill's bounding rectangle.
        """
        return self.rect.colliderect(car_world_rect)


def generate_random_checkpoints(count, existing_objects_for_spacing, start_finish_line_coords):
    """
    Generates a list of random Checkpoint coordinates, ensuring they are reasonably spaced.
    """
    checkpoint_coords = []
    # Checkpoints should be well spread out from each other and from the S/F line.
    min_dist_sq_cp = (const.MIN_OBJ_SEPARATION * 2.5)**2 # Increased separation for checkpoints
    attempts = 0
    max_attempts = count * 75 # Allow more attempts for sparse placement
    margin_factor = 0.90 # Keep checkpoints within 90% of world bounds

    # Define a region around the start/finish line to avoid placing checkpoints
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer_x = 500 # Horizontal buffer from S/F line for checkpoints
    sf_avoid_buffer_y = 300 # Vertical buffer from S/F line for checkpoints

    while len(checkpoint_coords) < count and attempts < max_attempts:
        attempts += 1
        wx = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        wy = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        pos = (wx, wy)

        # Avoid placing too close to the start/finish line (using a larger buffer for CPs)
        if abs(wx - sf_line_x) < sf_avoid_buffer_x and \
           (sf_line_y_min - sf_avoid_buffer_y) < wy < (sf_line_y_max + sf_avoid_buffer_y):
            continue

        # Check against existing_objects_for_spacing (e.g., start/finish gates passed from main)
        # and already placed checkpoints in this generation run.
        # Create temporary Checkpoint objects for is_too_close compatibility.
        temp_checkpoint_objects = [Checkpoint(c_x, c_y, -1) for c_x,c_y in checkpoint_coords]
        all_to_check_spacing = existing_objects_for_spacing + temp_checkpoint_objects

        if is_too_close(pos, all_to_check_spacing, min_dist_sq_cp):
            continue
        
        checkpoint_coords.append(pos)

    if attempts >= max_attempts and len(checkpoint_coords) < count:
        print(f"Warning: CourseGen - Could only generate {len(checkpoint_coords)}/{count} checkpoints due to spacing constraints.")
    
    # Fallback if no checkpoints generated (e.g., count is 1 and first attempt fails)
    while len(checkpoint_coords) < min(count, 1) and count > 0 : # Ensure at least one if count > 0
        # Try placing one further out if initial attempts fail
        wx = random.uniform(const.WORLD_BOUNDS*0.3, const.WORLD_BOUNDS*0.7) 
        wy = random.uniform(-const.WORLD_BOUNDS*0.5, const.WORLD_BOUNDS*0.5)
        pos = (wx,wy)
        temp_checkpoint_objects = [Checkpoint(c_x, c_y, -1) for c_x,c_y in checkpoint_coords]
        if not is_too_close(pos, temp_checkpoint_objects, min_dist_sq_cp): # Check against only itself if it's the first
            checkpoint_coords.append(pos)
        else: # Absolute fallback if even that fails
            checkpoint_coords.append((const.WORLD_BOUNDS*0.5, 0)) # Place one at a fixed spot
            break # Avoid infinite loop

    return checkpoint_coords


def generate_random_mud_patches(count, existing_objects, start_finish_line_coords, course_checkpoint_coords_list):
    """
    Generates a list of MudPatch objects.
    """
    mud_patches = []
    attempts = 0
    max_attempts = count * 30 # Allow more attempts for mud patches

    # Define a region around the start/finish line to avoid for mud
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer_mud = 150 # Buffer around S/F line for mud

    while len(mud_patches) < count and attempts < max_attempts:
        attempts += 1
        size = random.randint(const.MIN_MUD_SIZE, const.MAX_MUD_SIZE)
        half_size = size / 2.0 # Approximate radius for spacing

        # Try to place mud patches somewhat away from the direct center, but can be anywhere
        angle = random.uniform(0, 2 * math.pi)
        # Allow placement closer to center than checkpoints, but also further out
        dist_from_center = random.uniform(const.WORLD_BOUNDS * 0.05, const.WORLD_BOUNDS * 0.95)
        
        wx = dist_from_center * math.cos(angle)
        wy = dist_from_center * math.sin(angle)
        pos = (wx, wy)

        # Avoid start/finish line
        if abs(wx - sf_line_x) < (half_size + sf_avoid_buffer_mud) and \
           (sf_line_y_min - half_size - sf_avoid_buffer_mud) < wy < (sf_line_y_max + half_size + sf_avoid_buffer_mud):
            continue

        # Avoid placing directly on course checkpoints
        too_close_to_course_cp = False
        for cp_x, cp_y in course_checkpoint_coords_list:
            # Check against a larger radius around checkpoints for mud
            if distance_sq(pos, (cp_x, cp_y)) < (half_size + const.CHECKPOINT_RADIUS + const.MIN_OBJ_SEPARATION * 0.4)**2:
                too_close_to_course_cp = True
                break
        if too_close_to_course_cp:
            continue
        
        # Check against other existing objects (which includes start/finish gates and other mud patches)
        # Spacing for mud patches can be a bit tighter than checkpoints
        # Each mud patch has its own size, so use that for spacing calculation
        min_dist_sq_this_mud = (half_size + const.MIN_MUD_SIZE / 2 + const.MIN_OBJ_SEPARATION * 0.2)**2
        if is_too_close(pos, existing_objects + mud_patches, min_dist_sq_this_mud): # Check against already placed mud patches too
            continue
            
        mud_patches.append(MudPatch(wx, wy, size))

    if attempts >= max_attempts and len(mud_patches) < count:
        print(f"Warning: CourseGen - Could only generate {len(mud_patches)}/{count} mud patches.")
    return mud_patches


def generate_random_ramps(count, existing_objects, start_finish_line_coords):
    """
    Generates a list of Ramp objects.
    """
    ramps = []
    min_dist_sq_ramp = (const.MIN_OBJ_SEPARATION * 0.8)**2 # Ramps can be closer than CPs
    attempts = 0
    max_attempts = count * 35

    sf_line_x = start_finish_line_coords[0][0]
    sf_line_center_y = (start_finish_line_coords[0][1] + start_finish_line_coords[1][1]) / 2
    # Avoid placing ramps right on the start/finish line (using a radius)
    sf_avoid_radius_sq = (const.MIN_OBJ_SEPARATION * 1.2)**2 # Larger buffer for S/F line

    while len(ramps) < count and attempts < max_attempts:
        attempts += 1
        margin = 0.90 # Keep ramps generally within bounds
        wx = random.uniform(-const.WORLD_BOUNDS * margin, const.WORLD_BOUNDS * margin)
        wy = random.uniform(-const.WORLD_BOUNDS * margin, const.WORLD_BOUNDS * margin)
        pos = (wx, wy)
        angle_deg = random.uniform(0, 360) # Random orientation for the ramp

        # Avoid start/finish line (using distance to center of S/F line)
        if distance_sq(pos, (sf_line_x, sf_line_center_y)) < sf_avoid_radius_sq:
            continue
            
        # Check against all other objects (checkpoints, mud, other ramps)
        # For ramps, the 'existing_objects' list in is_too_close will include previously placed ramps.
        if is_too_close(pos, existing_objects + ramps, min_dist_sq_ramp): # Check against already placed ramps
            continue
            
        ramps.append(Ramp(wx, wy, const.RAMP_WIDTH, const.RAMP_HEIGHT, angle_deg))

    if attempts >= max_attempts and len(ramps) < count:
        print(f"Warning: CourseGen - Could only generate {len(ramps)}/{count} ramps.")
    return ramps

# --- NEW: Function to generate VisualHill objects ---
def generate_random_hills(count, existing_objects, start_finish_line_coords, course_checkpoint_coords_list):
    """
    Generates a list of VisualHill objects, ensuring they are reasonably spaced.
    They should avoid being too close to the start/finish line and critical checkpoints.
    """
    hills = []
    attempts = 0
    max_attempts = count * 40 # Max attempts to place all hills

    # Avoid placing hills too close to the start/finish line area
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer_hill = 100 # Buffer around S/F line for hills

    while len(hills) < count and attempts < max_attempts:
        attempts += 1
        # Determine random size for the hill
        size = random.uniform(const.MIN_HILL_SIZE, const.MAX_HILL_SIZE)
        half_size = size / 2.0 # Approximate radius for spacing checks

        # Determine random position for the hill
        margin_factor = 0.95 # Allow hills to be near world edges
        wx = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        wy = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        pos = (wx, wy)

        # 1. Avoid start/finish line
        if abs(wx - sf_line_x) < (half_size + sf_avoid_buffer_hill) and \
           (sf_line_y_min - half_size - sf_avoid_buffer_hill) < wy < (sf_line_y_max + half_size + sf_avoid_buffer_hill):
            continue

        # 2. Avoid placing directly on or too close to critical course checkpoints
        #    Hills are visual, so they shouldn't obscure checkpoints.
        too_close_to_course_cp = False
        for cp_x, cp_y in course_checkpoint_coords_list:
            # Check against a buffer around checkpoints for hills
            # Make this buffer slightly larger than the checkpoint itself plus hill's half_size
            if distance_sq(pos, (cp_x, cp_y)) < (half_size + const.CHECKPOINT_RADIUS + const.MIN_OBJ_SEPARATION * 0.3)**2:
                too_close_to_course_cp = True
                break
        if too_close_to_course_cp:
            continue

        # 3. Check spacing against all other existing_objects (checkpoints, mud, ramps)
        #    and also against already generated hills in this run.
        #    Hills are visual, so their minimum separation can be smaller.
        #    The min_dist_sq for hills should consider their own size.
        #    A simple approach: ensure center of new hill is at least half_size + half_size_of_other_obj away.
        #    is_too_close expects a single min_dist_sq, so we use a general one.
        #    A more specific min_dist_sq_hill for spacing between hills themselves:
        min_dist_sq_hill_to_hill = (half_size + const.MIN_HILL_SIZE / 2.0 + 20)**2 # 20 is a small buffer

        # Check against other hills
        if is_too_close(pos, hills, min_dist_sq_hill_to_hill):
            continue
        
        # Check against other physical objects (checkpoints, mud, ramps)
        # Use a general object separation for these, but adjusted because hills are visual.
        min_dist_sq_hill_to_other = (half_size + const.MIN_OBJ_SEPARATION * 0.3)**2
        if is_too_close(pos, existing_objects, min_dist_sq_hill_to_other):
            continue
            
        hills.append(VisualHill(wx, wy, size))

    if attempts >= max_attempts and len(hills) < count:
        print(f"Warning: CourseGen - Could only generate {len(hills)}/{count} visual hills due to spacing constraints.")
    
    return hills