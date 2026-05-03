"""
GeoFace Faculty Authentication System - Setting Model
"""

from ..extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class Setting(db.Model):
    """Stores global application settings."""

    __tablename__ = "settings"

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(JSONB, nullable=False)

    def to_dict(self) -> dict:
        return {
            self.key: self.value
        }

    @classmethod
    def get_all(cls) -> dict:
        """Helper to get all settings as a dictionary."""
        settings = cls.query.all()
        result = {}
        for s in settings:
            result[s.key] = s.value
        return result
