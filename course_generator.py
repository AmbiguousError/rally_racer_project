# course_generator.py
# This file contains functions for generating the race course elements like checkpoints,
# mud patches, and ramps.

import random
import math

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

    Args:
        new_pos (tuple): (x, y) coordinates of the new position.
        existing_objects (list): A list of objects that have a 'world_x' and 'world_y' attribute.
        min_dist_sq (float): The minimum squared distance allowed.
                             Using squared distance avoids a square root calculation.

    Returns:
        bool: True if new_pos is too close to any object, False otherwise.
    """
    for obj in existing_objects:
        # getattr is used to safely access attributes, defaulting if not present (though they should be)
        obj_pos = (getattr(obj, 'world_x', new_pos[0]), getattr(obj, 'world_y', new_pos[1]))
        if distance_sq(new_pos, obj_pos) < min_dist_sq:
            return True
    return False

def generate_random_checkpoints(count, existing_objects_for_spacing, start_finish_line_coords):
    """
    Generates a list of random Checkpoint coordinates, ensuring they are reasonably spaced.

    Args:
        count (int): The number of checkpoints to generate.
        existing_objects_for_spacing (list): A list of already existing objects (like start/finish gates)
                                             to maintain spacing from.
        start_finish_line_coords (list): Coordinates of the start/finish line to avoid placing checkpoints too close to it.
                                         Example: [(-200, -300), (-200, 300)]

    Returns:
        list: A list of (x, y) tuples representing checkpoint world coordinates.
    """
    checkpoint_coords = []
    # Use constants for spacing and world boundaries
    min_dist_sq_cp = (const.MIN_OBJ_SEPARATION * 2.5)**2 # Checkpoints should be well spread out
    attempts = 0
    max_attempts = count * 75 # Allow more attempts for sparse placement
    margin_factor = 0.90 # Keep checkpoints within 90% of world bounds

    # Define a region around the start/finish line to avoid
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer_x = 500 # Horizontal buffer
    sf_avoid_buffer_y = 300 # Vertical buffer

    while len(checkpoint_coords) < count and attempts < max_attempts:
        attempts += 1
        wx = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        wy = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        pos = (wx, wy)

        # Avoid placing too close to the start/finish line
        if abs(wx - sf_line_x) < sf_avoid_buffer_x and \
           (sf_line_y_min - sf_avoid_buffer_y) < wy < (sf_line_y_max + sf_avoid_buffer_y):
            continue

        # Check against existing_objects_for_spacing (e.g., start/finish gates passed from main)
        # and already placed checkpoints in this generation run.
        # Create temporary Checkpoint objects for is_too_close compatibility if needed,
        # or ensure is_too_close can handle coordinate tuples.
        # For simplicity, is_too_close expects objects with world_x, world_y.
        # So, we convert coords to temporary objects for checking.
        temp_checkpoint_objects = [Checkpoint(c_x, c_y, -1) for c_x,c_y in checkpoint_coords]
        all_to_check_spacing = existing_objects_for_spacing + temp_checkpoint_objects

        if is_too_close(pos, all_to_check_spacing, min_dist_sq_cp):
            continue
        
        checkpoint_coords.append(pos)

    if attempts >= max_attempts and len(checkpoint_coords) < count:
        print(f"Warning: CourseGen - Could only generate {len(checkpoint_coords)}/{count} checkpoints due to spacing constraints.")
    
    # Fallback if no checkpoints generated (e.g., count is 1 and first attempt fails)
    while len(checkpoint_coords) < min(count, 1) and count > 0 : # Ensure at least one if count > 0
        wx = random.uniform(const.WORLD_BOUNDS*0.3, const.WORLD_BOUNDS*0.7) 
        wy = random.uniform(-const.WORLD_BOUNDS*0.5, const.WORLD_BOUNDS*0.5)
        pos = (wx,wy)
        temp_checkpoint_objects = [Checkpoint(c_x, c_y, -1) for c_x,c_y in checkpoint_coords]
        if not is_too_close(pos, temp_checkpoint_objects, min_dist_sq_cp):
            checkpoint_coords.append(pos)
            # print("Warning: CourseGen - Adding fallback checkpoint.")
        else: # Absolute fallback
            checkpoint_coords.append((const.WORLD_BOUNDS*0.5, 0))
            # print("Warning: CourseGen - Adding absolute fallback checkpoint (last resort).")
            break # Avoid infinite loop if even this fails
            
    return checkpoint_coords


def generate_random_mud_patches(count, existing_objects, start_finish_line_coords, course_checkpoint_coords_list):
    """
    Generates a list of MudPatch objects.

    Args:
        count (int): Number of mud patches to generate.
        existing_objects (list): List of objects (like Checkpoints, other MudPatches) to avoid.
        start_finish_line_coords (list): Coordinates of the start/finish line.
        course_checkpoint_coords_list (list): List of (x,y) for actual course checkpoints to avoid placing mud on them.

    Returns:
        list: A list of MudPatch objects.
    """
    mud_patches = []
    attempts = 0
    max_attempts = count * 30 # Allow more attempts

    # Define a region around the start/finish line to avoid
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer = 150 # Buffer around S/F line for mud

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
        if abs(wx - sf_line_x) < (half_size + sf_avoid_buffer) and \
           (sf_line_y_min - half_size - sf_avoid_buffer) < wy < (sf_line_y_max + half_size + sf_avoid_buffer):
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
        min_dist_sq_mud = (half_size + const.MIN_MUD_SIZE / 2 + const.MIN_OBJ_SEPARATION * 0.2)**2
        if is_too_close(pos, existing_objects + mud_patches, min_dist_sq_mud):
            continue
            
        mud_patches.append(MudPatch(wx, wy, size))

    if attempts >= max_attempts and len(mud_patches) < count:
        print(f"Warning: CourseGen - Could only generate {len(mud_patches)}/{count} mud patches.")
    return mud_patches


def generate_random_ramps(count, existing_objects, start_finish_line_coords):
    """
    Generates a list of Ramp objects.

    Args:
        count (int): Number of ramps to generate.
        existing_objects (list): List of objects (Checkpoints, MudPatches, other Ramps) to avoid.
        start_finish_line_coords (list): Coordinates of the start/finish line.

    Returns:
        list: A list of Ramp objects.
    """
    ramps = []
    min_dist_sq_ramp = (const.MIN_OBJ_SEPARATION * 0.8)**2 # Ramps can be closer than CPs
    attempts = 0
    max_attempts = count * 35

    sf_line_x = start_finish_line_coords[0][0]
    sf_line_center_y = (start_finish_line_coords[0][1] + start_finish_line_coords[1][1]) / 2
    sf_avoid_radius_sq = (const.MIN_OBJ_SEPARATION * 1.2)**2

    while len(ramps) < count and attempts < max_attempts:
        attempts += 1
        margin = 0.90 # Keep ramps generally within bounds
        wx = random.uniform(-const.WORLD_BOUNDS * margin, const.WORLD_BOUNDS * margin)
        wy = random.uniform(-const.WORLD_BOUNDS * margin, const.WORLD_BOUNDS * margin)
        pos = (wx, wy)
        angle_deg = random.uniform(0, 360) # Random orientation for the ramp

        # Avoid start/finish line
        if distance_sq(pos, (sf_line_x, sf_line_center_y)) < sf_avoid_radius_sq:
            continue
            
        # Check against all other objects (checkpoints, mud, other ramps)
        # For ramps, the 'existing_objects' list in is_too_close will include previously placed ramps.
        if is_too_close(pos, existing_objects + ramps, min_dist_sq_ramp):
            continue
            
        ramps.append(Ramp(wx, wy, const.RAMP_WIDTH, const.RAMP_HEIGHT, angle_deg))

    if attempts >= max_attempts and len(ramps) < count:
        print(f"Warning: CourseGen - Could only generate {len(ramps)}/{count} ramps.")
    return ramps
