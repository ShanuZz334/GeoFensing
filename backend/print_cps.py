import sys
import os
sys.path.insert(0, os.getcwd())
from app import create_app
app = create_app()
from app.models import EventCheckpoint
import datetime
with app.app_context():
    cps = EventCheckpoint.query.all()
    print("CURRENT UTC TIME:", datetime.datetime.utcnow())
    for cp in cps:
        print(f"ID: {cp.id}, Name: {cp.name}, Starts: {cp.starts_at}, Expires: {cp.expires_at}")
