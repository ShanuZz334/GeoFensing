import os
import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)

GEOFENCE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'geofence.json')

def get_polygon():
    """
    Get the geofence polygon.
    First tries to read from geofence.json.
    Falls back to current_app.config['GEOFENCE_POLYGON'].
    """
    if os.path.exists(GEOFENCE_FILE):
        try:
            with open(GEOFENCE_FILE, 'r') as f:
                data = json.load(f)
                if 'polygon' in data and isinstance(data['polygon'], list):
                    return data['polygon']
        except Exception as e:
            logger.error(f"Failed to read {GEOFENCE_FILE}: {e}")
    
    return current_app.config.get("GEOFENCE_POLYGON")

def save_polygon(polygon):
    """
    Save the geofence polygon to geofence.json.
    """
    if not isinstance(polygon, list):
        raise ValueError("Polygon must be a list of coordinates")
        
    try:
        with open(GEOFENCE_FILE, 'w') as f:
            json.dump({'polygon': polygon}, f)
        return True
    except Exception as e:
        logger.error(f"Failed to write {GEOFENCE_FILE}: {e}")
        return False
