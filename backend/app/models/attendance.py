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
    # "check_in", "check_out", or "demo_test"
    action_type = db.Column(db.String(20), nullable=True)
    # "present", "half_day", "absent", or "flagged" (late check-in pending admin review)
    attendance_mark = db.Column(db.String(20), nullable=False, default="present")
    # Indicates if an admin has resolved the alert triggered by this log
    is_alert_resolved = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self) -> dict:
        """Serialize attendance log to dictionary."""
        if self.attendance_mark == "absent":
            status_display = "ABSENT"
        else:
            status_display = self.status.upper()
            if self.action_type == "demo_test":
                status_display = "DEMO TEST"
            elif self.status == "success":
                if self.attendance_mark == "leave":
                    status_display = "LEAVE"
                elif self.action_type == "check_in":
                    status_display = "CHECK-IN SUCCESS"
                elif self.action_type == "check_out":
                    if self.attendance_mark == "present":
                        status_display = "FULL DAY"
                    elif self.attendance_mark == "half_day":
                        status_display = "HALF DAY"
                    else:
                        status_display = self.attendance_mark.upper().replace("_", " ")
                else:
                    status_display = self.attendance_mark.upper().replace("_", " ")

        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.full_name if self.teacher else None,
            "reg_no": self.teacher.reg_no if self.teacher else None,
            "profile_pic": self.teacher.profile_pic if self.teacher else None,
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "status_display": status_display,
            "reason": self.reason,
            "action_type": self.action_type,
            "attendance_mark": self.attendance_mark,
            "frames_count": self.frames_count,
            "failure_stage": self.failure_stage,
        }

    def __repr__(self) -> str:
        return f"<AttendanceLog {self.id}: {self.teacher_id} → {self.status}>"
