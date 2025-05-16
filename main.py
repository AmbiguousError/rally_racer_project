import pygame
import random
import math
import time
import numpy as np
from collections import deque
from enum import Enum, auto

# Import from your new modules
import constants as const
from utils import (
    deg_to_rad, rad_to_deg, angle_difference, normalize_angle,
    lerp, distance_sq, clamp, check_line_crossing
)
from sound_manager import generate_sound_array
from course_generator import (
    generate_random_checkpoints, generate_random_mud_patches,
    generate_random_ramps, is_too_close, generate_random_hills
)
from ui_elements import (
    draw_button, draw_rpm_gauge, draw_pedal_indicator,
    draw_handbrake_indicator, draw_map, draw_scrolling_track, format_time
)

# Import classes
from classes import Car, Particle, DustParticle, MudParticle, Ramp, MudPatch, Checkpoint


# GameState Enum
class GameState(Enum):
    SETUP = auto(); COUNTDOWN = auto(); RACING = auto(); FINISHED = auto()

# --- Main Game Function ---
def main():
    # --- Pygame and Mixer Initialization ---
    pygame.mixer.pre_init(const.SAMPLE_RATE, -16, 2, 512)
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((const.SCREEN_WIDTH, const.SCREEN_HEIGHT))
    pygame.display.set_caption("Rally Racer")
    clock = pygame.time.Clock()

    # --- Tire Tracks Surface ---
    world_surface_size = (const.WORLD_BOUNDS * 2, const.WORLD_BOUNDS * 2)
    try:
        tire_tracks_surface = pygame.Surface(world_surface_size, pygame.SRCALPHA)
        tire_tracks_surface.fill((0, 0, 0, 0)) 
    except pygame.error as e:
        print(f"Error creating tire_tracks_surface (possibly too large for hardware): {e}")
        print(f"Attempted size: {world_surface_size}")
        tire_tracks_surface = pygame.Surface((const.SCREEN_WIDTH, const.SCREEN_HEIGHT), pygame.SRCALPHA)
        tire_tracks_surface.fill((0,0,0,0))


    font = pygame.font.Font(None, 40)
    title_font = pygame.font.Font(None, 72)
    lap_font = pygame.font.Font(None, 36)
    button_font = pygame.font.Font(None, 36)
    ui_font_small = pygame.font.Font(None, 24)
    option_font = pygame.font.Font(None, 40)
    countdown_font = pygame.font.Font(None, 150)

    # --- Sound Loading/Generation ---
    try:
        beep_high_arr = generate_sound_array(const.BEEP_FREQ_HIGH, const.BEEP_DURATION_MS, waveform='sine', sample_rate=const.SAMPLE_RATE)
        beep_low_arr = generate_sound_array(const.BEEP_FREQ_LOW, const.BEEP_DURATION_MS, waveform='sine', sample_rate=const.SAMPLE_RATE)
        skid_arr = generate_sound_array(0, const.SKID_DURATION_MS, waveform='noise', sample_rate=const.SAMPLE_RATE)
        engine_arr = generate_sound_array(const.ENGINE_BASE_FREQ, 1000, waveform='engine', sample_rate=const.SAMPLE_RATE)

        beep_high_sound = pygame.mixer.Sound(buffer=beep_high_arr)
        beep_low_sound = pygame.mixer.Sound(buffer=beep_low_arr)
        skid_sound = pygame.mixer.Sound(buffer=skid_arr)
        engine_sound = pygame.mixer.Sound(buffer=engine_arr)

        skid_sound.set_volume(const.SKID_VOL)
        engine_channel = pygame.mixer.Channel(0)
        skid_channel = pygame.mixer.Channel(1)
        sfx_channel = pygame.mixer.Channel(2)
        sounds_loaded = True
    except Exception as e:
        print(f"Error initializing sound: {e}")
        sounds_loaded = False
        beep_high_sound = beep_low_sound = skid_sound = engine_sound = None
        engine_channel = skid_channel = sfx_channel = None

    RPM_GAUGE_RECT_LOCAL = pygame.Rect(20, const.SCREEN_HEIGHT - 110, const.RPM_GAUGE_WIDTH, const.RPM_GAUGE_HEIGHT)
    ACCEL_PEDAL_RECT_LOCAL = pygame.Rect(230, const.SCREEN_HEIGHT - 110, const.ACCEL_PEDAL_WIDTH, const.ACCEL_PEDAL_HEIGHT)
    BRAKE_PEDAL_RECT_LOCAL = pygame.Rect(280, const.SCREEN_HEIGHT - 110, const.BRAKE_PEDAL_WIDTH, const.BRAKE_PEDAL_HEIGHT)
    HANDBRAKE_INDICATOR_POS_LOCAL = (const.HANDBRAKE_INDICATOR_POS_X_OFFSET, const.SCREEN_HEIGHT - 80 + const.HANDBRAKE_INDICATOR_RADIUS - ACCEL_PEDAL_RECT_LOCAL.height // 2)
    MAP_RECT_LOCAL = pygame.Rect(const.SCREEN_WIDTH - const.MAP_WIDTH - const.MAP_MARGIN, const.MAP_MARGIN, const.MAP_WIDTH, const.MAP_HEIGHT)

    player_car = Car(const.CENTER_X, const.CENTER_Y)
    ai_cars = []
    mud_patches = []; checkpoints = []; course_checkpoints_coords = []; ramps = []
    visual_hills = []

    selected_laps = const.DEFAULT_RACE_LAPS
    top_speed_options = [50, 75, 100, 125, 150, 200, 250]
    selected_speed_index = const.DEFAULT_TOP_SPEED_INDEX
    grip_options = [50, 75, 100, 125, 150, 200, 250]
    selected_grip_index = const.DEFAULT_GRIP_INDEX
    selected_num_checkpoints = const.DEFAULT_NUM_CHECKPOINTS
    max_checkpoints = const.MAX_CHECKPOINTS_ALLOWED
    selected_num_ai = const.DEFAULT_NUM_AI
    max_ai = const.MAX_AI_OPPONENTS
    difficulty_options = ["Easy", "Medium", "Hard", "Random"]
    selected_difficulty_index = const.DEFAULT_DIFFICULTY_INDEX

    laps_label_pos = (const.OPTION_LABEL_X, const.OPTION_Y_START + 0 * const.ROW_SPACING)
    laps_value_pos = (const.OPTION_VALUE_X, const.OPTION_Y_START + 0 * const.ROW_SPACING)
    laps_minus_rect = pygame.Rect(const.OPTION_MINUS_X, const.OPTION_Y_START + 0 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    laps_plus_rect = pygame.Rect(const.OPTION_PLUS_X, const.OPTION_Y_START + 0 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    speed_label_pos = (const.OPTION_LABEL_X, const.OPTION_Y_START + 1 * const.ROW_SPACING)
    speed_value_pos = (const.OPTION_VALUE_X, const.OPTION_Y_START + 1 * const.ROW_SPACING)
    speed_minus_rect = pygame.Rect(const.OPTION_MINUS_X, const.OPTION_Y_START + 1 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    speed_plus_rect = pygame.Rect(const.OPTION_PLUS_X, const.OPTION_Y_START + 1 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    grip_label_pos = (const.OPTION_LABEL_X, const.OPTION_Y_START + 2 * const.ROW_SPACING)
    grip_value_pos = (const.OPTION_VALUE_X, const.OPTION_Y_START + 2 * const.ROW_SPACING)
    grip_minus_rect = pygame.Rect(const.OPTION_MINUS_X, const.OPTION_Y_START + 2 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    grip_plus_rect = pygame.Rect(const.OPTION_PLUS_X, const.OPTION_Y_START + 2 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    checkpoints_label_pos = (const.OPTION_LABEL_X, const.OPTION_Y_START + 3 * const.ROW_SPACING)
    checkpoints_value_pos = (const.OPTION_VALUE_X, const.OPTION_Y_START + 3 * const.ROW_SPACING)
    checkpoints_minus_rect = pygame.Rect(const.OPTION_MINUS_X, const.OPTION_Y_START + 3 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    checkpoints_plus_rect = pygame.Rect(const.OPTION_PLUS_X, const.OPTION_Y_START + 3 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    ai_label_pos = (const.OPTION_LABEL_X, const.OPTION_Y_START + 4 * const.ROW_SPACING)
    ai_value_pos = (const.OPTION_VALUE_X, const.OPTION_Y_START + 4 * const.ROW_SPACING)
    ai_minus_rect = pygame.Rect(const.OPTION_MINUS_X, const.OPTION_Y_START + 4 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    ai_plus_rect = pygame.Rect(const.OPTION_PLUS_X, const.OPTION_Y_START + 4 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    difficulty_label_pos = (const.OPTION_LABEL_X, const.OPTION_Y_START + 5 * const.ROW_SPACING)
    difficulty_value_pos = (const.OPTION_VALUE_X, const.OPTION_Y_START + 5 * const.ROW_SPACING)
    difficulty_minus_rect = pygame.Rect(const.OPTION_MINUS_X, const.OPTION_Y_START + 5 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    difficulty_plus_rect = pygame.Rect(const.OPTION_PLUS_X, const.OPTION_Y_START + 5 * const.ROW_SPACING - const.OPTION_BUTTON_HEIGHT//2, const.OPTION_BUTTON_WIDTH, const.OPTION_BUTTON_HEIGHT)
    start_button_rect = pygame.Rect(const.CENTER_X - const.SETUP_BUTTON_WIDTH // 2, const.OPTION_Y_START + 6.5 * const.ROW_SPACING, const.SETUP_BUTTON_WIDTH, const.SETUP_BUTTON_HEIGHT)
    new_race_button_rect = pygame.Rect(const.CENTER_X - const.SETUP_BUTTON_WIDTH // 2, const.SCREEN_HEIGHT * 0.7, const.SETUP_BUTTON_WIDTH, const.SETUP_BUTTON_HEIGHT)

    game_state = GameState.SETUP
    total_laps = selected_laps
    player_current_lap = 0; player_next_checkpoint_index = -1
    player_lap_times = []; player_lap_start_time = 0.0
    player_race_started = False; player_race_finished = False
    player_last_line_crossing_time = -const.LINE_CROSSING_DEBOUNCE
    player_final_total_time = 0.0
    countdown_timer = 0; countdown_stage = 0
    world_offset_x = 0.0; world_offset_y = 0.0; course_generated = False
    total_race_start_time = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0; dt = min(dt, 0.1)
        if dt <= 0: dt = 1/60.0
        current_time_s = pygame.time.get_ticks() / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if game_state == GameState.SETUP:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # <<< DEBUG PRINT STATEMENTS ADDED HERE >>>
                    print(f"DEBUG: Mouse clicked at: {event.pos}") 

                    print(f"DEBUG: Laps Minus Rect: {laps_minus_rect} | Collides: {laps_minus_rect.collidepoint(event.pos)}")
                    print(f"DEBUG: Laps Plus Rect: {laps_plus_rect} | Collides: {laps_plus_rect.collidepoint(event.pos)}")
                    print(f"DEBUG: Speed Minus Rect: {speed_minus_rect} | Collides: {speed_minus_rect.collidepoint(event.pos)}")
                    print(f"DEBUG: Speed Plus Rect: {speed_plus_rect} | Collides: {speed_plus_rect.collidepoint(event.pos)}")
                    # Add similar prints for other option buttons if needed

                    if laps_minus_rect.collidepoint(event.pos):
                        print("DEBUG: Laps Minus Button Action!")
                        selected_laps = max(1, selected_laps - 1)
                    elif laps_plus_rect.collidepoint(event.pos):
                        print("DEBUG: Laps Plus Button Action!")
                        selected_laps = min(10, selected_laps + 1)
                    elif speed_minus_rect.collidepoint(event.pos):
                        print("DEBUG: Speed Minus Button Action!")
                        selected_speed_index = max(0, selected_speed_index - 1)
                    elif speed_plus_rect.collidepoint(event.pos):
                        print("DEBUG: Speed Plus Button Action!")
                        selected_speed_index = min(len(top_speed_options) - 1, selected_speed_index + 1)
                    elif grip_minus_rect.collidepoint(event.pos):
                        print("DEBUG: Grip Minus Button Action!")
                        selected_grip_index = max(0, selected_grip_index - 1)
                    elif grip_plus_rect.collidepoint(event.pos):
                        print("DEBUG: Grip Plus Button Action!")
                        selected_grip_index = min(len(grip_options) - 1, selected_grip_index + 1)
                    elif checkpoints_minus_rect.collidepoint(event.pos):
                        print("DEBUG: Checkpoints Minus Button Action!")
                        selected_num_checkpoints = max(1, selected_num_checkpoints - 1)
                    elif checkpoints_plus_rect.collidepoint(event.pos):
                        print("DEBUG: Checkpoints Plus Button Action!")
                        selected_num_checkpoints = min(max_checkpoints, selected_num_checkpoints + 1)
                    elif ai_minus_rect.collidepoint(event.pos):
                        print("DEBUG: AI Minus Button Action!")
                        selected_num_ai = max(0, selected_num_ai - 1)
                    elif ai_plus_rect.collidepoint(event.pos):
                        print("DEBUG: AI Plus Button Action!")
                        selected_num_ai = min(max_ai, selected_num_ai + 1)
                    elif difficulty_minus_rect.collidepoint(event.pos):
                        print("DEBUG: Difficulty Minus Button Action!")
                        selected_difficulty_index = (selected_difficulty_index - 1 + len(difficulty_options)) % len(difficulty_options)
                    elif difficulty_plus_rect.collidepoint(event.pos):
                        print("DEBUG: Difficulty Plus Button Action!")
                        selected_difficulty_index = (selected_difficulty_index + 1) % len(difficulty_options)
                    # <<< END DEBUG PRINT STATEMENTS (for actions) >>>
                    elif start_button_rect.collidepoint(event.pos):
                        print("DEBUG: Start Race Button Action!")
                        if tire_tracks_surface:
                            tire_tracks_surface.fill((0, 0, 0, 0))
                        player_car.apply_setup(top_speed_options[selected_speed_index], grip_options[selected_grip_index])
                        ai_cars = []
                        for i in range(selected_num_ai):
                            ai_unique_color = const.AI_AVAILABLE_COLORS[i % len(const.AI_AVAILABLE_COLORS)]
                            ai_car_instance = Car(0, 0, is_ai=True, unique_body_color=ai_unique_color)
                            ai_car_instance.apply_setup(top_speed_options[selected_speed_index], grip_options[selected_grip_index])
                            ai_car_instance.apply_ai_difficulty(selected_difficulty_index, difficulty_options)
                            ai_cars.append(ai_car_instance)
                        course_checkpoints_coords = generate_random_checkpoints(selected_num_checkpoints, [], const.START_FINISH_LINE)
                        checkpoints = [Checkpoint(const.START_FINISH_LINE[0][0], const.START_FINISH_LINE[0][1], -1, is_gate=True),
                                       Checkpoint(const.START_FINISH_LINE[1][0], const.START_FINISH_LINE[1][1], -1, is_gate=True)]
                        for i_cp, (cx_cp, cy_cp) in enumerate(course_checkpoints_coords): checkpoints.append(Checkpoint(cx_cp, cy_cp, i_cp))
                        all_obstacles_for_gen = list(checkpoints)
                        mud_patches = generate_random_mud_patches(const.NUM_MUD_PATCHES, all_obstacles_for_gen, const.START_FINISH_LINE, course_checkpoints_coords)
                        all_obstacles_for_gen.extend(mud_patches)
                        ramps = generate_random_ramps(const.NUM_RAMPS, all_obstacles_for_gen, const.START_FINISH_LINE)
                        all_obstacles_for_gen.extend(ramps)
                        if hasattr(const, 'NUM_VISUAL_HILLS') and const.NUM_VISUAL_HILLS > 0:
                            visual_hills = generate_random_hills(
                                const.NUM_VISUAL_HILLS, all_obstacles_for_gen,
                                const.START_FINISH_LINE, course_checkpoints_coords
                            )
                        else: visual_hills = []
                        course_generated = True
                        game_state = GameState.COUNTDOWN; countdown_timer = current_time_s + 3.0; countdown_stage = 1
                        player_start_world_x, player_start_world_y = 0.0, 20.0
                        player_car.reset_position(player_start_world_x, player_start_world_y)
                        for i, ai_car_instance in enumerate(ai_cars):
                            row_num = (i // 2) + 1; col_num = i % 2
                            ai_start_x = (col_num - 0.5) * player_car.collision_radius * 2.5
                            ai_start_y = player_start_world_y - (row_num * player_car.collision_radius * 3.0)
                            ai_car_instance.reset_position(ai_start_x, ai_start_y)
                        world_offset_x = player_car.world_x; world_offset_y = player_car.world_y
                        if sounds_loaded:
                            if engine_channel: engine_channel.stop()
                            if skid_channel: skid_channel.stop()
                            if sfx_channel and beep_high_sound: sfx_channel.play(beep_high_sound)
                    # else: # To see if click didn't match any button
                    #     print("DEBUG: Click in SETUP state did not match any button rect.")

            elif game_state == GameState.FINISHED:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if new_race_button_rect.collidepoint(event.pos):
                        game_state = GameState.SETUP; course_generated = False; visual_hills = []
                        if sounds_loaded and engine_channel and skid_channel:
                            engine_channel.stop(); skid_channel.stop()

        if game_state == GameState.SETUP:
             pass
        elif game_state == GameState.COUNTDOWN:
            time_left = countdown_timer - current_time_s; new_stage = 0
            if time_left > 2: new_stage = 1
            elif time_left > 1: new_stage = 2
            elif time_left > 0: new_stage = 3
            else: new_stage = 4
            if new_stage != countdown_stage:
                countdown_stage = new_stage
                if sounds_loaded and sfx_channel:
                    if countdown_stage <=3 and countdown_stage >=2 :
                        if beep_high_sound: sfx_channel.play(beep_high_sound)
                    elif countdown_stage == 4:
                        if beep_low_sound: sfx_channel.play(beep_low_sound)
                        game_state = GameState.RACING; total_laps = selected_laps
                        player_current_lap = 0; player_next_checkpoint_index = -1; player_lap_times = []
                        player_lap_start_time = 0.0; player_race_started = False; player_race_finished = False
                        player_last_line_crossing_time = -const.LINE_CROSSING_DEBOUNCE; player_final_total_time = 0.0
                        for ai in ai_cars:
                            ai.race_started = False; ai.current_lap = 0; ai.lap_times = []
                            ai.ai_target_checkpoint_index = 0; ai.last_line_crossing_time = -const.LINE_CROSSING_DEBOUNCE
                            ai.race_finished_for_car = False
                        total_race_start_time = current_time_s
                        if sounds_loaded and engine_sound and engine_channel:
                            engine_channel.play(engine_sound, loops=-1)
                            engine_channel.set_volume(const.ENGINE_MIN_VOL)
            world_offset_x = player_car.world_x
            world_offset_y = player_car.world_y

        elif game_state == GameState.RACING:
            keys = pygame.key.get_pressed()
            if not player_race_finished:
                 player_car.set_controls(
                    1.0 if keys[pygame.K_UP] or keys[pygame.K_w] else 0.0,
                    1.0 if keys[pygame.K_DOWN] or keys[pygame.K_s] else 0.0,
                    (1.0 if keys[pygame.K_RIGHT] or keys[pygame.K_d] else 0.0) - (1.0 if keys[pygame.K_LEFT] or keys[pygame.K_a] else 0.0),
                    1.0 if keys[pygame.K_SPACE] else 0.0)
            else: player_car.set_controls(0,0.2,0,0)

            for ai in ai_cars:
                ai.update_ai(dt, checkpoints, len(course_checkpoints_coords), total_laps, current_time_s)

            cars_to_update_physics = [player_car] + ai_cars
            for car_obj in cars_to_update_physics:
                car_obj.on_mud = False
                car_world_rect = car_obj.get_world_collision_rect()

                for mud in mud_patches:
                    if car_world_rect.colliderect(mud.rect) and mud.check_collision((car_obj.world_x, car_obj.world_y)):
                        car_obj.on_mud = True; break

                if not car_obj.is_airborne:
                    for ramp_obj in ramps:
                        if ramp_obj.check_collision(car_world_rect):
                            if car_obj.speed > car_obj.max_car_speed * const.MIN_JUMP_SPEED_FACTOR:
                                car_obj.trigger_jump(); break
                
                collided_with_a_crest_this_frame = False
                if not car_obj.is_airborne and visual_hills:
                    for hill in visual_hills:
                        if hill.check_collision(car_world_rect):
                            if hill.check_crest_collision(car_obj.world_x, car_obj.world_y):
                                collided_with_a_crest_this_frame = True
                                if car_obj.last_collided_hill_crest != hill:
                                    min_speed_for_hill_jump = car_obj.max_car_speed * const.MIN_JUMP_SPEED_FACTOR
                                    if car_obj.speed > min_speed_for_hill_jump:
                                        car_obj.trigger_jump()
                                        car_obj.last_collided_hill_crest = hill
                                        break 
                                break 
                            elif car_obj.last_collided_hill_crest == hill:
                                 car_obj.last_collided_hill_crest = None 
                        elif car_obj.last_collided_hill_crest == hill:
                            car_obj.last_collided_hill_crest = None
                                
                car_obj.update(dt)
                if tire_tracks_surface and hasattr(car_obj, 'leave_tire_tracks'):
                    car_obj.leave_tire_tracks(tire_tracks_surface, const.WORLD_BOUNDS)

            for i in range(len(cars_to_update_physics)):
                for j in range(i + 1, len(cars_to_update_physics)):
                    car1 = cars_to_update_physics[i]; car2 = cars_to_update_physics[j]
                    dist_x = car1.world_x - car2.world_x; dist_y = car1.world_y - car2.world_y
                    current_dist_sq = dist_x*dist_x + dist_y*dist_y
                    min_dist = car1.collision_radius + car2.collision_radius; min_dist_sq = min_dist*min_dist
                    if current_dist_sq < min_dist_sq and current_dist_sq > 1e-6:
                        current_dist = math.sqrt(current_dist_sq)
                        overlap = min_dist - current_dist
                        nx = dist_x / current_dist if current_dist != 0 else 1.0
                        ny = dist_y / current_dist if current_dist != 0 else 0.0
                        car1.resolve_collision_with(car2, nx, ny, overlap)

            world_offset_x = player_car.world_x; world_offset_y = player_car.world_y

            if sounds_loaded and engine_channel and skid_channel and skid_sound:
                is_skidding = (player_car.is_drifting or player_car.is_handbraking) and not player_car.is_airborne and player_car.speed > 10
                if is_skidding and not skid_channel.get_busy(): skid_channel.play(skid_sound, loops=-1)
                elif not is_skidding and skid_channel.get_busy(): skid_channel.stop()
                rpm_ratio_denom = (const.MAX_RPM - const.IDLE_RPM)
                rpm_ratio = clamp((player_car.rpm - const.IDLE_RPM) / rpm_ratio_denom if rpm_ratio_denom > 0 else 0, 0.0, 1.0)
                throttle_influence = 0.3 + 0.7 * player_car.throttle_input
                rpm_influence = 0.5 + 0.5 * rpm_ratio
                target_volume = const.ENGINE_MIN_VOL + (const.ENGINE_MAX_VOL - const.ENGINE_MIN_VOL) * throttle_influence * rpm_influence
                engine_channel.set_volume(clamp(target_volume, 0.0, 1.0))

            if not player_race_finished:
                car_pos = (player_car.world_x, player_car.world_y); car_prev_pos = (player_car.prev_world_x, player_car.prev_world_y)
                num_actual_cps = len(course_checkpoints_coords)
                if player_race_started and 0 <= player_next_checkpoint_index < num_actual_cps:
                    target_cp = checkpoints[player_next_checkpoint_index + 2]
                    if distance_sq(car_pos, (target_cp.world_x, target_cp.world_y)) < const.CHECKPOINT_ROUNDING_RADIUS**2:
                        player_next_checkpoint_index += 1
                if current_time_s - player_last_line_crossing_time > const.LINE_CROSSING_DEBOUNCE:
                    if distance_sq(car_prev_pos, car_pos) > 0.1:
                        if check_line_crossing(car_prev_pos, car_pos, const.START_FINISH_LINE[0], const.START_FINISH_LINE[1]):
                            player_last_line_crossing_time = current_time_s
                            if not player_race_started:
                                player_race_started = True; player_current_lap = 1; player_next_checkpoint_index = 0
                                player_lap_start_time = current_time_s; player_lap_times = []
                            elif player_next_checkpoint_index >= num_actual_cps:
                                lap_time = current_time_s - player_lap_start_time; player_lap_times.append(lap_time)
                                if player_current_lap >= total_laps:
                                    player_race_finished = True; player_final_total_time = current_time_s - total_race_start_time
                                    game_state = GameState.FINISHED
                                    if sounds_loaded and engine_channel and skid_channel:
                                        engine_channel.stop(); skid_channel.stop()
                                else:
                                    player_current_lap += 1; player_next_checkpoint_index = 0; player_lap_start_time = current_time_s

        draw_scrolling_track(screen, world_offset_x, world_offset_y, visual_hills)
        if tire_tracks_surface and (game_state == GameState.RACING or game_state == GameState.COUNTDOWN or game_state == GameState.FINISHED):
            src_rect_x = (world_offset_x - const.CENTER_X) + const.WORLD_BOUNDS
            src_rect_y = (world_offset_y - const.CENTER_Y) + const.WORLD_BOUNDS
            visible_world_area_on_tracks_surface = pygame.Rect(src_rect_x, src_rect_y, const.SCREEN_WIDTH, const.SCREEN_HEIGHT)
            screen.blit(tire_tracks_surface, (0,0), area=visible_world_area_on_tracks_surface)

        if game_state == GameState.SETUP:
            title_surf = title_font.render("Race Setup", True, const.WHITE)
            screen.blit(title_surf, (const.CENTER_X - title_surf.get_width()//2, const.SCREEN_HEIGHT * 0.08))
            laps_label_surf = option_font.render("Laps:", True, const.WHITE); screen.blit(laps_label_surf, laps_label_pos)
            laps_value_surf = option_font.render(str(selected_laps), True, const.WHITE); screen.blit(laps_value_surf, laps_value_pos)
            draw_button(screen, laps_minus_rect, "-", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            draw_button(screen, laps_plus_rect, "+", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            speed_label_surf = option_font.render("Top Speed:", True, const.WHITE); screen.blit(speed_label_surf, speed_label_pos)
            speed_value_surf = option_font.render(f"{top_speed_options[selected_speed_index]}%", True, const.WHITE); screen.blit(speed_value_surf, speed_value_pos)
            draw_button(screen, speed_minus_rect, "-", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            draw_button(screen, speed_plus_rect, "+", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            grip_label_surf = option_font.render("Grip:", True, const.WHITE); screen.blit(grip_label_surf, grip_label_pos)
            grip_value_surf = option_font.render(f"{grip_options[selected_grip_index]}%", True, const.WHITE); screen.blit(grip_value_surf, grip_value_pos)
            draw_button(screen, grip_minus_rect, "-", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            draw_button(screen, grip_plus_rect, "+", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            cp_label_surf = option_font.render("Checkpoints:", True, const.WHITE); screen.blit(cp_label_surf, checkpoints_label_pos)
            cp_value_surf = option_font.render(str(selected_num_checkpoints), True, const.WHITE); screen.blit(cp_value_surf, checkpoints_value_pos)
            draw_button(screen, checkpoints_minus_rect, "-", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            draw_button(screen, checkpoints_plus_rect, "+", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            ai_label_surf = option_font.render("AI Opponents:", True, const.WHITE); screen.blit(ai_label_surf, ai_label_pos)
            ai_value_surf = option_font.render(str(selected_num_ai), True, const.WHITE); screen.blit(ai_value_surf, ai_value_pos)
            draw_button(screen, ai_minus_rect, "-", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            draw_button(screen, ai_plus_rect, "+", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            difficulty_label_surf = option_font.render("AI Difficulty:", True, const.WHITE); screen.blit(difficulty_label_surf, difficulty_label_pos)
            difficulty_value_surf = option_font.render(difficulty_options[selected_difficulty_index], True, const.WHITE); screen.blit(difficulty_value_surf, difficulty_value_pos)
            draw_button(screen, difficulty_minus_rect, "<", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            draw_button(screen, difficulty_plus_rect, ">", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            draw_button(screen, start_button_rect, "Start Race", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)
            if course_generated:
                draw_map(screen, player_car, ai_cars, mud_patches, checkpoints, -1, const.START_FINISH_LINE, MAP_RECT_LOCAL, const.WORLD_BOUNDS, ramps, visual_hills)

        elif game_state == GameState.COUNTDOWN:
            cam_offset_x_cd = world_offset_x; cam_offset_y_cd = world_offset_y
            player_car.screen_x = const.CENTER_X; player_car.screen_y = const.CENTER_Y
            player_car.rotate_and_position_shapes(); player_car.draw(screen, draw_shadow=True)
            for ai in ai_cars:
                ai.screen_x = const.CENTER_X + (ai.world_x - cam_offset_x_cd)
                ai.screen_y = const.CENTER_Y + (ai.world_y - cam_offset_y_cd)
                ai.rotate_and_position_shapes(); ai.draw(screen, draw_shadow=True)
            time_left = countdown_timer - current_time_s
            if time_left > 0:
                num_to_show = math.ceil(time_left)
                if num_to_show <= 3:
                    text_surf = countdown_font.render(str(num_to_show), True, const.WHITE)
                    screen.blit(text_surf, text_surf.get_rect(center=(const.CENTER_X, const.CENTER_Y - 50)))
            elif time_left <=0 and time_left > -0.5:
                go_text_surf = countdown_font.render("GO!", True, const.GREEN)
                screen.blit(go_text_surf, go_text_surf.get_rect(center=(const.CENTER_X, const.CENTER_Y - 50)))

        elif game_state == GameState.RACING:
            cam_offset_x_race = player_car.world_x; cam_offset_y_race = player_car.world_y
            player_car.draw_dust(screen, cam_offset_x_race, cam_offset_y_race)
            player_car.draw_mud_splash(screen, cam_offset_x_race, cam_offset_y_race)
            for ai in ai_cars:
                ai.draw_dust(screen, cam_offset_x_race, cam_offset_y_race)
                ai.draw_mud_splash(screen, cam_offset_x_race, cam_offset_y_race)
            for mud in mud_patches: mud.draw(screen, cam_offset_x_race, cam_offset_y_race)
            for ramp_obj in ramps: ramp_obj.draw(screen, cam_offset_x_race, cam_offset_y_race)
            if const.DEBUG_DRAW_RAMPS:
                for ramp_obj in ramps: ramp_obj.draw_debug(screen, cam_offset_x_race, cam_offset_y_race)
            sf_p1_screen = (int(const.START_FINISH_LINE[0][0] - cam_offset_x_race + const.CENTER_X), int(const.START_FINISH_LINE[0][1] - cam_offset_y_race + const.CENTER_Y))
            sf_p2_screen = (int(const.START_FINISH_LINE[1][0] - cam_offset_x_race + const.CENTER_X), int(const.START_FINISH_LINE[1][1] - cam_offset_y_race + const.CENTER_Y))
            pygame.draw.line(screen, const.START_FINISH_LINE_COLOR, sf_p1_screen, sf_p2_screen, const.START_FINISH_WIDTH)
            map_next_cp_idx = -1
            if player_race_started and not player_race_finished and 0 <= player_next_checkpoint_index < len(course_checkpoints_coords):
                map_next_cp_idx = player_next_checkpoint_index + 2
            for i, cp_obj in enumerate(checkpoints): cp_obj.draw(screen, cam_offset_x_race, cam_offset_y_race, (i == map_next_cp_idx))
            for ai in ai_cars:
                ai.screen_x = const.CENTER_X + (ai.world_x - cam_offset_x_race)
                ai.screen_y = const.CENTER_Y + (ai.world_y - cam_offset_y_race)
                ai.rotate_and_position_shapes(); ai.draw(screen)
            player_car.screen_x = const.CENTER_X; player_car.screen_y = const.CENTER_Y
            player_car.rotate_and_position_shapes(); player_car.draw(screen)
            speed_denom = player_car.max_car_speed if player_car.max_car_speed > 0 else 1.0
            base_kph = 160
            disp_kph = (player_car.max_car_speed / const.BASE_MAX_CAR_SPEED) * base_kph * (player_car.speed / player_car.max_car_speed if player_car.max_car_speed > 0 else 0)
            speed_txt_surf = font.render(f"Speed: {disp_kph:.0f} kph", True, const.WHITE); screen.blit(speed_txt_surf, (20, const.SCREEN_HEIGHT - 50))
            draw_rpm_gauge(screen, player_car.rpm, const.MAX_RPM, const.IDLE_RPM, RPM_GAUGE_RECT_LOCAL, ui_font_small)
            draw_pedal_indicator(screen, player_car.throttle_input, ACCEL_PEDAL_RECT_LOCAL, const.ACCEL_PEDAL_COLOR, "Accel", ui_font_small)
            draw_pedal_indicator(screen, player_car.brake_input, BRAKE_PEDAL_RECT_LOCAL, const.BRAKE_PEDAL_COLOR, "Brake", ui_font_small)
            draw_handbrake_indicator(screen, player_car.is_handbraking, HANDBRAKE_INDICATOR_POS_LOCAL, const.HANDBRAKE_INDICATOR_RADIUS, ui_font_small)
            lap_disp_str = f"Lap: {player_current_lap}/{total_laps}" if player_race_started else "Cross Start Line"
            lap_txt_surf_ui = font.render(lap_disp_str, True, const.WHITE); screen.blit(lap_txt_surf_ui, (const.CENTER_X - lap_txt_surf_ui.get_width() // 2, 20))
            next_cp_disp_text = ""
            num_actual_cps_disp = len(course_checkpoints_coords)
            if player_race_started and not player_race_finished:
                if 0 <= player_next_checkpoint_index < num_actual_cps_disp: next_cp_disp_text = f"Next CP: {player_next_checkpoint_index + 1}/{num_actual_cps_disp}"
                else: next_cp_disp_text = "To Finish Line"
            next_cp_txt_surf = font.render(next_cp_disp_text, True, const.NEXT_CHECKPOINT_INDICATOR_COLOR); screen.blit(next_cp_txt_surf, (const.CENTER_X - next_cp_txt_surf.get_width() // 2, 60))
            total_tm_str = "00:00.00"; current_lp_str = "00:00.00"
            if player_race_started and not player_race_finished:
                total_tm_val = current_time_s - total_race_start_time; current_lp_val = current_time_s - player_lap_start_time
                total_tm_str = format_time(total_tm_val); current_lp_str = format_time(current_lp_val)
            elif player_race_finished :
                total_tm_str = format_time(player_final_total_time)
                if player_lap_times: current_lp_str = format_time(player_lap_times[-1])
            total_tm_txt_surf = font.render(f"Total: {total_tm_str}", True, const.WHITE); screen.blit(total_tm_txt_surf, (const.SCREEN_WIDTH - total_tm_txt_surf.get_width() - 20, 20))
            cur_lap_tm_txt_surf = font.render(f"Lap: {current_lp_str}", True, const.WHITE); screen.blit(cur_lap_tm_txt_surf, (const.SCREEN_WIDTH - cur_lap_tm_txt_surf.get_width() - 20, 60))
            y_lp_offset_ui = 100
            for i_lp, l_time_val in enumerate(reversed(player_lap_times)):
                if i_lp >= 5: break
                lap_n = len(player_lap_times) - i_lp; lp_time_surf_ui = lap_font.render(f"Lap {lap_n}: {format_time(l_time_val)}", True, const.GRAY)
                screen.blit(lp_time_surf_ui, (const.SCREEN_WIDTH - lp_time_surf_ui.get_width() - 20 , y_lp_offset_ui)); y_lp_offset_ui += 40
            draw_map(screen, player_car, ai_cars, mud_patches, checkpoints, map_next_cp_idx, const.START_FINISH_LINE, MAP_RECT_LOCAL, const.WORLD_BOUNDS, ramps, visual_hills)

        elif game_state == GameState.FINISHED:
            title_surf_fin = title_font.render("Race Finished!", True, const.WHITE); screen.blit(title_surf_fin, (const.CENTER_X - title_surf_fin.get_width()//2, const.SCREEN_HEIGHT * 0.1))
            total_time_surf_fin = font.render(f"Your Total Time: {format_time(player_final_total_time)}", True, const.WHITE); screen.blit(total_time_surf_fin, (const.CENTER_X - total_time_surf_fin.get_width()//2, const.SCREEN_HEIGHT * 0.20))
            y_lap_offset_fin = const.SCREEN_HEIGHT * 0.28
            lap_header_surf_fin = font.render("Your Lap Times:", True, const.WHITE)
            screen.blit(lap_header_surf_fin, (const.CENTER_X - lap_header_surf_fin.get_width()//2 , y_lap_offset_fin)); y_lap_offset_fin += 35
            for i_fin, l_time_fin in enumerate(player_lap_times):
                lap_num_fin = i_fin + 1; lap_time_surf_fin = lap_font.render(f"Lap {lap_num_fin}: {format_time(l_time_fin)}", True, const.WHITE)
                screen.blit(lap_time_surf_fin, (const.CENTER_X - lap_time_surf_fin.get_width()//2 , y_lap_offset_fin)); y_lap_offset_fin += 35
            y_lap_offset_fin += 15
            for i_ai_fin, ai_fin in enumerate(ai_cars):
                ai_header_surf_fin = font.render(f"AI {i_ai_fin+1} ({ai_fin.color}) Lap Times:", True, ai_fin.color if ai_fin.color else const.AI_CAR_BODY_COLOR)
                screen.blit(ai_header_surf_fin, (const.CENTER_X - ai_header_surf_fin.get_width()//2 , y_lap_offset_fin)); y_lap_offset_fin += 35
                if not ai_fin.lap_times and not ai_fin.race_finished_for_car:
                    no_time_surf_fin = lap_font.render("Did not finish", True, const.GRAY)
                    screen.blit(no_time_surf_fin, (const.CENTER_X - no_time_surf_fin.get_width()//2 , y_lap_offset_fin)); y_lap_offset_fin += 35
                elif ai_fin.race_finished_for_car:
                    ai_total_time = sum(ai_fin.lap_times)
                    ai_total_str = format_time(ai_total_time)
                    ai_total_surf = lap_font.render(f"Total: {ai_total_str}", True, const.WHITE)
                    screen.blit(ai_total_surf, (const.CENTER_X - ai_total_surf.get_width()//2, y_lap_offset_fin)); y_lap_offset_fin += 35
                for lap_idx_fin, l_time_ai_fin in enumerate(ai_fin.lap_times):
                    lap_num_ai_fin = lap_idx_fin + 1; lap_time_surf_ai_fin = lap_font.render(f"Lap {lap_num_ai_fin}: {format_time(l_time_ai_fin)}", True, const.WHITE)
                    screen.blit(lap_time_surf_ai_fin, (const.CENTER_X - lap_time_surf_ai_fin.get_width()//2 , y_lap_offset_fin)); y_lap_offset_fin += 35
                y_lap_offset_fin += 10
            new_race_button_rect.top = max(const.SCREEN_HEIGHT * 0.7, y_lap_offset_fin + 20)
            draw_button(screen, new_race_button_rect, "New Race Setup", button_font, const.BUTTON_COLOR, const.BUTTON_TEXT_COLOR, const.BUTTON_HOVER_COLOR)

        pygame.display.flip()

    pygame.mixer.quit()
    pygame.quit()

if __name__ == '__main__':
    main()