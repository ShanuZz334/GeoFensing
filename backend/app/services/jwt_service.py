"""
GeoFace Faculty Authentication System - JWT Service
"""

from datetime import datetime, timezone
from typing import Optional

from flask import current_app
from flask_jwt_extended import decode_token
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


def verify_timestamp_freshness(client_timestamp: float) -> bool:
    """
    Check that a client-supplied UNIX timestamp is not stale.
    Prevents replay attacks by rejecting timestamps older than
    TIMESTAMP_MAX_AGE_SECONDS or more than 5 seconds in the future.

    Args:
        client_timestamp: UNIX epoch seconds from the mobile client.

    Returns:
        True if timestamp is fresh, False otherwise.
    """
    max_age = current_app.config.get("TIMESTAMP_MAX_AGE_SECONDS", 30)
    now_utc = datetime.now(timezone.utc).timestamp()
    delta = abs(now_utc - client_timestamp)
    return delta <= max_age


def get_teacher_id_from_token(token: str) -> Optional[str]:
    """
    Decode a JWT and return the teacher_id stored in the identity field.

    Args:
        token: Raw JWT string.

    Returns:
        teacher_id string if valid, None otherwise.
    """
    try:
        decoded = decode_token(token)
        return decoded.get("sub")
    except (ExpiredSignatureError, InvalidTokenError, Exception):
        return None
