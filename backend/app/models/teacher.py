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
    password_hash = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.Text, nullable=True)
    # Stored as JSON array of 128 floats (face_recognition encoding)
    face_encoding = db.Column(db.JSON, nullable=True)
    # Optional: per-teacher geofence override
    college_latitude = db.Column(db.Float, nullable=True)
    college_longitude = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
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
        data = {
            "teacher_id": self.teacher_id,
            "full_name": self.full_name,
            "email": self.email,
            "reg_no": self.reg_no,
            "department": self.department,
            "is_active": self.is_active,
            "profile_pic": self.profile_pic,
            "has_face_encoding": self.face_encoding is not None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_encoding:
            data["face_encoding"] = self.face_encoding
        return data

    def __repr__(self) -> str:
        return f"<Teacher {self.teacher_id}: {self.email}>"
