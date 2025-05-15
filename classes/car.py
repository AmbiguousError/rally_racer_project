# classes/car.py
# This file defines the Car class for the Rally Racer game.

import pygame
import random
import math
from collections import deque

# Assuming constants.py and utils.py are in the parent directory or project root is in PYTHONPATH.
# If running main.py from the project root, these imports should work.
import constants as const
from utils import (
    deg_to_rad, rad_to_deg, angle_difference, normalize_angle, 
    lerp, distance_sq, clamp, check_line_crossing
)

# Relative import for particle classes from the same 'classes' package
from .particle import DustParticle, MudParticle

class Car:
    """
    Represents a car in the game, handling its physics, AI (if applicable),
    drawing, and interactions.
    """
    def __init__(self, x, y, is_ai=False, unique_body_color=None):
        """
        Initializes a Car object.

        Args:
            x (int): Initial screen x-coordinate (often a placeholder if camera-centered).
            y (int): Initial screen y-coordinate.
            is_ai (bool, optional): True if this car is AI-controlled. Defaults to False.
            unique_body_color (tuple, optional): (R,G,B) color for AI cars. Defaults to None.
        """
        self.screen_x = x  # Screen position for drawing (can be center if camera follows)
        self.screen_y = y
        self.world_x = 0.0 # Actual position in the game world, set by reset_position
        self.world_y = 0.0
        self.prev_world_x = 0.0 # Previous world position for line crossing checks
        self.prev_world_y = 0.0
        
        self.heading = 180.0  # Degrees, 0 is right, 90 is down, 180 is left, 270 is up
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.speed = 0.0
        self.rpm = const.IDLE_RPM
        
        # Control inputs (0.0 to 1.0 for throttle/brake, -1.0 to 1.0 for steer)
        self.steering_input = 0.0
        self.throttle_input = 0.0
        self.brake_input = 0.0
        self.handbrake_input = 0.0
        
        # State flags
        self.is_drifting = False
        self.is_handbraking = False
        self.on_mud = False
        self.is_ai = is_ai
        self.is_airborne = False
        self.airborne_timer = 0.0
        
        self.mass = 1.0 # For collision physics

        # Assign color
        if is_ai:
            self.color = unique_body_color if unique_body_color else const.AI_CAR_BODY_COLOR
        else:
            self.color = const.CAR_BODY_COLOR

        # Car shape definitions (base points relative to car center 0,0)
        self.base_shape_body = [(22, 0), (20, -6), (10, -9), (-12, -9), (-20, -6), (-22, 0), (-20, 6), (-12, 9), (10, 9), (20, 6)]
        self.base_shape_window = [(12, -6), (8, -6), (-8, -6), (-10, -4), (-10, 4), (-8, 6), (8, 6), (12, 4)]
        self.base_shape_tires = [(12, -10, 6, 4), (12, 10, 6, 4), (-12, -10, 6, 4), (-12, 10, 6, 4)] # (cx, cy, width, height)
        self.base_shape_spoiler = [(-18, -12), (-15, -12), (-15, 12), (-18, 12)]
        
        # Rotated shapes (will be calculated based on heading and screen_x, screen_y)
        self.rotated_shape_body = self.base_shape_body[:]
        self.rotated_shape_window = self.base_shape_window[:]
        self.rotated_shape_tires = [[(0,0)]*4 for _ in self.base_shape_tires] # Placeholder for 4 corners of each tire
        self.rotated_shape_spoiler = self.base_shape_spoiler[:]
        
        self.collision_radius = 18 # For car-to-car collision detection

        # Particle effects
        self.dust_particles = deque()
        self.time_since_last_dust = 0.0
        self.mud_particles = deque()
        self.time_since_last_mud = 0.0

        # AI / Race State (initialized here, managed by game logic and update_ai)
        self.ai_target_checkpoint_index = 0 # Index for course_checkpoints_coords
        self.current_lap = 0
        self.lap_times = []
        self.lap_start_time = 0.0
        self.race_started = False # True once this car crosses the start line for the first time
        self.race_finished_for_car = False # True if this car has completed all laps
        self.last_line_crossing_time = -const.LINE_CROSSING_DEBOUNCE # Debounce for line crossing

        # AI Difficulty Parameters (base values, will be tuned by apply_ai_difficulty)
        self.ai_lookahead_factor = const.BASE_AI_LOOKAHEAD_FACTOR
        self.ai_turn_threshold = const.BASE_AI_TURN_THRESHOLD
        self.ai_brake_factor = const.BASE_AI_BRAKE_FACTOR
        self.ai_steer_sharpness = const.BASE_AI_STEER_SHARPNESS
        self.ai_throttle_control = const.BASE_AI_THROTTLE_CONTROL
        self.ai_mud_reaction = const.BASE_AI_MUD_REACTION
        
        # Physics properties (base values, will be tuned by apply_setup)
        self.max_car_speed = const.BASE_MAX_CAR_SPEED
        self.engine_power = const.BASE_ENGINE_POWER
        self.brake_power = const.BASE_BRAKE_POWER
        self.friction = const.BASE_FRICTION
        self.drift_friction_multiplier = const.BASE_DRIFT_FRICTION_MULTIPLIER
        self.handbrake_friction_multiplier = const.BASE_HANDBRAKE_FRICTION_MULTIPLIER
        self.handbrake_side_grip_loss = const.BASE_HANDBRAKE_SIDE_GRIP_LOSS
        self.drift_threshold_speed = self.max_car_speed * 0.25
        self.dust_spawn_speed_threshold = self.max_car_speed * 0.05

    def apply_setup(self, top_speed_percent, grip_percent):
        """Applies car setup based on selected top speed and grip percentages."""
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
            speed_variation_factor = random.uniform(0.95, 1.05) # +/- 5%
            self.max_car_speed *= speed_variation_factor
            power_variation_factor = random.uniform(0.93, 1.07) # +/- 7%
            self.engine_power *= power_variation_factor
            # Note: Brake power is already scaled with engine power

        self.drift_threshold_speed = self.max_car_speed * 0.25
        self.dust_spawn_speed_threshold = self.max_car_speed * 0.05

    def apply_ai_difficulty(self, difficulty_index, difficulty_options):
        """Applies AI behavioral parameters based on selected difficulty."""
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
        else: # Default to Medium
            self.ai_throttle_control = const.BASE_AI_THROTTLE_CONTROL * 0.90
            self.ai_brake_factor = const.BASE_AI_BRAKE_FACTOR * 1.15
            self.ai_steer_sharpness = const.BASE_AI_STEER_SHARPNESS * 0.85
            self.ai_mud_reaction = const.BASE_AI_MUD_REACTION * 1.1
            self.ai_lookahead_factor = const.BASE_AI_LOOKAHEAD_FACTOR * 0.90
            self.ai_turn_threshold = const.BASE_AI_TURN_THRESHOLD + 8

        # Individual AI behavioral randomization
        param_variation_range = 0.10 
        self.ai_throttle_control = clamp(self.ai_throttle_control * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.60, 1.0)
        self.ai_brake_factor = clamp(self.ai_brake_factor * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.4, 1.3)
        self.ai_steer_sharpness = clamp(self.ai_steer_sharpness * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.3, 1.0)
        self.ai_lookahead_factor = clamp(self.ai_lookahead_factor * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.8, 2.5)
        self.ai_turn_threshold = clamp(self.ai_turn_threshold + random.uniform(-7, 7), 10, 55)
        self.ai_mud_reaction = clamp(self.ai_mud_reaction * random.uniform(1.0 - param_variation_range, 1.0 + param_variation_range), 0.2, 0.95)

    def reset_position(self, start_world_x=0.0, start_world_y=0.0):
        """Resets the car's position, velocity, and race state."""
        self.world_x = start_world_x
        self.world_y = start_world_y
        self.prev_world_x = start_world_x
        self.prev_world_y = start_world_y
        self.heading = 180.0  # Default heading (left)
        self.velocity_x = 0.0; self.velocity_y = 0.0; self.speed = 0.0
        self.rpm = const.IDLE_RPM
        self.steering_input = 0.0; self.throttle_input = 0.0
        self.brake_input = 0.0; self.handbrake_input = 0.0
        self.dust_particles.clear(); self.mud_particles.clear()
        self.on_mud = False; self.is_drifting = False; self.is_handbraking = False
        self.is_airborne = False; self.airborne_timer = 0.0
        
        # Reset race-specific state
        self.ai_target_checkpoint_index = 0
        self.current_lap = 0
        self.lap_times = []
        self.lap_start_time = 0.0
        self.race_started = False
        self.race_finished_for_car = False
        self.last_line_crossing_time = -const.LINE_CROSSING_DEBOUNCE

    def set_controls(self, throttle, brake, steer, handbrake):
        """Sets the control inputs for the car."""
        self.throttle_input = throttle
        self.brake_input = brake
        self.steering_input = steer
        self.handbrake_input = handbrake

    def update_ai(self, dt, checkpoints, num_course_checkpoints, total_laps, current_time_s):
        """Calculates AI control inputs and updates AI race state."""
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
                else: is_targeting_finish_for_lap = True # Failsafe
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
        """Updates the car's physics state for the given delta time."""
        if dt <= 0: return
        self.prev_world_x = self.world_x; self.prev_world_y = self.world_y
        self.is_handbraking = self.handbrake_input > 0.5

        if self.is_airborne:
            self.airborne_timer -= dt
            if self.airborne_timer <= 0: self.is_airborne = False
        
        current_turn_effectiveness = const.AIRBORNE_TURN_EFFECTIVENESS if self.is_airborne else const.MIN_TURN_EFFECTIVENESS
        speed_factor_denom = self.max_car_speed if self.max_car_speed > 0 else 1.0
        speed_factor_for_turning = current_turn_effectiveness + (1.0 - current_turn_effectiveness) * (1.0 - clamp(self.speed / speed_factor_denom, 0, 1))
        turn_amount = self.steering_input * const.CAR_TURN_RATE * speed_factor_for_turning * dt
        if self.is_airborne: turn_amount *= const.AIRBORNE_TURN_EFFECTIVENESS # Further reduce turning in air if needed, or set to 0
        
        self.heading = normalize_angle(self.heading + turn_amount)
        heading_rad = deg_to_rad(self.heading)

        # Acceleration
        effective_throttle = self.throttle_input * (1.0 - self.handbrake_input * 0.8) # Handbrake reduces throttle effect
        accel_magnitude = self.engine_power * effective_throttle
        accel_x = math.cos(heading_rad) * accel_magnitude
        accel_y = math.sin(heading_rad) * accel_magnitude
        self.velocity_x += accel_x * dt
        self.velocity_y += accel_y * dt

        # Braking
        if self.brake_input > 0 and self.speed > 0.01:
            brake_force_magnitude = self.brake_power * self.brake_input
            brake_dx = -self.velocity_x / self.speed if self.speed > 0 else 0
            brake_dy = -self.velocity_y / self.speed if self.speed > 0 else 0
            brake_impulse_x = brake_dx * brake_force_magnitude * dt
            brake_impulse_y = brake_dy * brake_force_magnitude * dt
            if abs(brake_impulse_x) >= abs(self.velocity_x): self.velocity_x = 0
            else: self.velocity_x += brake_impulse_x
            if abs(brake_impulse_y) >= abs(self.velocity_y): self.velocity_y = 0
            else: self.velocity_y += brake_impulse_y
        
        # Friction & Drifting
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
            
            if self.on_mud:
                current_base_friction_factor **= const.MUD_DRAG_MULTIPLIER # Makes friction much stronger

        effective_friction_per_second = min(current_base_friction_factor * current_drift_multiplier, 0.999) # Cap to avoid issues
        friction_factor_dt = effective_friction_per_second ** dt

        # Apply Friction & Grip Loss (decouple forward/sideways velocity)
        forward_velocity_component = self.velocity_x * math.cos(heading_rad) + self.velocity_y * math.sin(heading_rad)
        sideways_velocity_component = -self.velocity_x * math.sin(heading_rad) + self.velocity_y * math.cos(heading_rad)

        forward_velocity_component *= friction_factor_dt
        sideways_velocity_component *= friction_factor_dt # Base friction also applies to sideways
        
        if (self.is_handbraking or self.is_drifting) and not self.is_airborne: # More side slip when drifting/handbraking
             sideways_velocity_component *= (current_side_grip_loss_factor ** dt)

        self.velocity_x = forward_velocity_component * math.cos(heading_rad) - sideways_velocity_component * math.sin(heading_rad)
        self.velocity_y = forward_velocity_component * math.sin(heading_rad) + sideways_velocity_component * math.cos(heading_rad)

        # Speed Limiting & Stop Creeping
        self.speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if self.speed > self.max_car_speed:
            scale = self.max_car_speed / self.speed if self.speed > 0 else 0
            self.velocity_x *= scale; self.velocity_y *= scale; self.speed = self.max_car_speed
        
        # If speed is very low and no input, stop the car to prevent micro-drifting
        if self.speed < 0.5 and self.throttle_input < 0.01 and self.brake_input < 0.01 and not self.is_airborne:
            self.velocity_x = 0; self.velocity_y = 0; self.speed = 0
            self.rpm = lerp(self.rpm, const.IDLE_RPM, 0.1) # Settle RPM to idle

        # Position Update
        self.world_x += self.velocity_x * dt
        self.world_y += self.velocity_y * dt

        # RPM Simulation
        target_rpm = const.IDLE_RPM
        speed_ratio_rpm = clamp(self.speed / speed_factor_denom, 0, 1) # Use speed_factor_denom from above
        if self.throttle_input > 0.1: # Accelerating
            target_rpm = const.IDLE_RPM + (const.MAX_RPM - const.IDLE_RPM) * (0.2 + 0.8 * self.throttle_input) * (0.4 + 0.6 * speed_ratio_rpm)
        elif self.speed > 0.1: # Coasting
            target_rpm = const.IDLE_RPM + (const.MAX_RPM * 0.5) * speed_ratio_rpm 
        self.rpm = lerp(self.rpm, target_rpm, 0.15) # Smoothing factor for RPM change
        self.rpm = clamp(self.rpm, const.IDLE_RPM * 0.8, const.MAX_RPM) # Clamp RPM within valid range
        
        # Particle updates are called from Car instance after its own update in main loop if needed
        self.update_dust(dt)
        self.update_mud_splash(dt)
        # self.rotate_and_position_shapes() # This is now called in main loop before drawing

    def trigger_jump(self):
        if not self.is_airborne:
            self.is_airborne = True
            speed_ratio = clamp(self.speed / self.max_car_speed if self.max_car_speed > 0 else 0, 0, 1)
            self.airborne_timer = lerp(const.BASE_AIRBORNE_DURATION, const.MAX_AIRBORNE_DURATION, speed_ratio)

    def rotate_point(self, px, py, angle_rad, center_x, center_y): # Not used internally anymore, but can be helper
        cos_a = math.cos(angle_rad); sin_a = math.sin(angle_rad)
        rx = px * cos_a - py * sin_a; ry = px * sin_a + py * cos_a
        return rx + center_x, ry + center_y

    def rotate_and_position_shapes(self):
        """Calculates the screen coordinates of the car's shapes based on its current heading and screen position."""
        rad = deg_to_rad(self.heading)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        # Body
        self.rotated_shape_body = []
        for x, y in self.base_shape_body:
            rx = x * cos_a - y * sin_a
            ry = x * sin_a + y * cos_a
            self.rotated_shape_body.append((rx + self.screen_x, ry + self.screen_y))
        # Window
        self.rotated_shape_window = []
        for x, y in self.base_shape_window:
            rx = x * cos_a - y * sin_a
            ry = x * sin_a + y * cos_a
            self.rotated_shape_window.append((rx + self.screen_x, ry + self.screen_y))
        # Spoiler
        self.rotated_shape_spoiler = []
        for x, y in self.base_shape_spoiler:
            rx = x * cos_a - y * sin_a
            ry = x * sin_a + y * cos_a
            self.rotated_shape_spoiler.append((rx + self.screen_x, ry + self.screen_y))
        # Tires
        for i, (cx, cy, w, h) in enumerate(self.base_shape_tires):
            half_w, half_h = w / 2, h / 2
            # Tire corners relative to tire center (cx, cy)
            tire_local_corners = [
                (cx - half_w, cy - half_h), (cx + half_w, cy - half_h),
                (cx + half_w, cy + half_h), (cx - half_w, cy + half_h)
            ]
            rotated_tire_abs = []
            for tlx, tly in tire_local_corners:
                # Rotate these local tire points around car's origin (0,0) first
                rx_tire = tlx * cos_a - tly * sin_a
                ry_tire = tlx * sin_a + tly * cos_a
                # Then translate to car's screen position
                rotated_tire_abs.append((rx_tire + self.screen_x, ry_tire + self.screen_y))
            self.rotated_shape_tires[i] = rotated_tire_abs
            
    def update_dust(self, dt):
        if dt <= 0: return
        self.time_since_last_dust += dt
        spawn_intensity = 1.0
        if self.is_handbraking: spawn_intensity = 2.5
        elif self.is_drifting: spawn_intensity = 1.8
        
        spawn_condition = self.speed > self.dust_spawn_speed_threshold and not self.on_mud and not self.is_airborne
        current_dust_spawn_interval = const.DUST_SPAWN_INTERVAL / spawn_intensity if spawn_intensity > 0 else const.DUST_SPAWN_INTERVAL

        if spawn_condition and self.time_since_last_dust >= current_dust_spawn_interval:
            if len(self.dust_particles) < const.MAX_DUST_PARTICLES:
                rad = deg_to_rad(self.heading); cos_a = math.cos(rad); sin_a = math.sin(rad)
                # Spawn from rear tire area
                rear_offset_x = -15 # Relative to car center, behind it
                tire_offset_y = 9   # Relative to car center, to the side
                
                # Left rear tire approx world pos
                spawn_x_base_l = self.world_x + (rear_offset_x * cos_a - tire_offset_y * sin_a)
                spawn_y_base_l = self.world_y + (rear_offset_x * sin_a + tire_offset_y * cos_a)
                # Right rear tire approx world pos
                spawn_x_base_r = self.world_x + (rear_offset_x * cos_a - (-tire_offset_y) * sin_a)
                spawn_y_base_r = self.world_y + (rear_offset_x * sin_a + (-tire_offset_y) * cos_a)
                
                # Choose one side randomly or alternate
                if random.random() < 0.5:
                    particle_x = spawn_x_base_l + random.uniform(-3,3)
                    particle_y = spawn_y_base_l + random.uniform(-3,3)
                else:
                    particle_x = spawn_x_base_r + random.uniform(-3,3)
                    particle_y = spawn_y_base_r + random.uniform(-3,3)
                
                drift_vx = -self.velocity_x * 0.3 + random.uniform(-10, 10) # Dust kicked back
                drift_vy = -self.velocity_y * 0.3 + random.uniform(-10, 10)
                self.dust_particles.append(DustParticle(particle_x, particle_y, drift_vx, drift_vy))
            self.time_since_last_dust = 0.0
        
        # Update existing dust particles and remove dead ones
        self.dust_particles = deque(p for p in self.dust_particles if p.update(dt))

    def update_mud_splash(self, dt):
        if dt <= 0 or not self.on_mud or self.is_airborne: return
        self.time_since_last_mud += dt
        
        if self.speed > const.MUD_SPAWN_SPEED_THRESHOLD and self.time_since_last_mud >= const.MUD_SPAWN_INTERVAL:
            if len(self.mud_particles) < const.MAX_MUD_PARTICLES:
                rad = deg_to_rad(self.heading); cos_a = math.cos(rad); sin_a = math.sin(rad)
                # Spawn from all tire positions
                for tire_cx_rel, tire_cy_rel, _, _ in self.base_shape_tires: # Use tire center from base_shape_tires
                    # World position of the tire center
                    tire_world_x = self.world_x + (tire_cx_rel * cos_a - tire_cy_rel * sin_a)
                    tire_world_y = self.world_y + (tire_cx_rel * sin_a + tire_cy_rel * cos_a)
                    
                    particle_x = tire_world_x + random.uniform(-5, 5) # Spawn near the tire
                    particle_y = tire_world_y + random.uniform(-5, 5)
                    
                    # Mud splashes more erratically and can go upwards
                    drift_vx = -self.velocity_x * 0.15 + random.uniform(-40, 40) 
                    drift_vy = -self.velocity_y * 0.15 + random.uniform(-40, 40) - random.uniform(20, 60) # Add upward component
                    self.mud_particles.append(MudParticle(particle_x, particle_y, drift_vx, drift_vy))
            self.time_since_last_mud = 0.0
            
        self.mud_particles = deque(p for p in self.mud_particles if p.update(dt))

    def draw(self, surface, draw_shadow=True):
        """Draws the car on the given surface."""
        # Ensure shapes are updated based on current screen_x, screen_y, and heading
        # This should be called in main loop before drawing if car's screen pos or heading changed
        # self.rotate_and_position_shapes() # This is now called from main loop's drawing section

        if draw_shadow:
            shadow_scale = const.AIRBORNE_SHADOW_SCALE if self.is_airborne else 1.0
            shadow_offset_x_val = const.SHADOW_OFFSET_X * shadow_scale
            shadow_offset_y_val = const.SHADOW_OFFSET_Y * shadow_scale
            
            # Create a temporary surface for the shadow to handle alpha correctly
            shadow_surf = pygame.Surface((const.SCREEN_WIDTH, const.SCREEN_HEIGHT), pygame.SRCALPHA)
            shadow_surf.fill((0,0,0,0)) # Fully transparent

            shadow_color_with_alpha = (*const.BLACK[:3], const.SHADOW_COLOR[3]) # Use alpha from SHADOW_COLOR

            # Shadow for tires
            for tire_corners in self.rotated_shape_tires:
                shadow_tire_ps = [(int(p[0] * shadow_scale + shadow_offset_x_val), 
                                   int(p[1] * shadow_scale + shadow_offset_y_val)) for p in tire_corners]
                if len(shadow_tire_ps) == 4: pygame.draw.polygon(shadow_surf, shadow_color_with_alpha, shadow_tire_ps)
            
            # Shadow for spoiler
            spoiler_shadow_ps = [(int(p[0] * shadow_scale + shadow_offset_x_val), 
                                  int(p[1] * shadow_scale + shadow_offset_y_val)) for p in self.rotated_shape_spoiler]
            pygame.draw.polygon(shadow_surf, shadow_color_with_alpha, spoiler_shadow_ps)

            # Shadow for body
            body_shadow_ps = [(int(p[0] * shadow_scale + shadow_offset_x_val), 
                               int(p[1] * shadow_scale + shadow_offset_y_val)) for p in self.rotated_shape_body]
            pygame.draw.polygon(shadow_surf, shadow_color_with_alpha, body_shadow_ps)
            
            surface.blit(shadow_surf, (0,0))

        # Draw Tires
        for tire_corners in self.rotated_shape_tires:
            int_tire_corners = [(int(p[0]), int(p[1])) for p in tire_corners]
            if len(int_tire_corners) == 4: pygame.draw.polygon(surface, const.TIRE_COLOR, int_tire_corners)
        
        # Draw Spoiler
        pygame.draw.polygon(surface, const.SPOILER_COLOR, self.rotated_shape_spoiler)
        pygame.draw.lines(surface, const.BLACK, True, self.rotated_shape_spoiler, 1) # Outline
        
        # Draw Body (uses self.color which is unique for AI)
        pygame.draw.polygon(surface, self.color, self.rotated_shape_body)
        pygame.draw.lines(surface, const.BLACK, True, self.rotated_shape_body, 1) # Outline
        
        # Draw Window
        pygame.draw.polygon(surface, const.CAR_WINDOW_COLOR, self.rotated_shape_window)
        pygame.draw.lines(surface, const.BLACK, True, self.rotated_shape_window, 1) # Outline

    def draw_dust(self, surface, camera_offset_x, camera_offset_y):
        """Draws all active dust particles for this car."""
        for particle in self.dust_particles:
            particle.draw(surface, camera_offset_x, camera_offset_y)

    def draw_mud_splash(self, surface, camera_offset_x, camera_offset_y):
        """Draws all active mud splash particles for this car."""
        for particle in self.mud_particles:
            particle.draw(surface, camera_offset_x, camera_offset_y)
        
    def get_world_collision_rect(self):
        """Returns a pygame.Rect representing the car's bounding box in world coordinates."""
        # This is a simplified bounding box, using collision_radius.
        # For more accurate ramp/mud collision, polygon collision might be better.
        radius = self.collision_radius * 1.2 # Slightly larger for rect
        return pygame.Rect(self.world_x - radius, self.world_y - radius, radius * 2, radius * 2)

    def resolve_collision_with(self, other_car, nx, ny, overlap):
        """ Resolves collision between this car and other_car. """
        # Positional Correction
        correction_amount = overlap / 2.0 # Each car moves by half the overlap
        self.world_x += nx * correction_amount
        self.world_y += ny * correction_amount
        other_car.world_x -= nx * correction_amount
        other_car.world_y -= ny * correction_amount

        # Elastic Collision Response (Velocity Change)
        rvx = self.velocity_x - other_car.velocity_x
        rvy = self.velocity_y - other_car.velocity_y
        vel_normal = rvx * nx + rvy * ny # Relative velocity along the normal

        if vel_normal > 0: # Objects are already moving apart
            return

        elasticity = 0.6 # Coefficient of restitution (0=inelastic, 1=perfectly elastic)
        m1 = self.mass; m2 = other_car.mass
        if m1 <= 0: m1 = 1.0 # Safeguard against zero mass
        if m2 <= 0: m2 = 1.0
        
        inv_mass_sum = (1.0 / m1) + (1.0 / m2)
        if inv_mass_sum == 0: return # Avoid division by zero if both have "infinite" mass

        impulse_scalar = -(1.0 + elasticity) * vel_normal / inv_mass_sum

        # Apply impulse to change velocities
        self.velocity_x += (impulse_scalar / m1) * nx
        self.velocity_y += (impulse_scalar / m1) * ny
        other_car.velocity_x -= (impulse_scalar / m2) * nx
        other_car.velocity_y -= (impulse_scalar / m2) * ny
        
        # Update speed property after velocity change (Car.update might do this again)
        self.speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        other_car.speed = math.sqrt(other_car.velocity_x**2 + other_car.velocity_y**2)

