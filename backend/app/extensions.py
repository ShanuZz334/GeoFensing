"""
GeoFace Faculty Authentication System - Flask Extension Singletons
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
import redis

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
# Redis connection singleton
redis_client = None

def init_redis(app):
    global redis_client
    redis_client = redis.from_url(app.config.get("REDIS_URL", "redis://localhost:6379/0"))
