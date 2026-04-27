"""
GeoFace Faculty Authentication System - Application Entry Point
"""

import os
import logging

from dotenv import load_dotenv
load_dotenv()

from app import create_app

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

config_name = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = config_name == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
