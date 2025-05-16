# rally_racer_project/classes/track_elements.py
# This file defines classes for track elements like Ramps, MudPatches, and Checkpoints.

import pygame
import random
import math

import constants as const
from utils import deg_to_rad, lerp, clamp # Ensure clamp is imported from utils

class Ramp:
    """
    Represents a circular jump ramp on the track.
    """
    def __init__(self, world_x, world_y, radius): # Changed parameters
        self.world_x = world_x
        self.world_y = world_y
        self.radius = radius
        self.diameter = radius * 2

        # The bounding rectangle for this circular ramp
        # Used for broad-phase collision checks or culling.
        self.rect = pygame.Rect(
            self.world_x - self.radius,
            self.world_y - self.radius,
            self.diameter,
            self.diameter
        )
        # Old attributes for polygonal ramp are no longer needed:
        # self.angle_rad, self.cos_a, self.sin_a, self.corners_rel, self.corners_world
        # The old _calculate_bounding_rect method is also not needed as self.rect is simpler.

    def check_collision(self, car_world_rect):
        """
        Checks for collision between the car's world rectangle (car_world_rect)
        and this ramp's circular area.
        """
        # Find the closest point on the car's rectangle to the circle's center
        closest_x = clamp(self.world_x, car_world_rect.left, car_world_rect.right)
        closest_y = clamp(self.world_y, car_world_rect.top, car_world_rect.bottom)

        # Calculate squared distance between the circle's center and this closest point
        distance_x = self.world_x - closest_x
        distance_y = self.world_y - closest_y
        distance_squared = (distance_x * distance_x) + (distance_y * distance_y)

        # If the distance is less than the circle's radius squared, an intersection occurs
        return distance_squared < (self.radius * self.radius)

    def draw(self, surface, camera_offset_x, camera_offset_y):
        """Draws the circular ramp as a solid object."""
        screen_x = int(self.world_x - camera_offset_x + const.CENTER_X)
        screen_y = int(self.world_y - camera_offset_y + const.CENTER_Y)
        screen_radius = int(self.radius) # Assuming 1:1 world to screen scale for radius

        # Culling: Check if the ramp is off-screen
        # A simple check using screen coordinates and radius
        if not (-screen_radius < screen_x < const.SCREEN_WIDTH + screen_radius and \
                -screen_radius < screen_y < const.SCREEN_HEIGHT + screen_radius):
            return # Ramp is definitely off-screen

        if screen_radius < 1: # Don't draw if too small to see
            return

        # Draw the main ramp surface (circle)
        pygame.draw.circle(surface, const.RAMP_COLOR, (screen_x, screen_y), screen_radius)
        
        # Draw a border to give it some definition
        pygame.draw.circle(surface, const.RAMP_BORDER_COLOR, (screen_x, screen_y), screen_radius, 3) # Border thickness

        # Optional: Add simple shading for a 3D effect
        # Example: A slightly darker inner circle to suggest depth or a concave shape
        # inner_shade_radius = int(screen_radius * 0.8)
        # if inner_shade_radius > 2:
        #     inner_shade_color_rgb = [max(0, c - 20) for c in const.RAMP_COLOR[:3]]
        #     pygame.draw.circle(surface, inner_shade_color_rgb, (screen_x, screen_y), inner_shade_radius)


    def draw_debug(self, surface, camera_offset_x, camera_offset_y):
        """Draws the ramp's outline for debugging purposes."""
        if not const.DEBUG_DRAW_RAMPS:
            return
            
        screen_x = int(self.world_x - camera_offset_x + const.CENTER_X)
        screen_y = int(self.world_y - camera_offset_y + const.CENTER_Y)
        screen_radius = int(self.radius)

        if screen_radius < 1:
            return
        
        # Culling check (same as in draw method)
        if not (-screen_radius < screen_x < const.SCREEN_WIDTH + screen_radius and \
                -screen_radius < screen_y < const.SCREEN_HEIGHT + screen_radius):
            return

        pygame.draw.circle(surface, const.RAMP_DEBUG_COLOR, (screen_x, screen_y), screen_radius, 2)


# --- MudPatch Class (Remains Unchanged from your provided file) ---
class MudPatch:
    def __init__(self, world_x, world_y, size):
        self.world_x = world_x; self.world_y = world_y; self.size = size; self.color = const.MUD_COLOR; self.border_color = const.DARK_MUD_COLOR
        self.points_rel = self._generate_random_points(size); self.points_world = [(x + world_x, y + world_y) for x, y in self.points_rel]
        self.rect = self._calculate_bounding_rect(self.points_world)
    def _generate_random_points(self, size):
        points = []; num_vertices = random.randint(const.MIN_MUD_VERTICES, const.MAX_MUD_VERTICES); avg_radius = size / 2.0
        for i in range(num_vertices):
            angle = (i / num_vertices) * 2 * math.pi; radius_variation = random.uniform(1.0 - const.MUD_RADIUS_VARIATION, 1.0 + const.MUD_RADIUS_VARIATION)
            radius = avg_radius * radius_variation; angle += random.uniform(-0.5 / num_vertices, 0.5 / num_vertices) * 2 * math.pi
            x = radius * math.cos(angle); y = radius * math.sin(angle); points.append((x, y))
        points.sort(key=lambda p: math.atan2(p[1], p[0])); return points
    def _calculate_bounding_rect(self, points_list):
        if not points_list: return pygame.Rect(self.world_x, self.world_y, 0, 0)
        min_x = min(p[0] for p in points_list); max_x = max(p[0] for p in points_list); min_y = min(p[1] for p in points_list); max_y = max(p[1] for p in points_list)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    def draw(self, surface, offset_x, offset_y):
        screen_points = [(int(px - offset_x + const.CENTER_X), int(py - offset_y + const.CENTER_Y)) for px, py in self.points_world]
        screen_rect = self.rect.move(-offset_x + const.CENTER_X, -offset_y + const.CENTER_Y)
        if screen_rect.colliderect(surface.get_rect()):
            if len(screen_points) > 2: pygame.draw.polygon(surface, self.color, screen_points); pygame.draw.polygon(surface, self.border_color, screen_points, 2)
    def check_collision(self, point): # This is point collision for mud, car uses rect for broad phase
        if not self.rect.collidepoint(point): return False
        x, y = point; n = len(self.points_world); inside = False; p1x, p1y = self.points_world[0]
        for i in range(n + 1):
            p2x, p2y = self.points_world[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y: xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        else: xinters = p1x 
                        if p1x == p2x or x <= xinters: inside = not inside
            p1x, p1y = p2x, p2y
        return inside

# --- Checkpoint Class (Remains Unchanged from your provided file) ---
class Checkpoint: 
    def __init__(self, world_x, world_y, index, is_gate=False):
        self.world_x = world_x; self.world_y = world_y; self.index = index; self.radius = const.CHECKPOINT_RADIUS; self.is_gate = is_gate
        self.color = const.START_FINISH_MARKER_COLOR if is_gate else const.CHECKPOINT_COLOR
    def draw(self, surface, offset_x, offset_y, is_next):
        screen_x = int(self.world_x - offset_x + const.CENTER_X); screen_y = int(self.world_y - offset_y + const.CENTER_Y)
        if -self.radius < screen_x < const.SCREEN_WIDTH + self.radius and -self.radius < screen_y < const.SCREEN_HEIGHT + self.radius:
            color_to_use = self.color
            if is_next and not self.is_gate:
                color_to_use = const.NEXT_CHECKPOINT_INDICATOR_COLOR
                pygame.draw.circle(surface, color_to_use, (screen_x, screen_y), self.radius + 5, 2) 
            pygame.draw.circle(surface, color_to_use, (screen_x, screen_y), self.radius)
            pygame.draw.circle(surface, const.BLACK, (screen_x, screen_y), self.radius, 1) 
            if not self.is_gate and self.index >= 0: 
                font_size = 24 
                cp_font = pygame.font.Font(None, font_size) 
                text_surf = cp_font.render(str(self.index + 1), True, const.BLACK) 
                text_rect = text_surf.get_rect(center=(screen_x, screen_y)); surface.blit(text_surf, text_rect)