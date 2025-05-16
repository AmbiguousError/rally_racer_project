# rally_racer_project/utils.py
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
    """
    Calculates the squared Euclidean distance between two points (p1 and p2).
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
    # Bounding box check
    if (max(p1_segment1[0], p2_segment1[0]) < min(p1_segment2[0], p2_segment2[0]) or
        min(p1_segment1[0], p2_segment1[0]) > max(p1_segment2[0], p2_segment2[0]) or
        max(p1_segment1[1], p2_segment1[1]) < min(p1_segment2[1], p2_segment2[1]) or
        min(p1_segment1[1], p2_segment1[1]) > max(p1_segment2[1], p2_segment2[1])):
        return False

    def orientation(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - \
              (q[0] - p[0]) * (r[1] - q[1])
        if abs(val) < 1e-9: return 0  # Collinear (using epsilon for float comparison)
        return 1 if val > 0 else 2  # Clockwise or Counterclockwise

    o1 = orientation(p1_segment1, p2_segment1, p1_segment2)
    o2 = orientation(p1_segment1, p2_segment1, p2_segment2)
    o3 = orientation(p1_segment2, p2_segment2, p1_segment1)
    o4 = orientation(p1_segment2, p2_segment2, p2_segment1)

    if o1 != o2 and o3 != o4:
        return True # General case: segments intersect

    # Special Cases for collinear points:
    if o1 == 0 and on_segment(p1_segment1, p1_segment2, p2_segment1): return True
    if o2 == 0 and on_segment(p1_segment1, p2_segment2, p2_segment1): return True
    if o3 == 0 and on_segment(p1_segment2, p1_segment1, p2_segment2): return True
    if o4 == 0 and on_segment(p1_segment2, p2_segment1, p2_segment2): return True

    return False

def on_segment(p, q, r):
    """
    Given three collinear points p, q, r, the function checks if
    point q lies on line segment 'pr'.
    """
    if (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
        q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1])):
        return True
    return False

# --- NEW FUNCTION (added for road collision avoidance logic) ---
def point_segment_distance_sq(p, a, b):
    """
    Calculates the squared perpendicular distance from a point p to a line segment ab.
    Also handles cases where the closest point on the line ab is one of the endpoints a or b.
    p, a, b are tuples (x, y).
    Returns the squared distance.
    """
    px, py = p
    ax, ay = a
    bx, by = b

    ab_x = bx - ax
    ab_y = by - ay
    ap_x = px - ax
    ap_y = py - ay

    len_sq_ab = ab_x * ab_x + ab_y * ab_y

    if len_sq_ab == 0:
        return ap_x * ap_x + ap_y * ap_y

    t = (ap_x * ab_x + ap_y * ab_y) / len_sq_ab
    closest_x, closest_y = 0, 0

    if t < 0:
        closest_x, closest_y = ax, ay
    elif t > 1:
        closest_x, closest_y = bx, by
    else:
        closest_x = ax + t * ab_x
        closest_y = ay + t * ab_y
    
    dist_sq = (px - closest_x)**2 + (py - closest_y)**2
    return dist_sq

# --- NEW FUNCTION (added for car on_road detection logic) ---
def is_point_in_polygon(point, polygon_vertices):
    """
    Checks if a point is inside a polygon using the ray casting algorithm.
    point: tuple (x, y)
    polygon_vertices: list of tuples [(x1, y1), (x2, y2), ...]
    Returns: True if the point is in the polygon, False otherwise.
    """
    x, y = point
    n = len(polygon_vertices)
    inside = False

    if n < 3: # A polygon must have at least 3 vertices
        return False

    p1x, p1y = polygon_vertices[0]
    for i in range(n + 1):
        p2x, p2y = polygon_vertices[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y: # Check if the edge is not horizontal
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    # For horizontal lines, this xinters calculation might be problematic if y == p1y == p2y.
                    # However, the outer conditions y > min and y <= max should handle horizontal lines correctly
                    # by only proceeding if y is between the line's y-range (which is a single value for horizontal).
                    # If p1y == p2y (horizontal segment), the xinters calculation divides by zero.
                    # The point-in-polygon test handles horizontal segments implicitly.
                    # If p1y == p2y, this branch is only entered if y is exactly on that horizontal line.
                    # Then it checks if x <= max(p1x,p2x). If also x >= min(p1x,p2x), then the point (x,y) is on the horizontal segment.
                    # A ray from point (x,y) to the right would then either cross it (if x is to the left of segment) or not.
                    # The standard ray casting algorithm handles horizontal edges correctly by either counting them
                    # specially or by ensuring rays don't pass exactly through vertices.
                    # This implementation relies on the crossing count.

                    # A more robust way for xinters if p1y == p2y (horizontal segment):
                    # if p1y == p2y: # Horizontal segment
                    #    if y == p1y: # Point y is on the segment's y-level
                    #        # No crossing for horizontal segment unless endpoint, handled by vertex checks usually
                    #        # This simple version might miscount if ray aligns with edge
                    #        pass # Effectively no crossing for horizontal segments in this simple test
                    # else: # Non-horizontal
                    #    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x

                    # Simplified: if the edge is horizontal (p1y == p2y), this specific crossing test part
                    # doesn't robustly handle it for ray casting unless y is *not* equal to p1y.
                    # The original logic is mostly standard.
                    if p1y != p2y:
                         xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    elif y == p1y and x <= max(p1x, p2x) and min(p1x,p2x) <= x : # Point on horizontal segment, no "crossing" in standard sense
                        # This case might require specific handling if ray passes *along* horizontal segment
                        # For simplicity in this version, we assume general position.
                        # Most standard libraries might perturb y slightly or handle vertices explicitly.
                        # Let's stick to the common algorithm:
                        p1x,p1y=p2x,p2y # move to next segment if it's perfectly horizontal and point is on its y
                        continue


                    if p1x == p2x or x <= xinters: # If edge is vertical OR point is to the left of intersection
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside