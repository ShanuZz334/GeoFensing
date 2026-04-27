"""
GeoFace Faculty Authentication System - Geofencing Service

Implements Haversine distance formula to determine if a GPS coordinate
falls within the college campus radius.
"""

import math
from dataclasses import dataclass
from typing import Tuple, List, Optional


# Earth's mean radius in meters
_EARTH_RADIUS_M = 6_371_000.0


@dataclass
class GeoPoint:
    latitude: float
    longitude: float


def haversine_distance(point_a: GeoPoint, point_b: GeoPoint) -> float:
    """
    Calculate the great-circle distance between two GPS points using the
    Haversine formula.

    Returns:
        Distance in meters.
    """
    lat1 = math.radians(point_a.latitude)
    lat2 = math.radians(point_b.latitude)
    d_lat = math.radians(point_b.latitude - point_a.latitude)
    d_lon = math.radians(point_b.longitude - point_a.longitude)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return _EARTH_RADIUS_M * c


def is_inside_polygon(lat: float, lon: float, polygon: List[List[float]]) -> bool:
    """
    Check if a point is inside a polygon using the Ray Casting algorithm.
    """
    if not polygon:
        return False
    
    inside = False
    n = len(polygon)
    p1x, p1y = polygon[0][0], polygon[0][1]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n][0], polygon[i % n][1]
        if lon > min(p1y, p2y):
            if lon <= max(p1y, p2y):
                if lat <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (lon - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lat <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def point_to_segment_distance(lat: float, lon: float, p1: List[float], p2: List[float]) -> float:
    """
    Calculate the shortest distance (in meters) from a point to a line segment.
    """
    # Convert all to GeoPoints for haversine
    A = GeoPoint(p1[0], p1[1])
    B = GeoPoint(p2[0], p2[1])
    P = GeoPoint(lat, lon)

    # Vector calculation for projection
    # Using simple Euclidean approximation for small distances near boundaries
    # Since we are marked 'Inside', we are very close to the segment anyway.
    
    # 1 degree lat ~ 111,111 meters
    # 1 degree lon ~ 111,111 * cos(lat) meters
    cos_lat = math.cos(math.radians(lat))
    
    def to_meters_vec(p: GeoPoint):
        return (p.latitude * 111111, p.longitude * 111111 * cos_lat)

    v_a = to_meters_vec(A)
    v_b = to_meters_vec(B)
    v_p = to_meters_vec(P)

    # Segment vector SE = B - A
    se_x = v_b[0] - v_a[0]
    se_y = v_b[1] - v_a[1]
    
    # Point vector PE = P - A
    pe_x = v_p[0] - v_a[0]
    pe_y = v_p[1] - v_a[1]

    mag_sq = se_x**2 + se_y**2
    if mag_sq == 0:
        return haversine_distance(P, A)

    # t is the projection parameter
    t = (pe_x * se_x + pe_y * se_y) / mag_sq
    t = max(0, min(1, t))

    # Nearest point on segment
    nearest_x = v_a[0] + t * se_x
    nearest_y = v_a[1] + t * se_y
    
    dist = math.sqrt((v_p[0] - nearest_x)**2 + (v_p[1] - nearest_y)**2)
    return dist


def is_within_geofence(
    latitude: float,
    longitude: float,
    center_lat: float,
    center_lon: float,
    radius_meters: float,
    polygon: Optional[List[List[float]]] = None,
    buffer_meters: float = 15,
) -> Tuple[bool, float, str]:
    """
    Determine if a coordinate falls within the geofence.
    Supports both circular (fallback) and polygon boundaries.

    Returns:
        Tuple of (is_authorized, distance_m, status_code)
        status_code: "SUCCESS", "WARNING_NEAR_BOUNDARY", "FAILURE_OUTSIDE"
    """
    teacher_point = GeoPoint(latitude=latitude, longitude=longitude)
    
    # Use Polygon if provided
    if polygon and len(polygon) >= 3:
        inside = is_inside_polygon(latitude, longitude, polygon)
        
        # Calculate distance to the nearest wall (polygon segment)
        min_dist_to_wall = float('inf')
        for i in range(len(polygon)):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % len(polygon)]
            dist = point_to_segment_distance(latitude, longitude, p1, p2)
            if dist < min_dist_to_wall:
                min_dist_to_wall = dist
        
        # Determine authorization based on polygon containment OR buffer zone
        if inside:
            if min_dist_to_wall < buffer_meters:
                return True, round(min_dist_to_wall, 2), "WARNING_NEAR_BOUNDARY"
            return True, round(min_dist_to_wall, 2), "SUCCESS"
        else:
            # Outside mathematical polygon, but check if within buffer leeway
            if min_dist_to_wall <= buffer_meters:
                return True, round(min_dist_to_wall, 2), "WARNING_NEAR_BOUNDARY"
            
            # Completely outside, calculate distance to center for logging
            college_point = GeoPoint(latitude=center_lat, longitude=center_lon)
            distance = haversine_distance(teacher_point, college_point)
            return False, round(distance, 2), "FAILURE_OUTSIDE"

    # Fallback to circular geofence
    college_point = GeoPoint(latitude=center_lat, longitude=center_lon)
    distance = haversine_distance(teacher_point, college_point)
    inside = distance <= radius_meters

    status = "SUCCESS" if inside else "FAILURE_OUTSIDE"
    return inside, round(distance, 2), status
