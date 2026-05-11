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
        
        from .models.admin import Admin
        if Admin.query.count() == 0:
            head_admin_pass = app.config.get("ADMIN_PASSWORD", "admin123")
            head_admin_reg_no = app.config.get("HEAD_ADMIN_REG_NO", "ADMIN_001")
            head_admin_name = app.config.get("HEAD_ADMIN_NAME", "Head Admin")
            head_admin = Admin(
                name=head_admin_name,
                reg_no=head_admin_reg_no,
                password_hash=bcrypt.generate_password_hash(head_admin_pass).decode("utf-8"),
                is_head_admin=True
            )
            db.session.add(head_admin)
            db.session.commit()
            print(f"Seeded initial Head Admin with Reg No: {head_admin_reg_no}")

    return app

