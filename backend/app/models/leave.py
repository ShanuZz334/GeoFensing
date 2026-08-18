"""
GeoFace Faculty Authentication System - Leave Model
"""

import uuid
from datetime import datetime

from ..extensions import db


from sqlalchemy.dialects.postgresql import UUID as pgUUID

class LeaveRequest(db.Model):
    """Represents a leave application submitted by a teacher."""

    __tablename__ = "leave_requests"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # We use a custom type mapping to handle SQLite (dev) vs Postgres (prod)
    teacher_id = db.Column(
        db.String(36).with_variant(pgUUID(as_uuid=False), 'postgresql'),
        db.ForeignKey("teachers.teacher_id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    leave_type = db.Column(db.String(20), nullable=False) # 'normal' or 'emergency'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_half_day = db.Column(db.Boolean, default=False, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending", nullable=False) # 'pending', 'approved', 'rejected'
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(
        db.String(36), 
        db.ForeignKey("admins.id", ondelete="SET NULL"), 
        nullable=True
    )

    # Relationships
    admin = db.relationship("Admin", backref="reviewed_leaves")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "leave_type": self.leave_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "is_half_day": self.is_half_day,
            "reason": self.reason,
            "status": self.status,
            "applied_at": self.applied_at.isoformat() + "Z",
            "reviewed_at": self.reviewed_at.isoformat() + "Z" if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by
        }
