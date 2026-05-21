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
    geofence_config: Optional[dict] = None,
    buffer_meters: float = 15,
    action_type: str = "check_in",
    teacher_dept: str = "",
) -> Tuple[bool, float, str]:
    """
    Determine if a coordinate falls within the geofence based on the active mode.
    
    Modes:
    1: Main polygon only.
    2: Main polygon + Department Sub-polygons (Check-in requires dept block, Check-out anywhere in main).
    3: Checkpoints (Check-in and Check-out requires being inside ANY checkpoint radius).
    
    Returns:
        Tuple of (is_authorized, distance_m, status_code)
        status_code: "SUCCESS", "WARNING_NEAR_BOUNDARY", "FAILURE_OUTSIDE", "FAILURE_OUTSIDE_DEPT"
    """
    teacher_point = GeoPoint(latitude=latitude, longitude=longitude)
    
    if not geofence_config:
        # Fallback to circular geofence
        college_point = GeoPoint(latitude=center_lat, longitude=center_lon)
        distance = haversine_distance(teacher_point, college_point)
        inside = distance <= radius_meters
        status = "SUCCESS" if inside else "FAILURE_OUTSIDE"
        return inside, round(distance, 2), status

    mode = geofence_config.get("mode", 1)
    
    # ── MODE 3: Checkpoints ──
    if mode == 3:
        checkpoints = geofence_config.get("checkpoints", [])
        if not checkpoints:
            return False, 999.0, "FAILURE_OUTSIDE"
            
        min_dist = float('inf')
        for cp in checkpoints:
            cp_point = GeoPoint(latitude=float(cp["lat"]), longitude=float(cp["lng"]))
            dist = haversine_distance(teacher_point, cp_point)
            if dist < min_dist:
                min_dist = dist
            if dist <= float(cp["radius"]):
                return True, round(dist, 2), "SUCCESS"
        
        return False, round(min_dist, 2), "FAILURE_OUTSIDE"

    # ── MODE 1 & 2: Main Polygon ──
    main_polygon = geofence_config.get("main_polygon", [])
    if not main_polygon or len(main_polygon) < 3:
        # Fallback to circular geofence
        college_point = GeoPoint(latitude=center_lat, longitude=center_lon)
        distance = haversine_distance(teacher_point, college_point)
        inside = distance <= radius_meters
        status = "SUCCESS" if inside else "FAILURE_OUTSIDE"
        return inside, round(distance, 2), status

    # Verify inside main polygon
    inside_main = is_inside_polygon(latitude, longitude, main_polygon)
    
    # Calculate distance to the nearest wall of main polygon
    min_dist_to_main_wall = float('inf')
    for i in range(len(main_polygon)):
        p1 = main_polygon[i]
        p2 = main_polygon[(i + 1) % len(main_polygon)]
        dist = point_to_segment_distance(latitude, longitude, p1, p2)
        if dist < min_dist_to_main_wall:
            min_dist_to_main_wall = dist
            
    in_main_or_buffer = inside_main or min_dist_to_main_wall <= buffer_meters
    main_status = "SUCCESS"
    if in_main_or_buffer and not inside_main:
        main_status = "WARNING_NEAR_BOUNDARY"
        
    if not in_main_or_buffer:
        # Completely outside main
        college_point = GeoPoint(latitude=center_lat, longitude=center_lon)
        distance_to_center = haversine_distance(teacher_point, college_point)
        return False, round(distance_to_center, 2), "FAILURE_OUTSIDE"

    # ── MODE 2 Check-in specific logic (Department Blocks) ──
    if mode == 2 and action_type == "check_in":
        sub_polygons = geofence_config.get("sub_polygons", [])
        dept_polygons = [sp for sp in sub_polygons if teacher_dept and teacher_dept in sp.get("departments", [])]
        
        # If the department has mapped polygons, strictly enforce them
        if dept_polygons:
            inside_any_dept = False
            for sp in dept_polygons:
                sp_coords = sp.get("polygon", [])
                if sp_coords and len(sp_coords) >= 3:
                    if is_inside_polygon(latitude, longitude, sp_coords):
                        inside_any_dept = True
                        break
            
            if not inside_any_dept:
                # Inside main but outside department block
                return False, round(min_dist_to_main_wall, 2), "FAILURE_OUTSIDE_DEPT"
                
    # Success for Mode 1, Mode 2 check-out, or Mode 2 check-in (inside dept block or no dept block mapped)
    return True, round(min_dist_to_main_wall, 2), main_status
