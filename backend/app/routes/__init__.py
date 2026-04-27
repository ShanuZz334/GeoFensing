# Routes package
from .auth import auth_bp
from .verify import verify_bp
from .admin import admin_bp

__all__ = ["auth_bp", "verify_bp", "admin_bp"]
