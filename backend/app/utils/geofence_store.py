import os
import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)

GEOFENCE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'geofence.json')

def get_geofence_config():
    """
    Get the geofence configuration from DB settings.
    Falls back to legacy geofence_polygon or current_app.config.
    """
    from ..models.setting import Setting
    
    try:
        db_config = Setting.get("geofence_config")
        if db_config and isinstance(db_config, dict):
            return db_config
    except Exception as e:
        logger.error(f"Failed to read geofence_config from DB: {e}")
        
    # Fallback to legacy geofence_polygon if config doesn't exist
    try:
        db_polygon = Setting.get("geofence_polygon")
        if db_polygon and isinstance(db_polygon, list):
            return {
                "mode": 1,
                "main_polygon": db_polygon,
                "sub_polygons": [],
                "checkpoints": []
            }
    except Exception as e:
        pass
        
    # Fallback to geofence.json if not in DB
    if os.path.exists(GEOFENCE_FILE):
        try:
            with open(GEOFENCE_FILE, 'r') as f:
                data = json.load(f)
                if 'polygon' in data and isinstance(data['polygon'], list):
                    return {
                        "mode": 1,
                        "main_polygon": data['polygon'],
                        "sub_polygons": [],
                        "checkpoints": []
                    }
        except Exception as e:
            logger.error(f"Failed to read {GEOFENCE_FILE}: {e}")
            
    # Final fallback to app config
    fallback_poly = current_app.config.get("GEOFENCE_POLYGON", [])
    return {
        "mode": 1,
        "main_polygon": fallback_poly,
        "sub_polygons": [],
        "checkpoints": []
    }

def save_geofence_config(config):
    """
    Save the complete geofence configuration to DB settings.
    """
    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")
        
    from ..models.setting import Setting
    from ..extensions import db
    try:
        setting = Setting.query.get("geofence_config")
        if setting:
            setting.value = config
        else:
            setting = Setting(key="geofence_config", value=config)
            db.session.add(setting)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to write geofence_config to DB: {e}")
        db.session.rollback()
        return False
