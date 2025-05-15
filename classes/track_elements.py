# classes/track_elements.py
# This file defines classes for track elements like Ramps, MudPatches, and Checkpoints.

import pygame
import random
import math

# Assuming constants.py and utils.py are in the parent directory or project root is in PYTHONPATH.
import constants as const
from utils import deg_to_rad, lerp # Import specific utility functions

class Ramp:
    """
    Represents a jump ramp on the track.
    """
    def __init__(self, world_x, world_y, width, height, angle_deg):
        """
        Initializes a Ramp object.

        Args:
            world_x (float): World x-coordinate of the ramp's center.
            world_y (float): World y-coordinate of the ramp's center.
            width (int): Width of the ramp.
            height (int): Height (or depth along its orientation) of the ramp.
            angle_deg (float): Orientation angle of the ramp in degrees.
        """
        self.world_x = world_x
        self.world_y = world_y
        self.width = width
        self.height = height # This is more like the 'length' of the ramp surface
        self.angle_rad = deg_to_rad(angle_deg)
        self.cos_a = math.cos(self.angle_rad)
        self.sin_a = math.sin(self.angle_rad)

        # Define corners relative to ramp's center (0,0) before rotation
        hw, hh = self.width / 2, self.height / 2
        # These corners define the rectangular surface of the ramp
        self.corners_rel = [
            (-hw, -hh),  # Top-left (if angle is 0)
            (hw, -hh),   # Top-right
            (hw, hh),    # Bottom-right
            (-hw, hh)    # Bottom-left
        ]
        
        # Calculate world coordinates of the corners
        self.corners_world = []
        for x_rel, y_rel in self.corners_rel:
            # Rotate and then translate
            wx = self.world_x + (x_rel * self.cos_a - y_rel * self.sin_a)
            wy = self.world_y + (x_rel * self.sin_a + y_rel * self.cos_a)
            self.corners_world.append((wx, wy))
            
        # Create a bounding rectangle for broad-phase collision detection
        self.rect = self._calculate_bounding_rect(self.corners_world)

    def _calculate_bounding_rect(self, points_list):
        """Calculates the AABB (Axis-Aligned Bounding Box) for a list of points."""
        if not points_list:
            # Fallback if no points, though this shouldn't happen for a ramp
            return pygame.Rect(self.world_x, self.world_y, 0, 0)
        
        min_x = min(p[0] for p in points_list)
        max_x = max(p[0] for p in points_list)
        min_y = min(p[1] for p in points_list)
        max_y = max(p[1] for p in points_list)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def check_collision(self, car_world_rect):
        """
        Checks for collision with a car's world bounding rectangle.
        This is a broad-phase check. More precise polygon collision could be added.
        """
        return self.rect.colliderect(car_world_rect)

    def draw_debug(self, surface, camera_offset_x, camera_offset_y):
        """Draws the ramp's outline for debugging purposes."""
        if not const.DEBUG_DRAW_RAMPS: # Check global debug flag
            return
            
        screen_points = []
        for px, py in self.corners_world:
            screen_x = int(px - camera_offset_x + const.CENTER_X)
            screen_y = int(py - camera_offset_y + const.CENTER_Y)
            screen_points.append((screen_x, screen_y))
        
        if len(screen_points) == 4: # Ensure it's a quadrilateral
            pygame.draw.polygon(surface, const.RAMP_DEBUG_COLOR, screen_points, 2) # Draw outline


class MudPatch:
    """
    Represents a mud patch on the track that affects car handling.
    """
    def __init__(self, world_x, world_y, size):
        """
        Initializes a MudPatch object.

        Args:
            world_x (float): World x-coordinate of the mud patch's approximate center.
            world_y (float): World y-coordinate.
            size (int): Approximate diameter of the mud patch.
        """
        self.world_x = world_x
        self.world_y = world_y
        self.size = size # Approximate overall size/diameter
        self.color = const.MUD_COLOR
        self.border_color = const.DARK_MUD_COLOR
        
        # Generate a list of points defining the irregular shape of the mud patch
        self.points_rel = self._generate_random_points(self.size)
        # Convert relative points to world coordinates
        self.points_world = [(x_rel + self.world_x, y_rel + self.world_y) for x_rel, y_rel in self.points_rel]
        
        self.rect = self._calculate_bounding_rect(self.points_world)

    def _generate_random_points(self, base_size):
        """Generates an irregular polygonal shape for the mud patch."""
        points = []
        num_vertices = random.randint(const.MIN_MUD_VERTICES, const.MAX_MUD_VERTICES)
        avg_radius = base_size / 2.0
        
        for i in range(num_vertices):
            angle_rad = (i / num_vertices) * 2 * math.pi
            # Vary radius for irregularity
            radius_variation = random.uniform(1.0 - const.MUD_RADIUS_VARIATION, 1.0 + const.MUD_RADIUS_VARIATION)
            current_radius = avg_radius * radius_variation
            # Slightly perturb angle for more irregularity
            angle_rad += random.uniform(-0.5 / num_vertices, 0.5 / num_vertices) * 2 * math.pi
            
            x = current_radius * math.cos(angle_rad)
            y = current_radius * math.sin(angle_rad)
            points.append((x, y))
            
        # Sort points by angle to ensure a non-self-intersecting polygon (simple convex hull approximation)
        # This is important for pygame.draw.polygon
        points.sort(key=lambda p: math.atan2(p[1], p[0]))
        return points

    def _calculate_bounding_rect(self, points_list):
        """Calculates the AABB for the mud patch points."""
        if not points_list:
            return pygame.Rect(self.world_x, self.world_y, 0, 0)
        min_x = min(p[0] for p in points_list)
        max_x = max(p[0] for p in points_list)
        min_y = min(p[1] for p in points_list)
        max_y = max(p[1] for p in points_list)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def draw(self, surface, camera_offset_x, camera_offset_y):
        """Draws the mud patch on the given surface."""
        # Convert world points to screen points
        screen_points = []
        for px, py in self.points_world:
            screen_x = int(px - camera_offset_x + const.CENTER_X)
            screen_y = int(py - camera_offset_y + const.CENTER_Y)
            screen_points.append((screen_x, screen_y))
        
        # Basic culling: check if the bounding box of the mud patch is on screen
        # This uses the mud patch's world rect and converts it to screen space
        screen_rect_approx = self.rect.move(-camera_offset_x + const.CENTER_X, -camera_offset_y + const.CENTER_Y)
        if not screen_rect_approx.colliderect(surface.get_rect()):
            return

        if len(screen_points) > 2: # Need at least 3 points for a polygon
            pygame.draw.polygon(surface, self.color, screen_points)
            pygame.draw.polygon(surface, self.border_color, screen_points, 2) # Draw border

    def check_collision(self, point_world):
        """
        Checks if a world point is inside the mud patch polygon (Point-in-Polygon test).
        Args:
            point_world (tuple): (x, y) world coordinates of the point to check (e.g., car center).
        Returns:
            bool: True if the point is inside the mud patch, False otherwise.
        """
        # First, a quick check using the bounding rectangle
        if not self.rect.collidepoint(point_world):
            return False

        # Ray casting algorithm (even-odd rule)
        # https://en.wikipedia.org/wiki/Point_in_polygon
        x, y = point_world
        num_vertices = len(self.points_world)
        inside = False
        
        p1x, p1y = self.points_world[0]
        for i in range(num_vertices + 1):
            p2x, p2y = self.points_world[i % num_vertices] # Loop back to the first vertex
            if y > min(p1y, p2y):                   # Point is between y-range of segment
                if y <= max(p1y, p2y):              # Point is between y-range of segment
                    if x <= max(p1x, p2x):          # Point is to the left of the segment's x-range
                        if p1y != p2y:              # Segment is not horizontal
                            # Calculate x-intersection of a horizontal ray from the point
                            x_intersection = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        else: # Segment is horizontal, x_intersection is effectively p1x or p2x
                            x_intersection = p1x 
                        
                        if p1x == p2x or x <= x_intersection: # Point is to the left of the intersection or segment is vertical
                            inside = not inside
            p1x, p1y = p2x, p2y # Move to the next edge
            
        return inside


class Checkpoint:
    """
    Represents a checkpoint or a start/finish line marker.
    """
    def __init__(self, world_x, world_y, index, is_gate=False):
        """
        Initializes a Checkpoint object.

        Args:
            world_x (float): World x-coordinate of the checkpoint's center.
            world_y (float): World y-coordinate.
            index (int): The numerical index of the checkpoint (0-based for actual course CPs).
                         -1 can be used for non-indexed gates like start/finish.
            is_gate (bool, optional): True if this is a start/finish line gate marker,
                                      False if it's a numbered course checkpoint. Defaults to False.
        """
        self.world_x = world_x
        self.world_y = world_y
        self.index = index # 0-based for actual checkpoints, -1 for S/F gates
        self.radius = const.CHECKPOINT_RADIUS # Visual radius on screen
        self.is_gate = is_gate # True for start/finish line markers
        
        if self.is_gate:
            self.color = const.START_FINISH_MARKER_COLOR
        else:
            self.color = const.CHECKPOINT_COLOR

    def draw(self, surface, camera_offset_x, camera_offset_y, is_next_target):
        """
        Draws the checkpoint on the given surface.

        Args:
            surface (pygame.Surface): The Pygame surface to draw on.
            camera_offset_x (float): Camera's world x-coordinate.
            camera_offset_y (float): Camera's world y-coordinate.
            is_next_target (bool): True if this checkpoint is the player's current next target.
        """
        screen_x = int(self.world_x - camera_offset_x + const.CENTER_X)
        screen_y = int(self.world_y - camera_offset_y + const.CENTER_Y)

        # Basic culling
        if not (-self.radius < screen_x < const.SCREEN_WIDTH + self.radius and \
                -self.radius < screen_y < const.SCREEN_HEIGHT + self.radius):
            return

        color_to_use = self.color
        if is_next_target and not self.is_gate:
            color_to_use = const.NEXT_CHECKPOINT_INDICATOR_COLOR
            # Draw an outer circle to highlight the next checkpoint
            pygame.draw.circle(surface, color_to_use, (screen_x, screen_y), self.radius + 5, 2) 
        
        pygame.draw.circle(surface, color_to_use, (screen_x, screen_y), self.radius)
        pygame.draw.circle(surface, const.BLACK, (screen_x, screen_y), self.radius, 1) # Border

        # Draw checkpoint number if it's not a gate
        if not self.is_gate and self.index >= 0:
            # Consider creating font objects once in main and passing them if performance is an issue
            font_size = 24 
            cp_font = pygame.font.Font(None, font_size) 
            text_surf = cp_font.render(str(self.index + 1), True, const.BLACK) # Display 1-based index
            text_rect = text_surf.get_rect(center=(screen_x, screen_y))
            surface.blit(text_surf, text_rect)

