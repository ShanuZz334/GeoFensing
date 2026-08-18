"""
GeoFace Faculty Authentication System - Holiday Model
"""

from datetime import datetime

from ..extensions import db


class Holiday(db.Model):
    """Represents a public holiday or non-working day."""

    __tablename__ = "holidays"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    is_full_day = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        """Serialize holiday to dictionary."""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "name": self.name,
            "is_full_day": self.is_full_day,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Holiday {self.date}: {self.name}>"
