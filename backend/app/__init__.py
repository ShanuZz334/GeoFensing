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
    
    @jwt.decode_key_loader
    def get_decode_key(header, payload):
        sub = payload.get("sub", "")
        if isinstance(sub, str) and sub.startswith("admin:"):
            return app.config["ADMIN_JWT_SECRET_KEY"]
        return app.config["JWT_SECRET_KEY"]

    @jwt.encode_key_loader
    def get_encode_key(identity):
        if isinstance(identity, str) and identity.startswith("admin:"):
            return app.config["ADMIN_JWT_SECRET_KEY"]
        return app.config["JWT_SECRET_KEY"]
    
    from .extensions import init_redis
    init_redis(app)

    import re
    origins = app.config.get("ALLOWED_ORIGINS", ["*"])
    
    # Allow any localhost port for Flutter web testing
    if isinstance(origins, list):
        origins.append(re.compile(r"http://localhost:\d+"))

    # CORS — restrict to mobile app and admin panel origins in production
    CORS(
        app,
        origins=origins,
        supports_credentials=True,
    )

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.verify import verify_bp
    from .routes.admin import admin_bp
    from .routes.checkpoints import checkpoints_bp

    app.register_blueprint(auth_bp, url_prefix="/")
    app.register_blueprint(verify_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(checkpoints_bp, url_prefix="/")


    # Initialize background scheduler
    if not app.config.get("TESTING") and not app.debug:
        # Avoid running multiple schedulers in dev reloading mode
        from .scheduler import init_scheduler
        init_scheduler(app)

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

