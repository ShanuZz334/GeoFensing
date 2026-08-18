"""
GeoFace Faculty Authentication System - Teacher Model
"""

import uuid
from datetime import datetime

from ..extensions import db


class Teacher(db.Model):
    """Represents a registered faculty member."""

    __tablename__ = "teachers"

    teacher_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    reg_no = db.Column(db.String(100), unique=True, nullable=True, index=True)
    department = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(100), nullable=True)
    phone_no = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.Text, nullable=True)
    locked_device_id = db.Column(db.String(255), nullable=True)
    # Stored as JSON array of 512 floats (InsightFace encoding)
    face_encoding = db.Column(db.JSON, nullable=True)
    # Optional: per-teacher geofence override
    college_latitude = db.Column(db.Float, nullable=True)
    college_longitude = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    setup_complete = db.Column(db.Boolean, default=False, nullable=False)
    # Face re-registration window — admin grants a 4hr window for teacher to re-scan face
    face_reregister_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationship
    attendance_logs = db.relationship(
        "AttendanceLog",
        backref="teacher",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_encoding: bool = False) -> dict:
        """Serialize teacher to dictionary."""
        now = datetime.utcnow()
        face_reregister_allowed = (
            self.face_reregister_until is not None
            and self.face_reregister_until > now
        )
        data = {
            "teacher_id": self.teacher_id,
            "full_name": self.full_name,
            "email": self.email,
            "reg_no": self.reg_no,
            "department": self.department,
            "role": self.role,
            "phone_no": self.phone_no,
            "is_device_locked": self.locked_device_id is not None,
            "is_active": self.is_active,
            "setup_complete": self.setup_complete,
            "profile_pic": self.profile_pic,
            "has_face_encoding": bool(self.face_encoding and any(v != 0 for v in self.face_encoding)),
            "face_reregister_allowed": face_reregister_allowed,
            "face_reregister_until": self.face_reregister_until.isoformat() if self.face_reregister_until and face_reregister_allowed else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_encoding:
            data["face_encoding"] = self.face_encoding
        return data

    def __repr__(self) -> str:
        return f"<Teacher {self.teacher_id}: {self.email}>"
