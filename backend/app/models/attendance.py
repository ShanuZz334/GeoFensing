"""
GeoFace Faculty Authentication System - Attendance Log Model
"""

import uuid
from datetime import datetime

from ..extensions import db


class AttendanceLog(db.Model):
    """Records each verification attempt and its outcome."""

    __tablename__ = "attendance_logs"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    teacher_id = db.Column(
        db.String(36),
        db.ForeignKey("teachers.teacher_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    # "success" or "failure"
    status = db.Column(
        db.String(20),
        nullable=False,
        default="failure",
    )
    # Human-readable failure reason or "Verification successful"
    reason = db.Column(db.String(500), nullable=False, default="")
    # Number of frames submitted
    frames_count = db.Column(db.Integer, nullable=True)
    # Pipeline stage that failed (for analytics)
    failure_stage = db.Column(db.String(100), nullable=True)

    def to_dict(self) -> dict:
        """Serialize attendance log to dictionary."""
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.full_name if self.teacher else None,
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "reason": self.reason,
            "frames_count": self.frames_count,
            "failure_stage": self.failure_stage,
        }

    def __repr__(self) -> str:
        return f"<AttendanceLog {self.id}: {self.teacher_id} → {self.status}>"
