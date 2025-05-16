# rally_racer_project/classes/car.py
# This file defines the Car class for the Rally Racer game.

import pygame
import random
import math
from collections import deque

import constants as const # Ensure this imports your modified constants.py
from utils import (
    deg_to_rad, rad_to_deg, angle_difference, normalize_angle,
    lerp, distance_sq, clamp, check_line_crossing
)

from .particle import DustParticle, MudParticle

class Car:
    def __init__(self, x, y, is_ai=False, unique_body_color=None):
        # ... (all existing __init__ attributes should be here)
        self.screen_x = x
        self.screen_y = y
        self.world_x = 0.0
        self.world_y = 0.0
        self.prev_world_x = 0.0
        self.prev_world_y = 0.0

        self.heading = 180.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.speed = 0.0
        self.rpm = const.IDLE_RPM

        self.steering_input = 0.0
        self.throttle_input = 0.0
        self.brake_input = 0.0
        self.handbrake_input = 0.0

        self.is_drifting = False
        self.is_handbraking = False
        self.on_mud = False # This flag is set in main.py
        self.is_ai = is_ai
        self.is_airborne = False
        self.airborne_timer = 0.0
        self.initial_airborne_duration_this_jump = 0.0
        self.last_collided_hill_crest = None

        self.mass = 1.0

        if self.is_ai:
            self.color = unique_body_color if unique_body_color else const.AI_CAR_BODY_COLOR
        else:
            self.color = const.CAR_BODY_COLOR

        self.base_shape_body = [(22, 0), (20, -6), (10, -9), (-12, -9), (-20, -6), (-22, 0), (-20, 6), (-12, 9), (10, 9), (20, 6)]
        self.base_shape_window = [(12, -6), (8, -6), (-8, -6), (-10, -4), (-10, 4), (-8, 6), (8, 6), (12, 4)]
        self.base_shape_tires = [(12, -10, 6, 4), (12, 10, 6, 4), (-12, -10, 6, 4), (-12, 10, 6, 4)]
        self.base_shape_spoiler = [(-18, -12), (-15, -12), (-15, 12), (-18, 12)]

        self.rotated_shape_body = self.base_shape_body[:]
        self.rotated_shape_window = self.base_shape_window[:]
        self.rotated_shape_tires = [[(0,0)]*4 for _ in self.base_shape_tires]
        self.rotated_shape_spoiler = self.base_shape_spoiler[:]

        self.collision_radius = 18

        self.dust_particles = deque()
        self.time_since_last_dust = 0.0
        self.mud_particles = deque()
        self.time_since_last_mud = 0.0

        self.ai_target_checkpoint_index = 0
        self.current_lap = 0
        self.lap_times = []
        self.lap_start_time = 0.0
        self.race_started = False
        self.race_finished_for_car = False
        self.last_line_crossing_time = -const.LINE_CROSSING_DEBOUNCE

        self.ai_lookahead_factor = const.BASE_AI_LOOKAHEAD_FACTOR
        self.ai_turn_threshold = const.BASE_AI_TURN_THRESHOLD
        self.ai_brake_factor = const.BASE_AI_BRAKE_FACTOR
        self.ai_steer_sharpness = const.BASE_AI_STEER_SHARPNESS
        self.ai_throttle_control = const.BASE_AI_THROTTLE_CONTROL
        self.ai_mud_reaction = const.BASE_AI_MUD_REACTION

        self.max_car_speed = const.BASE_MAX_CAR_SPEED
        self.engine_power = const.BASE_ENGINE_POWER
        self.brake_power = const.BASE_BRAKE_POWER
        self.friction = const.BASE_FRICTION
        self.drift_friction_multiplier = const.BASE_DRIFT_FRICTION_MULTIPLIER
        self.handbrake_friction_multiplier = const.BASE_HANDBRAKE_FRICTION_MULTIPLIER
        self.handbrake_side_grip_loss = const.BASE_HANDBRAKE_SIDE_GRIP_LOSS
        self.drift_threshold_speed = self.max_car_speed * 0.25
        self.dust_spawn_speed_threshold = self.max_car_speed * 0.05
    
    # ... (apply_setup, apply_ai_difficulty, reset_position, set_controls, update_ai methods as before) ...
    def apply_setup(self, top_speed_percent, grip_percent):
        speed_scale = top_speed_percent / 100.0
        self.max_car_speed = const.BASE_MAX_CAR_SPEED * speed_scale
        self.engine_power = const.BASE_ENGINE_POWER * (speed_scale ** 1.5)
        self.brake_power = const.BASE_BRAKE_POWER * (speed_scale ** 1.5)
        grip_scale = grip_percent / 100.0
        grip_clamped = clamp(grip_scale, 0.5, 2.5)
        min_friction_val = 0.80; max_friction_val = 0.98
        self.friction = lerp(min_friction_val, max_friction_val, (grip_clamped - 0.5) / 2.0)
        self.drift_friction_multiplier = lerp(0.85, 0.99, (grip_clamped - 0.5) / 2.0)
        self.handbrake_friction_multiplier = lerp(0.75, 0.97, (grip_clamped - 0.5) / 2.0)
        self.handbrake_side_grip_loss = lerp(0.6, 0.98, (grip_clamped - 0.5) / 2.0)
        if self.is_ai:
            speed_variation_factor = random.uniform(0.95, 1.05)
            self.max_car_speed *= speed_variation_factor
            power_variation_factor = random.uniform(0.93, 1.07)
            self.engine_power *= power_variation_factor
        self.drift_threshold_speed = self.max_car_speed * 0.25
        self.dust_spawn_speed_threshold = self.max_car_speed * 0.05

    def apply_ai_difficulty(self, difficulty_index, difficulty_options):
        if not self.is_ai: return
        difficulty = difficulty_options[difficulty_index]
        if difficulty == "Easy":
            self.ai_throttle_control = 0.78; self.ai_brake_factor = 0.85
            self.ai_steer_sharpness = 0.45; self.ai_mud_reaction = 0.8
            self.ai_lookahead_factor = 1.0; self.ai_turn_threshold = 45
        elif difficulty == "Medium":
            self.ai_throttle_control = const.BASE_AI_THROTTLE_CONTROL * 0.90
            self.ai_brake_factor = const.BASE_AI_BRAKE_FACTOR * 1.15
            self.ai_steer_sharpness = const.BASE_AI_STEER_SHARPNESS * 0.85
            self.ai_mud_reaction = const.BASE_AI_MUD_REACTION * 1.1
            self.ai_lookahead_factor = const.BASE_AI_LOOKAHEAD_FACTOR * 0.90
            self.ai_turn_threshold = const.BASE_AI_TURN_THRESHOLD + 8
        elif difficulty == "Hard":
            self.ai_throttle_control = 0.98; self.ai_brake_factor = 0.9
            self.ai_steer_sharpness = 0.9; self.ai_mud_reaction = 0.4
            self.ai_lookahead_factor = 1.8; self.ai_turn_threshold = 15
        elif difficulty == "Random":
            self.ai_throttle_control = clamp(random.gauss(const.BASE_AI_THROTTLE_CONTROL, const.BASE_AI_THROTTLE_CONTROL * const.AI_RANDOM_STD_DEV_FACTOR), 0.65, 1.0)
            self.ai_brake_factor = clamp(random.gauss(const.BASE_AI_BRAKE_FACTOR, const.BASE_AI_BRAKE_FACTOR * const.AI_RANDOM_STD_DEV_FACTOR), 0.5, 1.2)
            self.ai_steer_sharpness = clamp(random.gauss(const.BASE_AI_STEER_SHARPNESS, const.BASE_AI_STEER_SHARPNESS * const.AI_RANDOM_STD_DEV_FACTOR), 0.4, 1.0)
            self.ai_mud_reaction = clamp(random.gauss(const.BASE_AI_MUD_REACTION, const.BASE_AI_MUD_REACTION * const.AI_RANDOM_STD_DEV_FACTOR), 0.3, 0.9)
            self.ai_lookahead_factor = clamp(random.gauss(const.BASE_AI_LOOKAHEAD_FACTOR, const.BASE_AI_LOOKAHEAD_FACTOR * const.AI_RANDOM_STD_DEV_FACTOR), 0.9, 2.2)
            self.ai_turn_threshold = clamp(random.gauss(const.BASE_AI_TURN_THRESHOLD, const.BASE_AI_TURN_THRESHOLD * const.AI_RANDOM_STD_DEV_FACTOR), 10, 50)
        else: # Default Medium
            self.ai_throttle_control = const.BASE_AI_THROTTLE_CONTROL * 0.90
            self.ai_brake_factor = const.BASE_AI_BRAKE_FACTOR * 1.15
            self.ai_steer_sharpness = const.BASE_AI_STEER_SHARPNESS * 0.85
            self.ai_mud_reaction = const.BASE_AI_MUD_REACTION * 1.1
            self.ai_lookahead_factor = const.BASE_AI_LOOKAHEAD_FACTOR * 0.90
            self.ai_turn_threshold = const.BASE_AI_TURN_THRESHOLD + 8
        param_variation_range = 0.10
        self.ai_throttle_control = clamp(self.ai_throttle_control * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.60, 1.0)
        self.ai_brake_factor = clamp(self.ai_brake_factor * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.4, 1.3)
        self.ai_steer_sharpness = clamp(self.ai_steer_sharpness * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.3, 1.0)
        self.ai_lookahead_factor = clamp(self.ai_lookahead_factor * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.8, 2.5)
        self.ai_turn_threshold = clamp(self.ai_turn_threshold + random.uniform(-7, 7), 10, 55)
        self.ai_mud_reaction = clamp(self.ai_mud_reaction * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.2, 0.95)

    def reset_position(self, start_world_x=0.0, start_world_y=0.0):
        self.world_x = start_world_x; self.world_y = start_world_y
        self.prev_world_x = start_world_x; self.prev_world_y = start_world_y
        self.heading = 180.0
        self.velocity_x = 0.0; self.velocity_y = 0.0; self.speed = 0.0; self.rpm = const.IDLE_RPM
        self.steering_input = 0.0; self.throttle_input = 0.0; self.brake_input = 0.0; self.handbrake_input = 0.0
        self.dust_particles.clear(); self.mud_particles.clear()
        self.on_mud = False; self.is_drifting = False; self.is_handbraking = False
        self.is_airborne = False; self.airborne_timer = 0.0
        self.initial_airborne_duration_this_jump = 0.0
        self.last_collided_hill_crest = None
        self.ai_target_checkpoint_index = 0
        self.current_lap = 0; self.lap_times = []
        self.lap_start_time = 0.0; self.race_started = False
        self.race_finished_for_car = False; self.last_line_crossing_time = -const.LINE_CROSSING_DEBOUNCE

    def set_controls(self, throttle, brake, steer, handbrake):
        self.throttle_input = throttle; self.brake_input = brake; self.steering_input = steer; self.handbrake_input = handbrake

    def update_ai(self, dt, checkpoints, num_course_checkpoints, total_laps, current_time_s):
        # ... (AI logic as before) ...
        if self.race_finished_for_car:
            self.throttle_input = 0; self.brake_input = 0.5; self.steering_input = 0; return
        current_target_world_pos = None
        if not self.race_started:
            target_x_for_start_crossing = const.START_FINISH_LINE[0][0] - 50
            target_y_for_start_crossing = (const.START_FINISH_LINE[0][1] + const.START_FINISH_LINE[1][1]) / 2
            current_target_world_pos = (target_x_for_start_crossing, target_y_for_start_crossing)
        else:
            is_targeting_finish_for_lap = (self.ai_target_checkpoint_index >= num_course_checkpoints)
            if not is_targeting_finish_for_lap:
                actual_cp_list_index = self.ai_target_checkpoint_index + 2
                if 0 <= actual_cp_list_index < len(checkpoints):
                    target_cp_object = checkpoints[actual_cp_list_index]
                    current_target_world_pos = (target_cp_object.world_x, target_cp_object.world_y)
                    dist_sq_to_target = distance_sq((self.world_x, self.world_y), current_target_world_pos)
                    if dist_sq_to_target < (const.CHECKPOINT_ROUNDING_RADIUS * 1.5)**2:
                        self.ai_target_checkpoint_index += 1
                        if self.ai_target_checkpoint_index >= num_course_checkpoints:
                            is_targeting_finish_for_lap = True
                else: is_targeting_finish_for_lap = True
            if is_targeting_finish_for_lap:
                current_target_world_pos = (const.START_FINISH_LINE[0][0], (const.START_FINISH_LINE[0][1] + const.START_FINISH_LINE[1][1]) / 2)
        if current_time_s - self.last_line_crossing_time > const.LINE_CROSSING_DEBOUNCE:
            if distance_sq((self.prev_world_x, self.prev_world_y), (self.world_x, self.world_y)) > 0.1:
                crossed_line = check_line_crossing((self.prev_world_x, self.prev_world_y), (self.world_x, self.world_y), const.START_FINISH_LINE[0], const.START_FINISH_LINE[1])
                if crossed_line:
                    self.last_line_crossing_time = current_time_s
                    if not self.race_started:
                        self.race_started = True; self.current_lap = 1
                        self.ai_target_checkpoint_index = 0; self.lap_start_time = current_time_s
                    elif (self.ai_target_checkpoint_index >= num_course_checkpoints):
                        lap_time = current_time_s - self.lap_start_time; self.lap_times.append(lap_time)
                        if self.current_lap >= total_laps: self.race_finished_for_car = True
                        else:
                            self.current_lap += 1; self.ai_target_checkpoint_index = 0
                            self.lap_start_time = current_time_s
        if self.race_finished_for_car:
            self.throttle_input = 0; self.brake_input = 0.5; self.steering_input = 0; return
        if current_target_world_pos is None:
            self.throttle_input = 0; self.brake_input = 0.1; self.steering_input = 0; return
        dx = current_target_world_pos[0] - self.world_x; dy = current_target_world_pos[1] - self.world_y
        target_angle = rad_to_deg(math.atan2(dy, dx))
        angle_diff_to_current_target = angle_difference(target_angle, self.heading)
        steer = clamp(angle_diff_to_current_target * self.ai_steer_sharpness * 0.05, -1.0, 1.0)
        self.steering_input = steer
        throttle = self.ai_throttle_control; brake = 0.0
        abs_angle_to_target_for_throttle = abs(angle_diff_to_current_target)
        if abs_angle_to_target_for_throttle > self.ai_turn_threshold * 0.75:
            reduction_factor = clamp(abs_angle_to_target_for_throttle / 90.0, 0.0, 0.6)
            throttle *= (1.0 - reduction_factor)
        dist_to_target_current = math.sqrt(dx**2 + dy**2)
        needs_braking_for_cp_approach = False
        if self.race_started and not (not self.race_started and current_target_world_pos[0] == const.START_FINISH_LINE[0][0] - 50) :
            effective_speed_for_braking = self.speed
            brake_threshold_dist = effective_speed_for_braking * self.ai_brake_factor * 1.2
            if dist_to_target_current < brake_threshold_dist and effective_speed_for_braking > 15:
                needs_braking_for_cp_approach = True
                brake = self.ai_brake_factor * clamp(1.0 - (dist_to_target_current / brake_threshold_dist if brake_threshold_dist > 1e-3 else 1.0), 0.2, 0.8)
        if needs_braking_for_cp_approach: throttle *= 0.3
        if self.on_mud:
            throttle *= self.ai_mud_reaction
            brake = clamp(brake + 0.15, 0.0, 1.0)
        self.throttle_input = clamp(throttle, 0.0, 1.0); self.brake_input = clamp(brake, 0.0, 1.0)
        self.handbrake_input = 0.0

    def update(self, dt):
        # ... (physics update as before) ...
        if dt <= 0: return
        self.prev_world_x = self.world_x; self.prev_world_y = self.world_y
        self.is_handbraking = self.handbrake_input > 0.5

        if self.is_airborne:
            self.airborne_timer -= dt
            if self.airborne_timer <= 0:
                self.is_airborne = False
        
        current_turn_effectiveness = const.AIRBORNE_TURN_EFFECTIVENESS if self.is_airborne else const.MIN_TURN_EFFECTIVENESS
        speed_factor_denom = self.max_car_speed if self.max_car_speed > 0 else 1.0
        speed_factor_for_turning = current_turn_effectiveness + (1.0 - current_turn_effectiveness) * (1.0 - clamp(self.speed / speed_factor_denom, 0, 1))
        
        turn_amount = self.steering_input * const.CAR_TURN_RATE * speed_factor_for_turning * dt
        if self.is_airborne:
            turn_amount *= const.AIRBORNE_TURN_EFFECTIVENESS
        
        self.heading = normalize_angle(self.heading + turn_amount)
        heading_rad = deg_to_rad(self.heading)

        effective_throttle = self.throttle_input * (1.0 - self.handbrake_input * 0.8)
        accel_magnitude = self.engine_power * effective_throttle
        accel_x = math.cos(heading_rad) * accel_magnitude
        accel_y = math.sin(heading_rad) * accel_magnitude
        if not self.is_airborne:
            self.velocity_x += accel_x * dt
            self.velocity_y += accel_y * dt

        if self.brake_input > 0 and self.speed > 0.01 and not self.is_airborne:
            brake_force_magnitude = self.brake_power * self.brake_input
            brake_dx = -self.velocity_x / self.speed if self.speed > 0 else 0
            brake_dy = -self.velocity_y / self.speed if self.speed > 0 else 0
            brake_impulse_x = brake_dx * brake_force_magnitude * dt
            brake_impulse_y = brake_dy * brake_force_magnitude * dt
            if abs(brake_impulse_x) >= abs(self.velocity_x): self.velocity_x = 0
            else: self.velocity_x += brake_impulse_x
            if abs(brake_impulse_y) >= abs(self.velocity_y): self.velocity_y = 0
            else: self.velocity_y += brake_impulse_y
        
        current_base_friction_factor = self.friction
        current_drift_multiplier = 1.0
        current_side_grip_loss_factor = 1.0

        if self.is_airborne:
            current_base_friction_factor = const.AIRBORNE_FRICTION_MULTIPLIER
        else:
            angle_diff_heading_velocity = 0
            if self.speed > 0.1:
                velocity_angle_rad = math.atan2(self.velocity_y, self.velocity_x)
                angle_diff_heading_velocity = abs(angle_difference(self.heading, rad_to_deg(velocity_angle_rad)))
            self.is_drifting = self.speed > self.drift_threshold_speed and angle_diff_heading_velocity > const.DRIFT_THRESHOLD_ANGLE
            if self.is_handbraking:
                current_drift_multiplier = self.handbrake_friction_multiplier
                current_side_grip_loss_factor = self.handbrake_side_grip_loss
            elif self.is_drifting:
                current_drift_multiplier = self.drift_friction_multiplier
            if self.on_mud: current_base_friction_factor **= const.MUD_DRAG_MULTIPLIER
        
        effective_friction_per_second = min(current_base_friction_factor * current_drift_multiplier, 0.999)
        friction_factor_dt = effective_friction_per_second ** dt
        
        forward_velocity_component = self.velocity_x * math.cos(heading_rad) + self.velocity_y * math.sin(heading_rad)
        sideways_velocity_component = -self.velocity_x * math.sin(heading_rad) + self.velocity_y * math.cos(heading_rad)

        forward_velocity_component *= friction_factor_dt
        sideways_velocity_component *= friction_factor_dt
        if (self.is_handbraking or self.is_drifting) and not self.is_airborne:
             sideways_velocity_component *= (current_side_grip_loss_factor ** dt)

        self.velocity_x = forward_velocity_component * math.cos(heading_rad) - sideways_velocity_component * math.sin(heading_rad)
        self.velocity_y = forward_velocity_component * math.sin(heading_rad) + sideways_velocity_component * math.cos(heading_rad)

        self.speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if self.speed > self.max_car_speed:
            scale = self.max_car_speed / self.speed if self.speed > 0 else 0
            self.velocity_x *= scale; self.velocity_y *= scale; self.speed = self.max_car_speed
        if self.speed < 0.5 and self.throttle_input < 0.01 and self.brake_input < 0.01 and not self.is_airborne:
            self.velocity_x = 0; self.velocity_y = 0; self.speed = 0
            self.rpm = lerp(self.rpm, const.IDLE_RPM, 0.1)

        self.world_x += self.velocity_x * dt
        self.world_y += self.velocity_y * dt

        target_rpm = const.IDLE_RPM
        speed_ratio_rpm = clamp(self.speed / speed_factor_denom, 0, 1)
        if self.throttle_input > 0.1 and not self.is_airborne:
            target_rpm = const.IDLE_RPM + (const.MAX_RPM - const.IDLE_RPM) * (0.2 + 0.8 * self.throttle_input) * (0.4 + 0.6 * speed_ratio_rpm)
        elif self.speed > 0.1:
            target_rpm = const.IDLE_RPM + (const.MAX_RPM * 0.5) * speed_ratio_rpm
        self.rpm = lerp(self.rpm, target_rpm, 0.15)
        self.rpm = clamp(self.rpm, const.IDLE_RPM * 0.8, const.MAX_RPM)
        
        self.update_dust(dt)
        self.update_mud_splash(dt)
        # Note: leave_tire_tracks is called from main.py after car_obj.update(dt)

    def trigger_jump(self):
        # ... (trigger_jump method as before) ...
        if not self.is_airborne:
            self.is_airborne = True
            speed_ratio = clamp(self.speed / self.max_car_speed if self.max_car_speed > 0 else 0, 0, 1)
            self.initial_airborne_duration_this_jump = lerp(const.BASE_AIRBORNE_DURATION, const.MAX_AIRBORNE_DURATION, speed_ratio)
            self.airborne_timer = self.initial_airborne_duration_this_jump

    def rotate_and_position_shapes(self):
        # ... (rotate_and_position_shapes method as before, with parabolic lift) ...
        rad = deg_to_rad(self.heading); cos_a = math.cos(rad); sin_a = math.sin(rad)
        base_screen_y = self.screen_y
        airborne_lift_amount = 0
        if self.is_airborne and self.initial_airborne_duration_this_jump > 0:
            time_elapsed_in_jump = self.initial_airborne_duration_this_jump - self.airborne_timer
            normalized_time_in_jump = time_elapsed_in_jump / self.initial_airborne_duration_this_jump
            max_visual_lift = 35 
            lift_factor = 4 * normalized_time_in_jump * (1 - normalized_time_in_jump)
            airborne_lift_amount = -max_visual_lift * lift_factor
        current_screen_y_with_lift = base_screen_y + airborne_lift_amount
        self.rotated_shape_body = []
        for x, y in self.base_shape_body:
            self.rotated_shape_body.append((x*cos_a - y*sin_a + self.screen_x, x*sin_a + y*cos_a + current_screen_y_with_lift))
        self.rotated_shape_window = []
        for x, y in self.base_shape_window:
            self.rotated_shape_window.append((x*cos_a - y*sin_a + self.screen_x, x*sin_a + y*cos_a + current_screen_y_with_lift))
        self.rotated_shape_spoiler = []
        for x, y in self.base_shape_spoiler:
            self.rotated_shape_spoiler.append((x*cos_a - y*sin_a + self.screen_x, x*sin_a + y*cos_a + current_screen_y_with_lift))
        for i, (cx,cy,w,h) in enumerate(self.base_shape_tires):
            hw, hh = w/2, h/2; corners = [(-hw,-hh),(hw,-hh),(hw,hh),(-hw,hh)]
            self.rotated_shape_tires[i] = [( (cx+px)*cos_a - (cy+py)*sin_a + self.screen_x, (cx+px)*sin_a + (cy+py)*cos_a + current_screen_y_with_lift) for px,py in corners]

    def update_dust(self, dt):
        # ... (update_dust method as before) ...
        if dt <= 0: return
        self.time_since_last_dust += dt; spawn_intensity = 1.0
        if self.is_handbraking: spawn_intensity = 2.5
        elif self.is_drifting: spawn_intensity = 1.8
        spawn_condition = self.speed > self.dust_spawn_speed_threshold and not self.on_mud and not self.is_airborne
        current_dust_spawn_interval = const.DUST_SPAWN_INTERVAL / spawn_intensity if spawn_intensity > 0 else const.DUST_SPAWN_INTERVAL
        if spawn_condition and self.time_since_last_dust >= current_dust_spawn_interval:
            if len(self.dust_particles) < const.MAX_DUST_PARTICLES:
                rad = deg_to_rad(self.heading); cos_a = math.cos(rad); sin_a = math.sin(rad)
                rx, ry = -15, 9
                spawn_x_l = self.world_x + (rx*cos_a - ry*sin_a); spawn_y_l = self.world_y + (rx*sin_a + ry*cos_a)
                spawn_x_r = self.world_x + (rx*cos_a - (-ry)*sin_a); spawn_y_r = self.world_y + (rx*sin_a + (-ry)*cos_a)
                particle_x, particle_y = random.choice([(spawn_x_l, spawn_y_l), (spawn_x_r, spawn_y_r)])
                particle_x += random.uniform(-3,3); particle_y += random.uniform(-3,3)
                drift_vx = -self.velocity_x * 0.3 + random.uniform(-10, 10); drift_vy = -self.velocity_y * 0.3 + random.uniform(-10, 10)
                self.dust_particles.append(DustParticle(particle_x, particle_y, drift_vx, drift_vy))
            self.time_since_last_dust = 0.0
        self.dust_particles = deque(p for p in self.dust_particles if p.update(dt))

    def update_mud_splash(self, dt):
        # ... (update_mud_splash method as before) ...
        if dt <= 0 or not self.on_mud or self.is_airborne: return
        self.time_since_last_mud += dt
        if self.speed > const.MUD_SPAWN_SPEED_THRESHOLD and self.time_since_last_mud >= const.MUD_SPAWN_INTERVAL:
            if len(self.mud_particles) < const.MAX_MUD_PARTICLES:
                rad = deg_to_rad(self.heading); cos_a = math.cos(rad); sin_a = math.sin(rad)
                for tire_cx_rel, tire_cy_rel, _, _ in self.base_shape_tires:
                    tire_world_x = self.world_x + (tire_cx_rel * cos_a - tire_cy_rel * sin_a)
                    tire_world_y = self.world_y + (tire_cx_rel * sin_a + tire_cy_rel * cos_a)
                    particle_x = tire_world_x + random.uniform(-5, 5)
                    particle_y = tire_world_y + random.uniform(-5, 5)
                    drift_vx = -self.velocity_x * 0.15 + random.uniform(-40, 40)
                    drift_vy = -self.velocity_y * 0.15 + random.uniform(-40, 40) - random.uniform(20, 60)
                    self.mud_particles.append(MudParticle(particle_x, particle_y, drift_vx, drift_vy))
            self.time_since_last_mud = 0.0
        self.mud_particles = deque(p for p in self.mud_particles if p.update(dt))

    def draw(self, surface, draw_shadow=True):
        # ... (draw method with dynamic shadow as before) ...
        if draw_shadow:
            shadow_scale_factor = 1.0; shadow_alpha_factor = 1.0
            shadow_offset_x_mult = 1.0; shadow_offset_y_mult = 1.0
            if self.is_airborne and self.initial_airborne_duration_this_jump > 0:
                time_elapsed_in_jump = self.initial_airborne_duration_this_jump - self.airborne_timer
                normalized_time_in_jump = time_elapsed_in_jump / self.initial_airborne_duration_this_jump
                parabolic_factor = 4 * normalized_time_in_jump * (1 - normalized_time_in_jump)
                shadow_scale_factor = lerp(1.0, const.AIRBORNE_SHADOW_SCALE, parabolic_factor)
                shadow_alpha_factor = lerp(1.0, 0.3, parabolic_factor)
                shadow_offset_x_mult = lerp(1.0, 3.5, parabolic_factor)
                shadow_offset_y_mult = lerp(1.0, 3.5, parabolic_factor)
            current_shadow_offset_x = const.SHADOW_OFFSET_X * shadow_offset_x_mult
            current_shadow_offset_y = const.SHADOW_OFFSET_Y * shadow_offset_y_mult
            final_shadow_alpha = int(const.SHADOW_COLOR[3] * shadow_alpha_factor)
            shadow_surf = pygame.Surface((const.SCREEN_WIDTH, const.SCREEN_HEIGHT), pygame.SRCALPHA); shadow_surf.fill((0,0,0,0))
            shadow_color_with_alpha = (*const.BLACK[:3], final_shadow_alpha)
            if not self.rotated_shape_body: return
            avg_lifted_x = sum(p[0] for p in self.rotated_shape_body) / len(self.rotated_shape_body)
            avg_lifted_y = sum(p[1] for p in self.rotated_shape_body) / len(self.rotated_shape_body)
            body_shadow_ps = []
            for p_x, p_y in self.rotated_shape_body:
                dx, dy = p_x - avg_lifted_x, p_y - avg_lifted_y
                scaled_dx, scaled_dy = dx * shadow_scale_factor, dy * shadow_scale_factor
                body_shadow_ps.append((avg_lifted_x + scaled_dx + current_shadow_offset_x, avg_lifted_y + scaled_dy + current_shadow_offset_y))
            if body_shadow_ps: pygame.draw.polygon(shadow_surf, shadow_color_with_alpha, body_shadow_ps)
            for tire_corners in self.rotated_shape_tires:
                if not tire_corners: continue
                avg_lifted_tx = sum(p[0] for p in tire_corners) / len(tire_corners); avg_lifted_ty = sum(p[1] for p in tire_corners) / len(tire_corners)
                shadow_tire_ps = []
                for p_x, p_y in tire_corners:
                    dx, dy = p_x - avg_lifted_tx, p_y - avg_lifted_ty; scaled_dx, scaled_dy = dx * shadow_scale_factor, dy * shadow_scale_factor
                    shadow_tire_ps.append((avg_lifted_tx + scaled_dx + current_shadow_offset_x, avg_lifted_ty + scaled_dy + current_shadow_offset_y))
                if len(shadow_tire_ps) == 4: pygame.draw.polygon(shadow_surf, shadow_color_with_alpha, shadow_tire_ps)
            if self.rotated_shape_spoiler:
                avg_lifted_sx = sum(p[0] for p in self.rotated_shape_spoiler) / len(self.rotated_shape_spoiler); avg_lifted_sy = sum(p[1] for p in self.rotated_shape_spoiler) / len(self.rotated_shape_spoiler)
                spoiler_shadow_ps = []
                for p_x, p_y in self.rotated_shape_spoiler:
                    dx, dy = p_x - avg_lifted_sx, p_y - avg_lifted_sy; scaled_dx, scaled_dy = dx * shadow_scale_factor, dy * shadow_scale_factor
                    spoiler_shadow_ps.append((avg_lifted_sx + scaled_dx + current_shadow_offset_x, avg_lifted_sy + scaled_dy + current_shadow_offset_y))
                pygame.draw.polygon(shadow_surf, shadow_color_with_alpha, spoiler_shadow_ps)
            surface.blit(shadow_surf, (0,0))
        for tire_corners in self.rotated_shape_tires:
            int_tire_corners = [(int(p[0]), int(p[1])) for p in tire_corners]
            if len(int_tire_corners) == 4: pygame.draw.polygon(surface, const.TIRE_COLOR, int_tire_corners)
        if self.rotated_shape_spoiler: pygame.draw.polygon(surface, const.SPOILER_COLOR, self.rotated_shape_spoiler); pygame.draw.lines(surface, const.BLACK, True, self.rotated_shape_spoiler, 1)
        if self.rotated_shape_body: pygame.draw.polygon(surface, self.color, self.rotated_shape_body); pygame.draw.lines(surface, const.BLACK, True, self.rotated_shape_body, 1)
        if self.rotated_shape_window: pygame.draw.polygon(surface, const.CAR_WINDOW_COLOR, self.rotated_shape_window); pygame.draw.lines(surface, const.BLACK, True, self.rotated_shape_window, 1)

    def draw_dust(self, surface, camera_offset_x, camera_offset_y):
        for particle in self.dust_particles: particle.draw(surface, camera_offset_x, camera_offset_y)

    def draw_mud_splash(self, surface, camera_offset_x, camera_offset_y):
        for particle in self.mud_particles: particle.draw(surface, camera_offset_x, camera_offset_y)
        
    # --- NEW METHOD for Tire Tracks ---
    def leave_tire_tracks(self, tracks_surface, world_bounds_offset):
        """
        Draws tire tracks onto the provided tracks_surface if conditions are met.
        world_bounds_offset is typically const.WORLD_BOUNDS, used to map world coords to surface coords.
        """
        # Conditions for leaving tracks:
        # 1. Not airborne
        # 2. Not on a mud patch (self.on_mud is set in main.py)
        # 3. Speed is above a minimum threshold
        # (Future: Could add check for "on_grass" if you have defined road surfaces)
        if not self.is_airborne and not self.on_mud and self.speed > const.TIRE_TRACK_MIN_SPEED:
            heading_rad = deg_to_rad(self.heading)
            cos_h = math.cos(heading_rad)
            sin_h = math.sin(heading_rad)

            # Calculate positions for two rear tire tracks
            # Using simplified offsets from constants for now
            # Track point 1 (e.g., left rear)
            track1_world_x = self.world_x - cos_h * const.TIRE_TRACK_OFFSET_REAR + sin_h * const.TIRE_TRACK_OFFSET_SIDE
            track1_world_y = self.world_y - sin_h * const.TIRE_TRACK_OFFSET_REAR - cos_h * const.TIRE_TRACK_OFFSET_SIDE
            
            # Track point 2 (e.g., right rear)
            track2_world_x = self.world_x - cos_h * const.TIRE_TRACK_OFFSET_REAR - sin_h * const.TIRE_TRACK_OFFSET_SIDE
            track2_world_y = self.world_y - sin_h * const.TIRE_TRACK_OFFSET_REAR + cos_h * const.TIRE_TRACK_OFFSET_SIDE

            # Convert world coordinates to coordinates on the tire_tracks_surface
            # The tire_tracks_surface has its (0,0) at world (-world_bounds_offset, -world_bounds_offset)
            track1_surf_x = int(track1_world_x + world_bounds_offset)
            track1_surf_y = int(track1_world_y + world_bounds_offset)
            track2_surf_x = int(track2_world_x + world_bounds_offset)
            track2_surf_y = int(track2_world_y + world_bounds_offset)

            # Draw the tracks (e.g., small circles)
            pygame.draw.circle(tracks_surface, const.TIRE_TRACK_COLOR, (track1_surf_x, track1_surf_y), const.TIRE_TRACK_RADIUS)
            pygame.draw.circle(tracks_surface, const.TIRE_TRACK_COLOR, (track2_surf_x, track2_surf_y), const.TIRE_TRACK_RADIUS)

    def get_world_collision_rect(self):
        # ... (get_world_collision_rect method as before) ...
        radius = self.collision_radius * 1.2
        return pygame.Rect(self.world_x - radius, self.world_y - radius, radius * 2, radius * 2)

    def resolve_collision_with(self, other_car, nx, ny, overlap):
        # ... (resolve_collision_with method as before) ...
        correction_amount = overlap / 2.0
        self.world_x += nx * correction_amount; self.world_y += ny * correction_amount
        other_car.world_x -= nx * correction_amount; other_car.world_y -= ny * correction_amount
        rvx = self.velocity_x - other_car.velocity_x; rvy = self.velocity_y - other_car.velocity_y
        vel_normal = rvx * nx + rvy * ny
        if vel_normal > 0: return
        elasticity = 0.6; m1 = self.mass; m2 = other_car.mass
        if m1 <= 0: m1 = 1.0; 
        if m2 <= 0: m2 = 1.0
        inv_mass_sum = (1.0 / m1) + (1.0 / m2)
        if inv_mass_sum == 0: return
        impulse_scalar = -(1.0 + elasticity) * vel_normal / inv_mass_sum
        self.velocity_x += (impulse_scalar / m1) * nx; self.velocity_y += (impulse_scalar / m1) * ny
        other_car.velocity_x -= (impulse_scalar / m2) * nx; other_car.velocity_y -= (impulse_scalar / m2) * ny
        self.speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        other_car.speed = math.sqrt(other_car.velocity_x**2 + other_car.velocity_y**2)