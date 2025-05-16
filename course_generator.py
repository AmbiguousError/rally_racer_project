# rally_racer_project/course_generator.py
# This file contains functions for generating the race course elements.

import pygame
import random
import math

import constants as const
from utils import (distance_sq, lerp, point_segment_distance_sq, distance, 
                   normalize_angle, deg_to_rad, rad_to_deg, angle_difference) # Ensure all needed utils are imported
from classes import Checkpoint, MudPatch, Ramp # Assuming these are correctly imported via classes/__init__.py

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

class VisualHill:
    """
    Represents a physical hill patch on the track, circular.
    """
    def __init__(self, world_x, world_y, diameter):
        self.world_x = world_x
        self.world_y = world_y
        self.diameter = diameter
        self.radius = diameter / 2.0
        self.color = const.HILL_COLOR_NO_GRASS # Using pastel name from constants
        self.border_color = const.DARK_HILL_COLOR # Using pastel name
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
            screen_rect_approx = self.rect.move(-camera_offset_x + const.CENTER_X, -camera_offset_y + const.CENTER_Y)
            if not screen_rect_approx.colliderect(surface.get_rect()): return 
        if screen_radius < 1: return
        pygame.draw.circle(surface, self.color, (screen_x, screen_y), screen_radius)
        pygame.draw.circle(surface, self.border_color, (screen_x, screen_y), screen_radius, 2)

    def check_collision(self, car_world_rect): # Broad-phase
        return self.rect.colliderect(car_world_rect)

    def check_crest_collision(self, car_center_x, car_center_y): # Narrow-phase for jump
        return distance_sq((car_center_x, car_center_y), (self.world_x, self.world_y)) < (self.crest_radius ** 2)

def get_perpendicular_offset_points(center_x, center_y, tangent_dx, tangent_dy, width):
    """
    Calculates two points offset perpendicularly from a center point along a tangent.
    """
    length = math.sqrt(tangent_dx**2 + tangent_dy**2)
    if length == 0: norm_dx, norm_dy = 0, 1.0
    else: norm_dx = tangent_dx / length; norm_dy = tangent_dy / length
    perp_dx = -norm_dy; perp_dy = norm_dx
    half_width = width / 2.0
    p1_x = center_x + perp_dx * half_width; p1_y = center_y + perp_dy * half_width
    p2_x = center_x - perp_dx * half_width; p2_y = center_y - perp_dy * half_width
    return (p1_x, p1_y), (p2_x, p2_y)

def generate_road_path(checkpoint_objects_list, start_finish_line_coords, road_width):
    """
    Generates a road path based on checkpoints, attempting to incorporate roundabouts.
    """
    final_centerline_points = []
    road_segments_polygons = []

    anchor_nodes = []
    sf_p1 = start_finish_line_coords[0]; sf_p2 = start_finish_line_coords[1]
    sf_mid_x = (sf_p1[0] + sf_p2[0]) / 2; sf_mid_y = (sf_p1[1] + sf_p2[1]) / 2
    sf_dx = sf_p2[0] - sf_p1[0]; sf_dy = sf_p2[1] - sf_p1[1]
    sf_len = math.sqrt(sf_dx**2 + sf_dy**2)
    track_dir_x = -sf_dy / sf_len if sf_len > 0 else 1.0
    track_dir_y = sf_dx / sf_len if sf_len > 0 else 0.0
    
    ext_offset = const.ROUNDABOUT_CENTERLINE_RADIUS + road_width * 1.5 # Increased offset
    extended_start_node = (sf_mid_x - track_dir_x * ext_offset, sf_mid_y - track_dir_y * ext_offset)
    anchor_nodes.append({'pos': extended_start_node, 'type': 'connector', 'is_roundabout': False})
    anchor_nodes.append({'pos': (sf_mid_x, sf_mid_y), 'type': 'sf_line', 'is_roundabout': False})

    course_cps_objects = sorted([cp for cp in checkpoint_objects_list if not cp.is_gate], key=lambda cp: cp.index)
    for cp_obj in course_cps_objects:
        anchor_nodes.append({'pos': (cp_obj.world_x, cp_obj.world_y), 'type': 'checkpoint', 
                             'is_roundabout': const.CREATE_ROUNDABOUTS})

    anchor_nodes.append({'pos': (sf_mid_x, sf_mid_y), 'type': 'sf_line', 'is_roundabout': False})
    extended_end_node = (sf_mid_x + track_dir_x * ext_offset, sf_mid_y + track_dir_y * ext_offset)
    anchor_nodes.append({'pos': extended_end_node, 'type': 'connector', 'is_roundabout': False})
    
    if len(anchor_nodes) < 2: return [], []

    current_path_point = anchor_nodes[0]['pos']
    final_centerline_points.append(current_path_point)

    for i in range(len(anchor_nodes) -1):
        start_node_info = anchor_nodes[i]
        end_node_info   = anchor_nodes[i+1]

        p_start = final_centerline_points[-1] # Start from where the last segment (or roundabout) ended
        p_end_target = end_node_info['pos']   # The actual center of the next anchor

        if end_node_info['is_roundabout']:
            rb_center_x, rb_center_y = p_end_target
            
            # Vector from p_start to roundabout center
            dir_to_rb_x = rb_center_x - p_start[0]
            dir_to_rb_y = rb_center_y - p_start[1]
            len_to_rb = math.sqrt(dir_to_rb_x**2 + dir_to_rb_y**2)

            if len_to_rb > const.ROUNDABOUT_CENTERLINE_RADIUS: # If there's space for a straight approach
                norm_dir_to_rb_x = dir_to_rb_x / len_to_rb if len_to_rb > 0 else 0
                norm_dir_to_rb_y = dir_to_rb_y / len_to_rb if len_to_rb > 0 else 0
                
                # Calculate the point where the straight segment should meet the roundabout circle
                rb_entry_x = rb_center_x - norm_dir_to_rb_x * const.ROUNDABOUT_CENTERLINE_RADIUS
                rb_entry_y = rb_center_y - norm_dir_to_rb_y * const.ROUNDABOUT_CENTERLINE_RADIUS

                # Subdivide straight segment leading to rb_entry
                dist_straight = distance(p_start, (rb_entry_x, rb_entry_y))
                num_subs = max(1, int(dist_straight / (road_width * 0.3))) # Adjust density
                for j in range(1, num_subs + 1):
                    t = j / float(num_subs)
                    final_centerline_points.append((lerp(p_start[0], rb_entry_x, t), lerp(p_start[1], rb_entry_y, t)))
                
                current_arc_start_point = (rb_entry_x, rb_entry_y)
            else: # p_start is already very close or inside roundabout radius, start arc from p_start
                current_arc_start_point = p_start

            # Determine the exit direction for the roundabout
            node_after_rb_info = anchor_nodes[i+2] if (i+2) < len(anchor_nodes) else end_node_info # Next anchor after this roundabout
            pos_after_rb_anchor = node_after_rb_info['pos']
            
            dir_from_rb_x = pos_after_rb_anchor[0] - rb_center_x
            dir_from_rb_y = pos_after_rb_anchor[1] - rb_center_y
            len_from_rb = math.sqrt(dir_from_rb_x**2 + dir_from_rb_y**2)
            norm_dir_from_rb_x = dir_from_rb_x / len_from_rb if len_from_rb > 0 else 0
            norm_dir_from_rb_y = dir_from_rb_y / len_from_rb if len_from_rb > 0 else 0

            rb_exit_x = rb_center_x + norm_dir_from_rb_x * const.ROUNDABOUT_CENTERLINE_RADIUS
            rb_exit_y = rb_center_y + norm_dir_from_rb_y * const.ROUNDABOUT_CENTERLINE_RADIUS

            start_angle_rad = math.atan2(current_arc_start_point[1] - rb_center_y, current_arc_start_point[0] - rb_center_x)
            end_angle_rad = math.atan2(rb_exit_y - rb_center_y, rb_exit_x - rb_center_x)

            # Ensure counter-clockwise sweep from start to end
            if end_angle_rad < start_angle_rad: end_angle_rad += 2 * math.pi
            
            # If sweep is too small (e.g. < 90 deg), or too large (almost full circle back), force a standard sweep
            angle_sweep = end_angle_rad - start_angle_rad
            if angle_sweep < math.pi / 2 or angle_sweep > math.pi * 1.85 : # Less than 90 or more than ~330
                # Default to a ~270 degree CCW turn from entry direction for predictability
                # This part is heuristic and can be improved for ideal tangential exits
                end_angle_rad = start_angle_rad + (math.pi * 1.5) # 270 degree sweep

            num_arc_segments = const.ROUNDABOUT_DETAIL_SEGMENTS
            for k in range(1, num_arc_segments + 1): 
                t_arc = k / float(num_arc_segments)
                current_angle_rad = lerp(start_angle_rad, end_angle_rad, t_arc)
                arc_x = rb_center_x + const.ROUNDABOUT_CENTERLINE_RADIUS * math.cos(current_angle_rad)
                arc_y = rb_center_y + const.ROUNDABOUT_CENTERLINE_RADIUS * math.sin(current_angle_rad)
                final_centerline_points.append((arc_x, arc_y))
        
        else: # Straight segment to p_end_target
            dist_straight = distance(p_start, p_end_target)
            num_subs = max(1, int(dist_straight / (road_width * 0.3)))
            for j in range(1, num_subs + 1):
                t = j / float(num_subs)
                final_centerline_points.append((lerp(p_start[0], p_end_target[0], t), lerp(p_start[1], p_end_target[1], t)))

    # Remove duplicate consecutive points
    if final_centerline_points:
        unique_final_centerline = [final_centerline_points[0]]
        for k in range(1, len(final_centerline_points)):
            if distance_sq(final_centerline_points[k], final_centerline_points[k-1]) > 0.1: # Small threshold
                unique_final_centerline.append(final_centerline_points[k])
        final_centerline_points = unique_final_centerline
    
    if len(final_centerline_points) < 2: return final_centerline_points, []

    # Generate road edge polygons (Quads) from the final_centerline_points
    left_edge_points = []; right_edge_points = []
    # (The rest of this polygon generation part is the same as your last working version using averaged tangents)
    for i in range(len(final_centerline_points)):
        p_curr = final_centerline_points[i]; tangent_dx, tangent_dy = 0.0, 0.0
        if i == 0:
            if len(final_centerline_points) > 1: p_next = final_centerline_points[i+1]; tangent_dx = p_next[0] - p_curr[0]; tangent_dy = p_next[1] - p_curr[1]
            else: tangent_dx = 1.0; tangent_dy = 0.0
        elif i == len(final_centerline_points) - 1:
            p_prev = final_centerline_points[i-1]; tangent_dx = p_curr[0] - p_prev[0]; tangent_dy = p_curr[1] - p_prev[1]
        else:
            p_prev = final_centerline_points[i-1]; p_next = final_centerline_points[i+1]
            v_in_dx = p_curr[0]-p_prev[0]; v_in_dy = p_curr[1]-p_prev[1]; len_in = math.sqrt(v_in_dx**2+v_in_dy**2)
            if len_in > 1e-3: v_in_dx/=len_in; v_in_dy/=len_in
            else: v_in_dx = 0; v_in_dy = 0 # Avoid issues if p_curr == p_prev
            v_out_dx = p_next[0]-p_curr[0]; v_out_dy = p_next[1]-p_curr[1]; len_out = math.sqrt(v_out_dx**2+v_out_dy**2)
            if len_out > 1e-3: v_out_dx/=len_out; v_out_dy/=len_out
            else: v_out_dx = 0; v_out_dy = 0 # Avoid issues if p_curr == p_next
            
            avg_dx = v_in_dx + v_out_dx; avg_dy = v_in_dy + v_out_dy
            len_avg = math.sqrt(avg_dx**2 + avg_dy**2)
            if len_avg > 1e-3: tangent_dx = avg_dx/len_avg; tangent_dy = avg_dy/len_avg
            else: # Fallback if vectors cancel out (e.g. U-turn) or were zero
                tangent_dx = v_out_dx if len_out > 1e-3 else (v_in_dx if len_in > 1e-3 else 1.0)
                tangent_dy = v_out_dy if len_out > 1e-3 else (v_in_dy if len_in > 1e-3 else 0.0)
        
        len_final_tangent = math.sqrt(tangent_dx**2 + tangent_dy**2)
        if len_final_tangent > 1e-3: tangent_dx /= len_final_tangent; tangent_dy /= len_final_tangent
        else: tangent_dx = 1.0; tangent_dy = 0.0 # Final fallback
        
        left_pt, right_pt = get_perpendicular_offset_points(p_curr[0], p_curr[1], tangent_dx, tangent_dy, road_width)
        left_edge_points.append(left_pt); right_edge_points.append(right_pt)

    for i in range(len(final_centerline_points) - 1):
        road_segments_polygons.append([left_edge_points[i], left_edge_points[i+1], right_edge_points[i+1], right_edge_points[i]])
        
    return final_centerline_points, road_segments_polygons


def generate_random_checkpoints(count, existing_objects_for_spacing, start_finish_line_coords):
    checkpoint_coords = []
    min_dist_sq_cp = (const.MIN_OBJ_SEPARATION * 2.5)**2; attempts = 0; max_attempts = count * 75; margin_factor = 0.90
    sf_line_x = start_finish_line_coords[0][0]; sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1]); sf_avoid_buffer_x = 500; sf_avoid_buffer_y = 300
    while len(checkpoint_coords) < count and attempts < max_attempts:
        attempts += 1; wx = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor)
        wy = random.uniform(-const.WORLD_BOUNDS * margin_factor, const.WORLD_BOUNDS * margin_factor); pos = (wx, wy)
        if abs(wx - sf_line_x) < sf_avoid_buffer_x and (sf_line_y_min - sf_avoid_buffer_y) < wy < (sf_line_y_max + sf_avoid_buffer_y): continue
        temp_checkpoint_objects = [Checkpoint(c_x, c_y, -1) for c_x,c_y in checkpoint_coords]
        all_to_check_spacing = existing_objects_for_spacing + temp_checkpoint_objects
        if is_too_close(pos, all_to_check_spacing, min_dist_sq_cp): continue
        checkpoint_coords.append(pos)
    if attempts >= max_attempts and len(checkpoint_coords) < count: print(f"Warning: CourseGen - Could only generate {len(checkpoint_coords)}/{count} checkpoints.")
    while len(checkpoint_coords) < min(count, 1) and count > 0 :
        wx = random.uniform(const.WORLD_BOUNDS*0.3, const.WORLD_BOUNDS*0.7); wy = random.uniform(-const.WORLD_BOUNDS*0.5, const.WORLD_BOUNDS*0.5); pos = (wx,wy)
        temp_checkpoint_objects = [Checkpoint(c_x, c_y, -1) for c_x,c_y in checkpoint_coords]
        if not is_too_close(pos, temp_checkpoint_objects, min_dist_sq_cp): checkpoint_coords.append(pos)
        else: checkpoint_coords.append((const.WORLD_BOUNDS*0.5, 0)); break 
    return checkpoint_coords

def generate_random_mud_patches(count, existing_objects, start_finish_line_coords, course_checkpoint_coords_list, centerline_road_points, road_width):
    mud_patches = []
    attempts = 0; max_attempts = count * 50 
    sf_line_x = start_finish_line_coords[0][0]
    sf_line_y_min = min(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1], start_finish_line_coords[1][1])
    sf_avoid_buffer_mud = 150 
    road_clearance_buffer = 20 
    while len(mud_patches) < count and attempts < max_attempts:
        attempts += 1
        size = random.randint(const.MIN_MUD_SIZE, const.MAX_MUD_SIZE); object_radius = size / 2.0
        wx = random.uniform(-const.WORLD_BOUNDS*0.95, const.WORLD_BOUNDS*0.95); wy = random.uniform(-const.WORLD_BOUNDS*0.95, const.WORLD_BOUNDS*0.95); pos = (wx, wy)
        if abs(wx - sf_line_x) < (object_radius + sf_avoid_buffer_mud) and \
           (sf_line_y_min - object_radius - sf_avoid_buffer_mud) < wy < (sf_line_y_max + object_radius + sf_avoid_buffer_mud): continue
        too_close_to_course_cp = False
        for cp_x, cp_y in course_checkpoint_coords_list:
            if distance_sq(pos, (cp_x, cp_y)) < (object_radius + const.CHECKPOINT_RADIUS + const.MIN_OBJ_SEPARATION * 0.4)**2: too_close_to_course_cp = True; break
        if too_close_to_course_cp: continue
        min_dist_sq_this_mud = (object_radius + const.MIN_MUD_SIZE / 2 + const.MIN_OBJ_SEPARATION * 0.2)**2
        if is_too_close(pos, existing_objects + mud_patches, min_dist_sq_this_mud): continue
        on_road_or_too_close = False
        if centerline_road_points and len(centerline_road_points) >= 2:
            min_safe_dist_from_road_center_sq = (road_width / 2.0 + object_radius + road_clearance_buffer)**2
            for i in range(len(centerline_road_points) - 1):
                road_p1 = centerline_road_points[i]; road_p2 = centerline_road_points[i+1]
                if point_segment_distance_sq(pos, road_p1, road_p2) < min_safe_dist_from_road_center_sq: on_road_or_too_close = True; break
        if on_road_or_too_close: continue
        mud_patches.append(MudPatch(wx, wy, size))
    if attempts >= max_attempts and len(mud_patches) < count: print(f"Warning: CourseGen - Could only generate {len(mud_patches)}/{count} mud patches.")
    return mud_patches

def generate_random_ramps(count, existing_objects, start_finish_line_coords, centerline_road_points, road_width):
    ramps = []
    min_dist_sq_ramp = (const.MIN_OBJ_SEPARATION * 0.7)**2 
    attempts = 0; max_attempts = count * 50
    sf_line_x = start_finish_line_coords[0][0]; sf_line_center_y = (start_finish_line_coords[0][1] + start_finish_line_coords[1][1]) / 2
    sf_avoid_radius_sq = (const.MIN_OBJ_SEPARATION * 1.2)**2
    road_clearance_buffer = 10 
    while len(ramps) < count and attempts < max_attempts:
        attempts += 1
        radius = random.uniform(const.RAMP_MIN_RADIUS, const.RAMP_MAX_RADIUS); object_radius = radius
        margin = 0.90; wx = random.uniform(-const.WORLD_BOUNDS*margin,const.WORLD_BOUNDS*margin); wy = random.uniform(-const.WORLD_BOUNDS*margin,const.WORLD_BOUNDS*margin); pos = (wx, wy)
        if distance_sq(pos, (sf_line_x, sf_line_center_y)) < sf_avoid_radius_sq: continue
        if is_too_close(pos, existing_objects + ramps, min_dist_sq_ramp): continue
        on_road_or_too_close = False
        if centerline_road_points and len(centerline_road_points) >= 2:
            min_safe_dist_from_road_center_sq = (road_width / 2.0 + object_radius + road_clearance_buffer)**2
            for i in range(len(centerline_road_points) - 1):
                road_p1 = centerline_road_points[i]; road_p2 = centerline_road_points[i+1]
                if point_segment_distance_sq(pos, road_p1, road_p2) < min_safe_dist_from_road_center_sq: on_road_or_too_close = True; break
        if on_road_or_too_close: continue # Ramps strictly off-road for now by this logic
        ramps.append(Ramp(wx, wy, radius))
    if attempts >= max_attempts and len(ramps) < count: print(f"Warning: CourseGen - Could only generate {len(ramps)}/{count} ramps.")
    return ramps

def generate_random_hills(count, existing_objects, start_finish_line_coords, course_checkpoint_coords_list, centerline_road_points, road_width):
    hills = []
    attempts = 0; max_attempts = count * 50
    sf_line_x = start_finish_line_coords[0][0]; sf_line_y_min = min(start_finish_line_coords[0][1],start_finish_line_coords[1][1])
    sf_line_y_max = max(start_finish_line_coords[0][1],start_finish_line_coords[1][1]); sf_avoid_buffer_hill = 100
    road_clearance_buffer = 30 
    while len(hills) < count and attempts < max_attempts:
        attempts += 1
        diameter = random.uniform(const.MIN_HILL_SIZE, const.MAX_HILL_SIZE); object_radius = diameter / 2.0
        margin_factor = 0.95; wx = random.uniform(-const.WORLD_BOUNDS*margin_factor,const.WORLD_BOUNDS*margin_factor); wy = random.uniform(-const.WORLD_BOUNDS*margin_factor,const.WORLD_BOUNDS*margin_factor); pos = (wx, wy)
        if abs(wx - sf_line_x) < (object_radius + sf_avoid_buffer_hill) and \
           (sf_line_y_min - object_radius - sf_avoid_buffer_hill) < wy < (sf_line_y_max + object_radius + sf_avoid_buffer_hill): continue
        too_close_to_course_cp = False
        for cp_x, cp_y in course_checkpoint_coords_list:
            if distance_sq(pos, (cp_x, cp_y)) < (object_radius + const.CHECKPOINT_RADIUS + const.MIN_OBJ_SEPARATION*0.3)**2: too_close_to_course_cp = True; break
        if too_close_to_course_cp: continue
        min_dist_sq_hill_to_hill = (object_radius + const.MIN_HILL_SIZE / 2.0 + 20)**2
        if is_too_close(pos, hills, min_dist_sq_hill_to_hill): continue
        min_dist_sq_hill_to_other = (object_radius + const.MIN_OBJ_SEPARATION * 0.3)**2
        if is_too_close(pos, existing_objects, min_dist_sq_hill_to_other): continue
        on_road_or_too_close = False
        if centerline_road_points and len(centerline_road_points) >= 2:
            min_safe_dist_from_road_center_sq = (road_width / 2.0 + object_radius + road_clearance_buffer)**2
            for i in range(len(centerline_road_points) - 1):
                road_p1 = centerline_road_points[i]; road_p2 = centerline_road_points[i+1]
                if point_segment_distance_sq(pos, road_p1, road_p2) < min_safe_dist_from_road_center_sq: on_road_or_too_close = True; break
        if on_road_or_too_close: continue
        hills.append(VisualHill(wx, wy, diameter))
    if attempts >= max_attempts and len(hills) < count: print(f"Warning: CourseGen - Could only generate {len(hills)}/{count} visual hills.")
    return hills