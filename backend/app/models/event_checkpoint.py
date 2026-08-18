"""
GeoFace Faculty Authentication System - Event Checkpoint Model
Stores temporary event/seminar/session checkpoints placed by admins.
"""

import uuid
from datetime import datetime
from ..extensions import db


class EventCheckpoint(db.Model):
    """A temporary geographic checkpoint for event/seminar attendance."""

    __tablename__ = "event_checkpoints"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name = db.Column(db.String(200), nullable=False)  # Event name e.g. "ML Seminar - Hall B"
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, nullable=False, default=50.0)  # meters

    # Who this checkpoint applies to
    restriction_type = db.Column(
        db.String(20), nullable=False, default="all"
    )  # 'all' | 'department' | 'faculty'
    departments = db.Column(db.JSON, nullable=True)  # list of dept strings
    faculty_reg_nos = db.Column(db.JSON, nullable=True)  # list of reg_no strings
    is_compulsory = db.Column(db.Boolean, default=False)

    # Timer
    starts_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    # Meta
    created_by = db.Column(db.String(36), nullable=True)  # admin_id
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def is_active(self):
        now = datetime.utcnow()
        return self.starts_at <= now <= self.expires_at

    def faculty_qualifies(self, teacher):
        """Return True if a given Teacher object qualifies for this checkpoint."""
        if self.restriction_type == "all":
            return True
        if self.restriction_type == "department":
            depts = self.departments or []
            return teacher.department in depts
        if self.restriction_type == "faculty":
            reg_nos = self.faculty_reg_nos or []
            return teacher.reg_no in reg_nos
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
            "radius": self.radius,
            "restriction_type": self.restriction_type,
            "departments": self.departments or [],
            "faculty_reg_nos": self.faculty_reg_nos or [],
            "is_compulsory": self.is_compulsory,
            "starts_at": self.starts_at.isoformat() + "Z",
            "expires_at": self.expires_at.isoformat() + "Z",
            "created_at": self.created_at.isoformat() + "Z",
            "is_active": self.is_active(),
        }

class EventAttendance(db.Model):
    """Tracks which faculty attended which event checkpoint."""
    
    __tablename__ = "event_attendance"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checkpoint_id = db.Column(db.String(36), db.ForeignKey("event_checkpoints.id", ondelete="CASCADE"), nullable=False)
    
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    teacher_id = db.Column(PG_UUID(as_uuid=False), db.ForeignKey("teachers.teacher_id", ondelete="CASCADE"), nullable=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="attended")
    
    # Relationships
    teacher = db.relationship("Teacher", backref=db.backref("event_attendances", lazy=True, cascade="all, delete"))
    checkpoint = db.relationship("EventCheckpoint", backref=db.backref("attendances", lazy=True, cascade="all, delete"))
    
    def to_dict(self):
        return {
            "id": self.id,
            "checkpoint_id": self.checkpoint_id,
            "teacher_id": self.teacher_id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "status": self.status,
        }

