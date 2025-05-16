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
        obj_pos = (getattr(obj, 'world_x', new_pos[0]), getattr(obj, 'world_y', new_pos[1]))
        if distance_sq(new_pos, obj_pos) < min_dist_sq:
            return True
    return False

# --- VisualHill Class (as defined previously) ---
class VisualHill:
    """
    Represents a physical hill patch on the track, now circular.
    """
    def __init__(self, world_x, world_y, diameter):
        self.world_x = world_x
        self.world_y = world_y
        self.diameter = diameter
        self.radius = diameter / 2.0
        self.color = const.HILL_COLOR_NO_GRASS
        self.border_color = const.DARK_HILL_COLOR
        self.crest_radius = self.radius * const.HILL_CREST_RADIUS_FACTOR
        self.rect = pygame.Rect(
            self.world_x - self.radius,
            self.world_y - self.radius,
            self.diameter,
            self.diameter
        )
    def draw(self, surface, camera_offset_x, camera_offset_y):
        screen_x = int(self.world_x - camera_offset_x + const.CENTER_X)
        screen_y = int(self.world_y - camera_offset_y + const.CENTER_Y)
        screen_radius = int(self.radius) 
        if not (-screen_radius < screen_x < const.SCREEN_WIDTH + screen_radius and \
                -screen_radius < screen_y < const.SCREEN_HEIGHT + screen_radius):
            screen_rect_approx = self.rect.move(
                -camera_offset_x + const.CENTER_X,
                -camera_offset_y + const.CENTER_Y
            )
            if not screen_rect_approx.colliderect(surface.get_rect()):
                 return 
        if screen_radius < 1: return
        pygame.draw.circle(surface, self.color, (screen_x, screen_y), screen_radius)
        pygame.draw.circle(surface, self.border_color, (screen_x, screen_y), screen_radius, 2)
    def check_collision(self, car_world_rect):
        return self.rect.colliderect(car_world_rect)
    def check_crest_collision(self, car_center_x, car_center_y):
        dist_sq_to_center = distance_sq((car_center_x, car_center_y), (self.world_x, self.world_y))
        return dist_sq_to_center < (self.crest_radius ** 2)


def generate_random_checkpoints(count, existing_objects_for_spacing, start_finish_line_coords):
    checkpoint_coords = []
    min_dist_sq_cp = (const.MIN_OBJ_SEPARATION * 2.5)**2
    attempts = 0
    max_attempts = count * 75 
    margin_factor = 0.90
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer_x = 500 
    sf_avoid_buffer_y = 300 
    while len(checkpoint_coords) < count and attempts < max_attempts:
        attempts += 1
        wx = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        wy = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        pos = (wx, wy)
        if abs(wx - sf_line_x) < sf_avoid_buffer_x and \
           (sf_line_y_min - sf_avoid_buffer_y) < wy < (sf_line_y_max + sf_avoid_buffer_y):
            continue
        temp_checkpoint_objects = [Checkpoint(c_x, c_y, -1) for c_x,c_y in checkpoint_coords]
        all_to_check_spacing = existing_objects_for_spacing + temp_checkpoint_objects
        if is_too_close(pos, all_to_check_spacing, min_dist_sq_cp):
            continue
        checkpoint_coords.append(pos)
    if attempts >= max_attempts and len(checkpoint_coords) < count:
        print(f"Warning: CourseGen - Could only generate {len(checkpoint_coords)}/{count} checkpoints due to spacing constraints.")
    while len(checkpoint_coords) < min(count, 1) and count > 0 :
        wx = random.uniform(const.WORLD_BOUNDS*0.3, const.WORLD_BOUNDS*0.7) 
        wy = random.uniform(-const.WORLD_BOUNDS*0.5, const.WORLD_BOUNDS*0.5)
        pos = (wx,wy)
        temp_checkpoint_objects = [Checkpoint(c_x, c_y, -1) for c_x,c_y in checkpoint_coords]
        if not is_too_close(pos, temp_checkpoint_objects, min_dist_sq_cp):
            checkpoint_coords.append(pos)
        else: 
            checkpoint_coords.append((const.WORLD_BOUNDS*0.5, 0))
            break 
    return checkpoint_coords

def generate_random_mud_patches(count, existing_objects, start_finish_line_coords, course_checkpoint_coords_list):
    mud_patches = []
    attempts = 0
    max_attempts = count * 30
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer_mud = 150 
    while len(mud_patches) < count and attempts < max_attempts:
        attempts += 1
        size = random.randint(const.MIN_MUD_SIZE, const.MAX_MUD_SIZE)
        half_size = size / 2.0
        angle = random.uniform(0, 2 * math.pi)
        dist_from_center = random.uniform(const.WORLD_BOUNDS * 0.05, const.WORLD_BOUNDS * 0.95)
        wx = dist_from_center * math.cos(angle)
        wy = dist_from_center * math.sin(angle)
        pos = (wx, wy)
        if abs(wx - sf_line_x) < (half_size + sf_avoid_buffer_mud) and \
           (sf_line_y_min - half_size - sf_avoid_buffer_mud) < wy < (sf_line_y_max + half_size + sf_avoid_buffer_mud):
            continue
        too_close_to_course_cp = False
        for cp_x, cp_y in course_checkpoint_coords_list:
            if distance_sq(pos, (cp_x, cp_y)) < (half_size + const.CHECKPOINT_RADIUS + const.MIN_OBJ_SEPARATION * 0.4)**2:
                too_close_to_course_cp = True
                break
        if too_close_to_course_cp:
            continue
        min_dist_sq_this_mud = (half_size + const.MIN_MUD_SIZE / 2 + const.MIN_OBJ_SEPARATION * 0.2)**2
        if is_too_close(pos, existing_objects + mud_patches, min_dist_sq_this_mud):
            continue
        mud_patches.append(MudPatch(wx, wy, size))
    if attempts >= max_attempts and len(mud_patches) < count:
        print(f"Warning: CourseGen - Could only generate {len(mud_patches)}/{count} mud patches.")
    return mud_patches

# --- UPDATED: generate_random_ramps Function ---
def generate_random_ramps(count, existing_objects, start_finish_line_coords):
    """
    Generates a list of circular Ramp objects.
    """
    ramps = []
    # Spacing for ramp centers. Tune const.MIN_OBJ_SEPARATION if needed.
    min_dist_sq_ramp = (const.MIN_OBJ_SEPARATION * 0.7)**2 

    attempts = 0
    max_attempts = count * 35

    sf_line_x = start_finish_line_coords[0][0]
    sf_line_center_y = (start_finish_line_coords[0][1] + start_finish_line_coords[1][1]) / 2
    sf_avoid_radius_sq = (const.MIN_OBJ_SEPARATION * 1.2)**2

    while len(ramps) < count and attempts < max_attempts:
        attempts += 1
        
        # Determine random radius for the circular ramp
        radius = random.uniform(const.RAMP_MIN_RADIUS, const.RAMP_MAX_RADIUS)

        margin = 0.90 
        wx = random.uniform(-const.WORLD_BOUNDS * margin, const.WORLD_BOUNDS * margin)
        wy = random.uniform(-const.WORLD_BOUNDS * margin, const.WORLD_BOUNDS * margin)
        pos = (wx, wy)
        
        # Angle is no longer needed for instantiating a simple circular Ramp
        # angle_deg = random.uniform(0, 360) # This line is removed

        if distance_sq(pos, (sf_line_x, sf_line_center_y)) < sf_avoid_radius_sq:
            continue
            
        # Check spacing against other objects and already placed ramps
        # The min_dist_sq_ramp considers the minimum distance between object centers.
        # More sophisticated spacing could account for individual radii, but this is a good start.
        if is_too_close(pos, existing_objects + ramps, min_dist_sq_ramp):
            continue
            
        # Create the new circular Ramp
        ramps.append(Ramp(wx, wy, radius)) # Pass radius

    if attempts >= max_attempts and len(ramps) < count:
        print(f"Warning: CourseGen - Could only generate {len(ramps)}/{count} ramps.")
    return ramps

def generate_random_hills(count, existing_objects, start_finish_line_coords, course_checkpoint_coords_list):
    hills = []
    attempts = 0
    max_attempts = count * 40
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer_hill = 100 
    while len(hills) < count and attempts < max_attempts:
        attempts += 1
        diameter = random.uniform(const.MIN_HILL_SIZE, const.MAX_HILL_SIZE) # HILL_SIZE is diameter
        half_size = diameter / 2.0
        margin_factor = 0.95 
        wx = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        wy = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        pos = (wx, wy)
        if abs(wx - sf_line_x) < (half_size + sf_avoid_buffer_hill) and \
           (sf_line_y_min - half_size - sf_avoid_buffer_hill) < wy < (sf_line_y_max + half_size + sf_avoid_buffer_hill):
            continue
        too_close_to_course_cp = False
        for cp_x, cp_y in course_checkpoint_coords_list:
            if distance_sq(pos, (cp_x, cp_y)) < (half_size + const.CHECKPOINT_RADIUS + const.MIN_OBJ_SEPARATION * 0.3)**2:
                too_close_to_course_cp = True; break
        if too_close_to_course_cp: continue
        min_dist_sq_hill_to_hill = (half_size + const.MIN_HILL_SIZE / 2.0 + 20)**2
        if is_too_close(pos, hills, min_dist_sq_hill_to_hill): continue
        min_dist_sq_hill_to_other = (half_size + const.MIN_OBJ_SEPARATION * 0.3)**2
        if is_too_close(pos, existing_objects, min_dist_sq_hill_to_other): continue
        hills.append(VisualHill(wx, wy, diameter)) # Pass diameter to VisualHill
    if attempts >= max_attempts and len(hills) < count:
        print(f"Warning: CourseGen - Could only generate {len(hills)}/{count} visual hills.")
    return hills