import os
import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)

GEOFENCE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'geofence.json')

def get_polygon():
    """
    Get the geofence polygon from DB settings.
    Falls back to current_app.config['GEOFENCE_POLYGON'].
    """
    from ..models.setting import Setting
    
    try:
        db_polygon = Setting.get("geofence_polygon")
        if db_polygon and isinstance(db_polygon, list):
            return db_polygon
    except Exception as e:
        logger.error(f"Failed to read geofence from DB: {e}")
        
    # Fallback to geofence.json if not in DB
    if os.path.exists(GEOFENCE_FILE):
        try:
            with open(GEOFENCE_FILE, 'r') as f:
                data = json.load(f)
                if 'polygon' in data and isinstance(data['polygon'], list):
                    # Migrate to DB in background
                    from ..extensions import db
                    try:
                        setting = Setting(key="geofence_polygon", value=data['polygon'])
                        db.session.add(setting)
                        db.session.commit()
                        logger.info("Migrated geofence from JSON to DB.")
                    except:
                        db.session.rollback()
                    return data['polygon']
        except Exception as e:
            logger.error(f"Failed to read {GEOFENCE_FILE}: {e}")
            
    return current_app.config.get("GEOFENCE_POLYGON")

def save_polygon(polygon):
    """
    Save the geofence polygon to DB settings.
    """
    if not isinstance(polygon, list):
        raise ValueError("Polygon must be a list of coordinates")
        
    from ..models.setting import Setting
    from ..extensions import db
    try:
        setting = Setting.query.get("geofence_polygon")
        if setting:
            setting.value = polygon
        else:
            setting = Setting(key="geofence_polygon", value=polygon)
            db.session.add(setting)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to write geofence to DB: {e}")
        db.session.rollback()
        return False
