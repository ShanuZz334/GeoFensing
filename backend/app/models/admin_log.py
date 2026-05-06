"""
GeoFace Authentication System - Admin Log Model
"""

from datetime import datetime

from ..extensions import db


class AdminLog(db.Model):
    """Represents an audit log for actions performed by administrators."""

    __tablename__ = "admin_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_reg_no = db.Column(db.String(100), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)  # JSON or simple text
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "admin_reg_no": self.admin_reg_no,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }
