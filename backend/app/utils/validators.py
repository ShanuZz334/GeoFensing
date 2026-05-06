"""
GeoFace Faculty Authentication System - Input Validators
"""

import re
from typing import Any, Dict, List, Optional, Tuple


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_login_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate /login request body.

    Returns:
        (valid: bool, error_message: Optional[str])
    """
    if not data:
        return False, "Request body is required"

    reg_no = data.get("reg_no")
    password = data.get("password")

    if not reg_no:
        return False, "Registration number is required"
    if not isinstance(reg_no, str):
        return False, "Registration number must be a string"
    if not password:
        return False, "Password is required"
    if not isinstance(password, str) or len(password) < 6:
        return False, "Password must be at least 6 characters"

    return True, None


def validate_verify_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate /verify request body.

    Returns:
        (valid: bool, error_message: Optional[str])
    """
    if not data:
        return False, "Request body is required"

    frames = data.get("frames")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timestamp = data.get("timestamp")

    # Frames validation
    if not frames:
        return False, "No frames provided"
    if not isinstance(frames, list) or len(frames) == 0:
        return False, "frames must be a non-empty array"
    if len(frames) > 50:
        return False, "Too many frames (max 50)"

    # Coordinates validation
    if latitude is None or longitude is None:
        return False, "GPS coordinates are required"
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False, "Invalid GPS coordinates"
    if not (-90 <= lat <= 90):
        return False, "Latitude out of range"
    if not (-180 <= lon <= 180):
        return False, "Longitude out of range"

    # Timestamp validation
    if timestamp is None:
        return False, "Timestamp is required"
    try:
        float(timestamp)
    except (TypeError, ValueError):
        return False, "Invalid timestamp format (UNIX epoch expected)"

    return True, None


def validate_teacher_register_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate admin teacher registration payload.
    face_encoding is required and must be a list of 512 floats.
    """
    if not data:
        return False, "Request body is required"

    for field in ("full_name", "email", "reg_no", "password", "department"):
        if not data.get(field):
            return False, f"{field} is required"

    if not validate_email(data["email"]):
        return False, "Invalid email format"
    # Strict password constraints
    password = data["password"]
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    # 1. No simple sequences
    simple_sequences = ["12345678", "abcdefgh", "123456789", "qwertyui", "password"]
    if any(seq in password.lower() for seq in simple_sequences):
        return False, "Password cannot be a simple sequence or common word"
        
    # 2. Cannot contain name or reg no
    name_parts = [p.lower() for p in data["full_name"].split() if len(p) > 2]
    if any(part in password.lower() for part in name_parts):
        return False, "Password cannot contain parts of your name"
        
    if data["reg_no"].strip().lower() in password.lower():
        return False, "Password cannot contain your Registration Number"

    encoding = data.get("face_encoding")
    if encoding is not None:
        if not isinstance(encoding, list) or len(encoding) != 512:
            return False, "face_encoding must be an array of exactly 512 floats"

    return True, None
