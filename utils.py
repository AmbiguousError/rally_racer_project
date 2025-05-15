# utils.py
# This file contains general utility functions for the Rally Racer game.

import math

def deg_to_rad(degrees):
    """Converts degrees to radians."""
    return degrees * math.pi / 180.0

def rad_to_deg(radians):
    """Converts radians to degrees."""
    return radians * 180.0 / math.pi

def angle_difference(angle1, angle2):
    """Calculates the shortest difference between two angles in degrees."""
    return (angle1 - angle2 + 180) % 360 - 180

def normalize_angle(degrees):
    """Normalizes an angle to the range [0, 360) degrees."""
    return degrees % 360

def lerp(a, b, t):
    """Linear interpolation between a and b by a factor t."""
    return a + (b - a) * t

def distance_sq(p1, p2):
    """Calculates the squared Euclidean distance between two points (p1 and p2).
    Each point is a tuple (x, y).
    This is faster than distance() if you only need to compare distances.
    """
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2

def distance(p1, p2):
    """Calculates the Euclidean distance between two points (p1 and p2)."""
    return math.sqrt(distance_sq(p1,p2))

def clamp(value, min_val, max_val):
    """Clamps a value to be within the range [min_val, max_val]."""
    return max(min_val, min(value, max_val))

def check_line_crossing(p1_segment1, p2_segment1, p1_segment2, p2_segment2):
    """
    Checks if two line segments intersect.
    p1_segment1, p2_segment1: Define the first line segment.
    p1_segment2, p2_segment2: Define the second line segment.
    Each point is a tuple (x, y).
    """
    # Check bounding boxes first for a quick exit if no overlap
    if (max(p1_segment1[0], p2_segment1[0]) < min(p1_segment2[0], p2_segment2[0]) or
        min(p1_segment1[0], p2_segment1[0]) > max(p1_segment2[0], p2_segment2[0]) or
        max(p1_segment1[1], p2_segment1[1]) < min(p1_segment2[1], p2_segment2[1]) or
        min(p1_segment1[1], p2_segment1[1]) > max(p1_segment2[1], p2_segment2[1])):
        return False

    # Helper function to find orientation of ordered triplet (p, q, r).
    # 0 -> p, q and r are collinear
    # 1 -> Clockwise
    # 2 -> Counterclockwise
    def orientation(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - \
              (q[0] - p[0]) * (r[1] - q[1])
        if abs(val) < 1e-9:  # Using a small epsilon for float comparison
            return 0  # Collinear
        return 1 if val > 0 else 2  # Clockwise or Counterclockwise

    # Find the four orientations needed for general and special cases
    o1 = orientation(p1_segment1, p2_segment1, p1_segment2)
    o2 = orientation(p1_segment1, p2_segment1, p2_segment2)
    o3 = orientation(p1_segment2, p2_segment2, p1_segment1)
    o4 = orientation(p1_segment2, p2_segment2, p2_segment1)

    # General case: segments intersect if orientations are different
    if o1 != o2 and o3 != o4:
        return True

    # Special Cases for collinear points:
    # Check if p1_segment2 lies on segment p1_segment1-p2_segment1
    if o1 == 0 and on_segment(p1_segment1, p1_segment2, p2_segment1): return True
    # Check if p2_segment2 lies on segment p1_segment1-p2_segment1
    if o2 == 0 and on_segment(p1_segment1, p2_segment2, p2_segment1): return True
    # Check if p1_segment1 lies on segment p1_segment2-p2_segment2
    if o3 == 0 and on_segment(p1_segment2, p1_segment1, p2_segment2): return True
    # Check if p2_segment1 lies on segment p1_segment2-p2_segment2
    if o4 == 0 and on_segment(p1_segment2, p2_segment1, p2_segment2): return True

    return False  # Doesn't fall in any of the above cases

def on_segment(p, q, r):
    """
    Given three collinear points p, q, r, the function checks if
    point q lies on line segment 'pr'.
    """
    if (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
        q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1])):
        return True
    return False

# You can add other general utility functions here as your project grows.
# For example, functions for:
# - Vector math (normalize vector, dot product, cross product if needed for 3D later)
# - Random number generation with specific distributions if `random` module isn't enough
# - Text rendering helpers (e.g., drawing multi-line text, text with background)
