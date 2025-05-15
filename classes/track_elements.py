# classes/track_elements.py
# This file defines classes for track elements like Ramps, MudPatches, and Checkpoints.

import pygame
import random
import math

import constants as const
from utils import deg_to_rad, lerp 

# Make sure Checkpoint and MudPatch classes are also in this file or imported correctly
# For brevity, I'm focusing on the Ramp class changes.
# class MudPatch: ... (as defined before)
# class Checkpoint: ... (as defined before)

class Ramp:
    """
    Represents a jump ramp on the track.
    """
    def __init__(self, world_x, world_y, width, height, angle_deg):
        self.world_x = world_x
        self.world_y = world_y
        self.width = width
        self.height = height 
        self.angle_rad = deg_to_rad(angle_deg)
        self.cos_a = math.cos(self.angle_rad)
        self.sin_a = math.sin(self.angle_rad)

        hw, hh = self.width / 2, self.height / 2
        self.corners_rel = [
            (-hw, -hh), (hw, -hh),
            (hw, hh), (-hw, hh)   
        ]
        
        self.corners_world = []
        for x_rel, y_rel in self.corners_rel:
            wx = self.world_x + (x_rel * self.cos_a - y_rel * self.sin_a)
            wy = self.world_y + (x_rel * self.sin_a + y_rel * self.cos_a)
            self.corners_world.append((wx, wy))
            
        self.rect = self._calculate_bounding_rect(self.corners_world)

    def _calculate_bounding_rect(self, points_list):
        if not points_list:
            return pygame.Rect(self.world_x, self.world_y, 0, 0)
        min_x = min(p[0] for p in points_list)
        max_x = max(p[0] for p in points_list)
        min_y = min(p[1] for p in points_list)
        max_y = max(p[1] for p in points_list)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def check_collision(self, car_world_rect):
        return self.rect.colliderect(car_world_rect)

    def draw(self, surface, camera_offset_x, camera_offset_y):
        """Draws the ramp as a solid object."""
        screen_points = []
        for px, py in self.corners_world:
            screen_x = int(px - camera_offset_x + const.CENTER_X)
            screen_y = int(py - camera_offset_y + const.CENTER_Y)
            screen_points.append((screen_x, screen_y))
        
        # Basic culling: check if the bounding box of the ramp is on screen
        screen_rect_approx = self.rect.move(-camera_offset_x + const.CENTER_X, -camera_offset_y + const.CENTER_Y)
        if not screen_rect_approx.colliderect(surface.get_rect()):
            return

        if len(screen_points) == 4: # Ensure it's a quadrilateral
            # Draw the main ramp surface
            pygame.draw.polygon(surface, const.RAMP_COLOR, screen_points)
            # Draw a border to give it some definition
            pygame.draw.polygon(surface, const.RAMP_BORDER_COLOR, screen_points, 3) # Border thickness 3

            # Optional: Add some simple shading or detail lines to suggest 3D form
            # For example, draw lines from "front" corners to "back" corners if perspective was different
            # For a top-down, you could draw lines indicating the slope direction or texture.
            # Let's add a line down the middle in the direction of the ramp's angle.
            mid_x1_rel = 0
            mid_y1_rel = -self.height / 2 * 0.8 # Start a bit from the edge
            mid_x2_rel = 0
            mid_y2_rel = self.height / 2 * 0.8  # End a bit before the edge

            # Rotate these mid-line points
            wm_x1 = self.world_x + (mid_x1_rel * self.cos_a - mid_y1_rel * self.sin_a)
            wm_y1 = self.world_y + (mid_x1_rel * self.sin_a + mid_y1_rel * self.cos_a)
            wm_x2 = self.world_x + (mid_x2_rel * self.cos_a - mid_y2_rel * self.sin_a)
            wm_y2 = self.world_y + (mid_x2_rel * self.sin_a + mid_y2_rel * self.cos_a)

            # Convert to screen coordinates
            sm_x1 = int(wm_x1 - camera_offset_x + const.CENTER_X)
            sm_y1 = int(wm_y1 - camera_offset_y + const.CENTER_Y)
            sm_x2 = int(wm_x2 - camera_offset_x + const.CENTER_X)
            sm_y2 = int(wm_y2 - camera_offset_y + const.CENTER_Y)
            
            pygame.draw.line(surface, const.RAMP_BORDER_COLOR, (sm_x1, sm_y1), (sm_x2, sm_y2), 1)


    def draw_debug(self, surface, camera_offset_x, camera_offset_y):
        """Draws the ramp's outline for debugging purposes."""
        # This can be kept separate if you want a different debug view
        if not const.DEBUG_DRAW_RAMPS: 
            return
            
        screen_points = []
        for px, py in self.corners_world:
            screen_x = int(px - camera_offset_x + const.CENTER_X)
            screen_y = int(py - camera_offset_y + const.CENTER_Y)
            screen_points.append((screen_x, screen_y))
        
        if len(screen_points) == 4: 
            pygame.draw.polygon(surface, const.RAMP_DEBUG_COLOR, screen_points, 2) 


# Ensure MudPatch and Checkpoint classes are also present in this file
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
    def check_collision(self, point):
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
