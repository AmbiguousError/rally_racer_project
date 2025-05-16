# rally_racer_project/course_generator.py
# This file contains functions for generating the race course elements like checkpoints,
# mud patches, ramps, and visual hills.

import random
import math
import pygame # For pygame.Rect if used in VisualHill internal calculations

# Assuming constants.py and utils.py are in the parent directory or project root is in PYTHONPATH
# If running main.py from the project root, these imports should work.
import constants as const
from utils import distance_sq, lerp # For checking distances between objects

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

# rally_racer_project/course_generator.py
# ... (imports and other classes/functions like VisualHill, is_too_close, etc.)

# Helper function for road generation (can be inside generate_road_path or global to module)
def get_perpendicular_offset_points(center_x, center_y, tangent_dx, tangent_dy, width):
    """
    Calculates two points offset perpendicularly from a center point along a tangent.
    """
    # Normalize the tangent vector (direction of the road segment)
    length = math.sqrt(tangent_dx**2 + tangent_dy**2)
    if length == 0: # Avoid division by zero for coincident points
        # Default to horizontal perpendicular if tangent is zero length
        norm_dx, norm_dy = 0, 1
    else:
        norm_dx = tangent_dx / length
        norm_dy = tangent_dy / length

    # Perpendicular vector (rotate tangent by 90 degrees)
    perp_dx = -norm_dy
    perp_dy = norm_dx

    half_width = width / 2.0

    p1_x = center_x + perp_dx * half_width
    p1_y = center_y + perp_dy * half_width
    p2_x = center_x - perp_dx * half_width
    p2_y = center_y - perp_dy * half_width
    return (p1_x, p1_y), (p2_x, p2_y)


# rally_racer_project/course_generator.py

# ... (other imports, is_too_close, VisualHill class, get_perpendicular_offset_points,
#      generate_random_checkpoints, generate_random_mud_patches, generate_random_ramps, generate_random_hills) ...

def generate_road_path(checkpoint_objects_list, start_finish_line_coords, road_width):
    """
    Generates a road path based on checkpoints.
    Returns:
        centerline_points (list of tuples): Points defining the road's centerline.
        road_segments_polygons (list of lists of tuples): List of polygons (quads) representing road surface.
    """
    centerline_points = []
    road_segments_polygons = []
    
    path_nodes = []
    sf_mid_x = (start_finish_line_coords[0][0] + start_finish_line_coords[1][0]) / 2
    sf_mid_y = (start_finish_line_coords[0][1] + start_finish_line_coords[1][1]) / 2
    
    course_cps = sorted([cp for cp in checkpoint_objects_list if not cp.is_gate], key=lambda cp: cp.index)

    if not course_cps:
        p_start = (sf_mid_x, sf_mid_y - 200) 
        p_end = (sf_mid_x, sf_mid_y + 200)   
        path_nodes.extend([p_start, (sf_mid_x, sf_mid_y), p_end])
    else:
        sf_dx = start_finish_line_coords[1][0] - start_finish_line_coords[0][0]
        sf_dy = start_finish_line_coords[1][1] - start_finish_line_coords[0][1]
        sf_len = math.sqrt(sf_dx**2 + sf_dy**2)
        track_dir_x = -sf_dy / sf_len if sf_len > 0 else 1.0 # Ensure float
        track_dir_y = sf_dx / sf_len if sf_len > 0 else 0.0  # Ensure float

        # Start a bit before the S/F line, oriented correctly
        path_nodes.append((sf_mid_x - track_dir_x * road_width, sf_mid_y - track_dir_y * road_width))
        path_nodes.append((sf_mid_x, sf_mid_y)) 

        for cp in course_cps:
            path_nodes.append((cp.world_x, cp.world_y))
        
        path_nodes.append((sf_mid_x, sf_mid_y)) # Loop back through S/F
        # End a bit after the S/F line
        path_nodes.append((sf_mid_x + track_dir_x * road_width, sf_mid_y + track_dir_y * road_width))


    if len(path_nodes) < 2:
        return [], []

    # --- Refined Centerline (Optional: Add more points for smoother curves later if needed) ---
    # For now, path_nodes will be our centerline_points.
    # If you want smoother curves, you'd interpolate more points here (e.g., using Catmull-Rom).
    # Let's add a simple subdivision for slightly smoother tangents:
    # For a slightly smoother path using subdivision and midpoint displacement (basic):
    subdivided_centerline = []
    if len(path_nodes) >=2:
        subdivided_centerline.append(path_nodes[0])
        for i in range(len(path_nodes) - 1):
            p0 = path_nodes[i]
            p1 = path_nodes[i+1]
            # Add N subdivisions (e.g., 3 subdivisions = 4 new segments)
            
            # --- TRY INCREASING THIS VALUE ---
            num_intermediate_points = 7 # Was 3. Try 5, 7, or 10.
            # --- END CHANGE ---

            for j in range(1, num_intermediate_points + 1):
                t = j / (num_intermediate_points + 1.0) # Ensure float division
                ix = lerp(p0[0], p1[0], t)
                iy = lerp(p0[1], p1[1], t)
                subdivided_centerline.append((ix, iy))
            subdivided_centerline.append(p1) # Add the actual end node of the segment
    centerline_points = subdivided_centerline
    
    if len(centerline_points) < 2:
         return [], []


    # --- Generate edge points with improved tangent/normal calculation ---
    left_edge_points = []
    right_edge_points = []

    for i in range(len(centerline_points)):
        p_curr = centerline_points[i]
        
        tangent_dx, tangent_dy = 0, 0

        if i == 0: # First point
            p_next = centerline_points[i+1]
            tangent_dx = p_next[0] - p_curr[0]
            tangent_dy = p_next[1] - p_curr[1]
        elif i == len(centerline_points) - 1: # Last point
            p_prev = centerline_points[i-1]
            tangent_dx = p_curr[0] - p_prev[0]
            tangent_dy = p_curr[1] - p_prev[1]
        else: # Intermediate points - use average of incoming and outgoing segment directions
            p_prev = centerline_points[i-1]
            p_next = centerline_points[i+1]

            # Vector from previous to current
            v_in_dx = p_curr[0] - p_prev[0]
            v_in_dy = p_curr[1] - p_prev[1]
            len_in = math.sqrt(v_in_dx**2 + v_in_dy**2)
            if len_in > 0:
                v_in_dx /= len_in
                v_in_dy /= len_in

            # Vector from current to next
            v_out_dx = p_next[0] - p_curr[0]
            v_out_dy = p_next[1] - p_curr[1]
            len_out = math.sqrt(v_out_dx**2 + v_out_dy**2)
            if len_out > 0:
                v_out_dx /= len_out
                v_out_dy /= len_out
            
            # Average the normalized direction vectors
            avg_dx = (v_in_dx + v_out_dx) 
            avg_dy = (v_in_dy + v_out_dy)
            len_avg = math.sqrt(avg_dx**2 + avg_dy**2)

            if len_avg > 0: # If vectors aren't opposite
                tangent_dx = avg_dx / len_avg
                tangent_dy = avg_dy / len_avg
            else: # Vectors were opposite (e.g. 180 degree turn point), use outgoing as fallback
                  # This case might still cause pinching if not handled by spline/smoothing.
                tangent_dx = v_out_dx 
                tangent_dy = v_out_dy
                if not (tangent_dx or tangent_dy) and v_in_dx or v_in_dy: # if v_out was zero length
                    tangent_dx = v_in_dx
                    tangent_dy = v_in_dy
                elif not (tangent_dx or tangent_dy): # if both were zero length (coincident points)
                    tangent_dx = 1.0; tangent_dy = 0.0 # default

        left_pt, right_pt = get_perpendicular_offset_points(p_curr[0], p_curr[1], tangent_dx, tangent_dy, road_width)
        left_edge_points.append(left_pt)
        right_edge_points.append(right_pt)

    # Create quad polygons for each segment
    for i in range(len(centerline_points) - 1):
        p1_left = left_edge_points[i]
        p1_right = right_edge_points[i]
        p2_left = left_edge_points[i+1]
        p2_right = right_edge_points[i+1]
        
        road_segments_polygons.append([p1_left, p2_left, p2_right, p1_right])
        
    return centerline_points, road_segments_polygons


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