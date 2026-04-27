"""
GeoFace Faculty Authentication System - Flask Application Factory
"""

from flask import Flask
from flask_cors import CORS

from .config import config_map
from .extensions import db, jwt, bcrypt


def create_app(config_name: str = "production") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    from .extensions import init_redis
    init_redis(app)

    # CORS — restrict to mobile app and admin panel origins in production
    CORS(
        app,
        origins=app.config.get("ALLOWED_ORIGINS", ["*"]),
        supports_credentials=True,
    )

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.verify import verify_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/")
    app.register_blueprint(verify_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Create DB tables on first run
    with app.app_context():
        db.create_all()

    return app
