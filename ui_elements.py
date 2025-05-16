# rally_racer_project/ui_elements.py
# This file contains functions for drawing UI elements like buttons, map, gauges, etc.

import pygame
import math

import constants as const
from utils import deg_to_rad, clamp, lerp

# --- Track Background Scrolling Function ---
# rally_racer_project/ui_elements.py
# ... (imports and other functions)

def draw_scrolling_track(surface, offset_x, offset_y, visual_hills_list=None, road_segments_polygons=None):
    # ... (grass drawing) ...
    surface.fill(const.GRASS_COLOR)
    line_spacing_grass = 60; line_color_grass = const.LIGHT_GRASS_COLOR; line_width_grass = 1
    start_y_grass_abs = -(offset_y % line_spacing_grass)
    for y_offset in range(int(start_y_grass_abs), const.SCREEN_HEIGHT, line_spacing_grass):
        pygame.draw.line(surface, line_color_grass, (0, y_offset), (const.SCREEN_WIDTH, y_offset), line_width_grass)
    start_x_grass_abs = -(offset_x % line_spacing_grass)
    for x_offset in range(int(start_x_grass_abs), const.SCREEN_WIDTH, line_spacing_grass):
        pygame.draw.line(surface, line_color_grass, (x_offset, 0), (x_offset, const.SCREEN_HEIGHT), line_width_grass)

    # --- Draw Road Segments ---
    if road_segments_polygons:
        screen_rect = surface.get_rect() # Get screen rectangle for culling
        for road_poly_world_coords in road_segments_polygons:
            if len(road_poly_world_coords) < 3:
                continue

            # Calculate screen coordinates for the polygon's vertices
            road_poly_screen_coords = []
            min_x_screen, max_x_screen = float('inf'), float('-inf')
            min_y_screen, max_y_screen = float('inf'), float('-inf')

            for wx, wy in road_poly_world_coords:
                screen_x = int(wx - offset_x + const.CENTER_X)
                screen_y = int(wy - offset_y + const.CENTER_Y)
                road_poly_screen_coords.append((screen_x, screen_y))
                min_x_screen = min(min_x_screen, screen_x)
                max_x_screen = max(max_x_screen, screen_x)
                min_y_screen = min(min_y_screen, screen_y)
                max_y_screen = max(max_y_screen, screen_y)
            
            # Create a bounding box for the screen polygon
            poly_screen_bbox = pygame.Rect(min_x_screen, min_y_screen, max_x_screen - min_x_screen, max_y_screen - min_y_screen)

            # Cull if the polygon's bounding box doesn't intersect the screen
            if poly_screen_bbox.colliderect(screen_rect):
                pygame.draw.polygon(surface, const.ROAD_COLOR, road_poly_screen_coords)
                if const.ROAD_BORDER_WIDTH > 0:
                    pygame.draw.polygon(surface, const.ROAD_BORDER_COLOR, road_poly_screen_coords, const.ROAD_BORDER_WIDTH)

    # --- Draw Visual Hills ---
    if visual_hills_list:
        for hill in visual_hills_list:
            hill.draw(surface, offset_x, offset_y)
            
# --- Map Drawing Function ---
# (draw_map function remains as it was in the last full version you have,
#  it already has visual_hills_list and ramps_list as optional parameters.
#  We haven't added roads to the minimap drawing logic yet.)
def draw_map(surface, player_car, ai_cars, mud_patches, checkpoints, next_checkpoint_index_on_list, start_finish_line_coords, map_display_rect, world_game_bounds, ramps_list=None, visual_hills_list=None):
    map_surface = pygame.Surface(map_display_rect.size, pygame.SRCALPHA)
    map_surface.fill(const.MAP_BG_COLOR)
    pygame.draw.rect(surface, const.MAP_BORDER_COLOR, map_display_rect, 1)

    map_world_scale_x = map_display_rect.width / (2 * world_game_bounds)
    map_world_scale_y = map_display_rect.height / (2 * world_game_bounds)

    def world_to_map(wx, wy):
        map_x = (map_display_rect.width / 2) + wx * map_world_scale_x
        map_y = (map_display_rect.height / 2) + wy * map_world_scale_y
        return int(map_x), int(map_y)

    sf_p1_map = world_to_map(start_finish_line_coords[0][0], start_finish_line_coords[0][1])
    sf_p2_map = world_to_map(start_finish_line_coords[1][0], start_finish_line_coords[1][1])
    pygame.draw.line(map_surface, const.START_FINISH_LINE_COLOR, sf_p1_map, sf_p2_map, 1)

    for i, cp in enumerate(checkpoints):
        map_x, map_y = world_to_map(cp.world_x, cp.world_y)
        is_next = (i == next_checkpoint_index_on_list)
        color_to_use = cp.color
        if is_next and not cp.is_gate:
            color_to_use = const.NEXT_CHECKPOINT_INDICATOR_COLOR
        if 0 <= map_x <= map_display_rect.width and 0 <= map_y <= map_display_rect.height:
            pygame.draw.circle(map_surface, color_to_use, (map_x, map_y), const.MAP_CHECKPOINT_MARKER_RADIUS)
            if not cp.is_gate:
                pygame.draw.circle(map_surface, const.BLACK, (map_x, map_y), const.MAP_CHECKPOINT_MARKER_RADIUS, 1)

    for mud in mud_patches: # MudPatch has .size
        map_x, map_y = world_to_map(mud.world_x, mud.world_y)
        map_radius = max(1, int((mud.size / 2.0) * map_world_scale_x))
        if 0 <= map_x <= map_display_rect.width and 0 <= map_y <= map_display_rect.height:
            pygame.draw.circle(map_surface, const.DARK_MUD_COLOR, (map_x, map_y), map_radius)

    if ramps_list: # Ramp has .diameter
        for ramp in ramps_list:
            map_x, map_y = world_to_map(ramp.world_x, ramp.world_y)
            map_ramp_size = max(1, int((ramp.diameter / 2.0) * map_world_scale_x))
            if 0 <= map_x <= map_display_rect.width and 0 <= map_y <= map_display_rect.height:
                pygame.draw.rect(map_surface, const.RAMP_COLOR, (map_x - map_ramp_size//2, map_y - map_ramp_size//2, map_ramp_size, map_ramp_size))

    if visual_hills_list: # VisualHill has .diameter
        for hill in visual_hills_list:
            map_x, map_y = world_to_map(hill.world_x, hill.world_y)
            map_radius = max(1, int((hill.diameter / 2.0) * map_world_scale_x))
            if 0 <= map_x <= map_display_rect.width and 0 <= map_y <= map_display_rect.height:
                hill_map_color = (*const.HILL_COLOR_NO_GRASS[:3], 100)
                pygame.draw.circle(map_surface, hill_map_color, (map_x, map_y), map_radius)
                pygame.draw.circle(map_surface, const.DARK_HILL_COLOR, (map_x, map_y), map_radius, 1)

    car_map_x, car_map_y = world_to_map(player_car.world_x, player_car.world_y)
    if 0 <= car_map_x <= map_display_rect.width and 0 <= car_map_y <= map_display_rect.height:
        car_angle_rad = deg_to_rad(player_car.heading)
        p1 = (car_map_x + math.cos(car_angle_rad) * const.MAP_CAR_MARKER_SIZE, car_map_y + math.sin(car_angle_rad) * const.MAP_CAR_MARKER_SIZE)
        p2 = (car_map_x + math.cos(car_angle_rad + 2.356) * const.MAP_CAR_MARKER_SIZE * 0.6, car_map_y + math.sin(car_angle_rad + 2.356) * const.MAP_CAR_MARKER_SIZE * 0.6)
        p3 = (car_map_x + math.cos(car_angle_rad - 2.356) * const.MAP_CAR_MARKER_SIZE * 0.6, car_map_y + math.sin(car_angle_rad - 2.356) * const.MAP_CAR_MARKER_SIZE * 0.6)
        try: pygame.draw.polygon(map_surface, const.MAP_CAR_COLOR, [(int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (int(p3[0]), int(p3[1]))])
        except ValueError: pygame.draw.circle(map_surface, const.MAP_CAR_COLOR, (car_map_x, car_map_y), 2)

    for ai_car in ai_cars:
        ai_car_map_x, ai_car_map_y = world_to_map(ai_car.world_x, ai_car.world_y)
        if 0 <= ai_car_map_x <= map_display_rect.width and 0 <= ai_car_map_y <= map_display_rect.height:
            ai_angle_rad = deg_to_rad(ai_car.heading)
            map_marker_color = ai_car.color
            ai_p1 = (ai_car_map_x + math.cos(ai_angle_rad) * const.MAP_CAR_MARKER_SIZE, ai_car_map_y + math.sin(ai_angle_rad) * const.MAP_CAR_MARKER_SIZE)
            ai_p2 = (ai_car_map_x + math.cos(ai_angle_rad + 2.356) * const.MAP_CAR_MARKER_SIZE * 0.6, ai_car_map_y + math.sin(ai_angle_rad + 2.356) * const.MAP_CAR_MARKER_SIZE * 0.6)
            ai_p3 = (ai_car_map_x + math.cos(ai_angle_rad - 2.356) * const.MAP_CAR_MARKER_SIZE * 0.6, ai_car_map_y + math.sin(ai_angle_rad - 2.356) * const.MAP_CAR_MARKER_SIZE * 0.6)
            try: pygame.draw.polygon(map_surface, map_marker_color, [(int(ai_p1[0]),int(ai_p1[1])), (int(ai_p2[0]),int(ai_p2[1])), (int(ai_p3[0]),int(ai_p3[1]))])
            except ValueError: pygame.draw.circle(map_surface, map_marker_color, (ai_car_map_x, ai_car_map_y), 2)

    surface.blit(map_surface, map_display_rect.topleft)

def draw_button(surface, rect, text, font, button_base_color, text_color, button_hover_color):
    mouse_pos = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mouse_pos)
    color_to_use = button_hover_color if hovered else button_base_color
    pygame.draw.rect(surface, color_to_use, rect, border_radius=5)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)
    return hovered

def format_time(seconds):
    if seconds < 0: return "00:00.00"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    hunds = int((seconds * 100) % 100)
    return f"{mins:02}:{secs:02}.{hunds:02}"

def draw_rpm_gauge(surface, rpm, max_rpm_val, idle_rpm_val, display_rect, font_to_use):
    pygame.draw.rect(surface, const.PEDAL_BG_COLOR, display_rect)
    pygame.draw.rect(surface, const.BLACK, display_rect, 1)
    rpm_range = max_rpm_val - idle_rpm_val
    rpm_ratio = 0.0
    if rpm_range > 0: rpm_ratio = clamp((rpm - idle_rpm_val) / rpm_range, 0.0, 1.0)
    bar_width = int(display_rect.width * rpm_ratio)
    bar_rect = pygame.Rect(display_rect.left, display_rect.top, bar_width, display_rect.height)
    bar_color = const.RPM_BAR_COLOR
    if rpm_ratio > 0.9: bar_color = const.RPM_BAR_MAX_COLOR
    elif rpm_ratio > 0.7: bar_color = const.RPM_BAR_HIGH_COLOR
    pygame.draw.rect(surface, bar_color, bar_rect)

def draw_pedal_indicator(surface, value, display_rect, active_color, label, font_to_use):
    pygame.draw.rect(surface, const.PEDAL_BG_COLOR, display_rect)
    fill_height = int(display_rect.height * value)
    fill_rect = pygame.Rect(display_rect.left, display_rect.bottom - fill_height, display_rect.width, fill_height)
    pygame.draw.rect(surface, active_color, fill_rect)
    pygame.draw.rect(surface, const.BLACK, display_rect, 1)

def draw_handbrake_indicator(surface, active, position_tuple, radius, font_to_use):
    color_to_use = const.HANDBRAKE_INDICATOR_COLOR if active else const.GRAY
    pygame.draw.circle(surface, color_to_use, position_tuple, radius)
    pygame.draw.circle(surface, const.BLACK, position_tuple, radius, 1)