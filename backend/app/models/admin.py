"""
GeoFace Authentication System - Admin Model
"""

import uuid
from datetime import datetime

from ..extensions import db


class Admin(db.Model):
    """Represents an administrator for the GeoFace system."""

    __tablename__ = "admins"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name = db.Column(db.String(200), nullable=False)
    reg_no = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_head_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "reg_no": self.reg_no,
            "is_head_admin": self.is_head_admin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }
