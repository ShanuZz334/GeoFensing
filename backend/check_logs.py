from app import create_app
from app.extensions import db
from app.models import AttendanceLog
import json

app = create_app()
with app.app_context():
    logs = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc()).limit(10).all()
    out = []
    for log in logs:
        out.append({
            "timestamp": log.timestamp.isoformat(),
            "action_type": log.action_type,
            "status": log.status,
            "attendance_mark": log.attendance_mark
        })
    print(json.dumps(out, indent=2))