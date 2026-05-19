"""
GeoFace Faculty Authentication System - Configuration
"""

import os
import json
from datetime import timedelta


class BaseConfig:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production-min32chars!")
    DEBUG: bool = False
    TESTING: bool = False

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://geoface_user:geoface_pass@localhost:5432/geoface_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_POOL_SIZE: int = 10
    SQLALCHEMY_POOL_TIMEOUT: int = 30
    SQLALCHEMY_POOL_RECYCLE: int = 1800
    SQLALCHEMY_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # JWT
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-me-production!")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=24)
    JWT_ALGORITHM: str = "HS256"

    # Geofencing
    COLLEGE_LATITUDE: float = float(os.environ.get("COLLEGE_LATITUDE", "31.2536"))
    COLLEGE_LONGITUDE: float = float(os.environ.get("COLLEGE_LONGITUDE", "75.7037"))
    GEOFENCE_RADIUS_METERS: int = int(os.environ.get("GEOFENCE_RADIUS_METERS", "200"))
    
    # Polygon Geofencing
    GEOFENCE_POLYGON: list = json.loads(os.environ.get("GEOFENCE_POLYGON", "[]"))
    GEOFENCE_BUFFER_METERS: int = int(os.environ.get("GEOFENCE_BUFFER_METERS", "15"))

    # Face Recognition
    FACE_RECOGNITION_THRESHOLD: float = float(os.environ.get("FACE_RECOGNITION_THRESHOLD", "1.2"))
    MIN_FACE_FRAMES_RATIO: float = 0.25  # >25% of frames must have a face
    MAX_FRAMES: int = 12  # Limit frames processed per request (Reduced from 25 for speed)

    # Liveness Detection
    EAR_BLINK_THRESHOLD: float = 0.20   # More strict blink detection
    HEAD_MOVE_THRESHOLD: int = 5        # More sensitive head movement
    MIN_BLINK_COUNT: int = 1            # At least 1 blink required

    # Replay attack prevention
    TIMESTAMP_MAX_AGE_SECONDS: int = 30

    # CORS
    ALLOWED_ORIGINS: list = os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")

    # Admin
    HEAD_ADMIN_REG_NO: str = os.environ.get("HEAD_ADMIN_REG_NO", "ADMIN_001")
    HEAD_ADMIN_NAME: str = os.environ.get("HEAD_ADMIN_NAME", "Head Admin")
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "AdminPass@123")


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://geoface_user:geoface_pass@localhost:5432/geoface_db",
    )
    ALLOWED_ORIGINS = ["*"]


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(BaseConfig):
    """Production configuration — all values must come from env."""
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
