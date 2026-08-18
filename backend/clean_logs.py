import os
from dotenv import load_dotenv
load_dotenv()

# Override the database host for local execution
db_url = os.environ.get("DATABASE_URL", "")
if "@db:" in db_url:
    os.environ["DATABASE_URL"] = db_url.replace("@db:", "@localhost:")

from app import create_app
from app.extensions import db
from app.models.admin_log import AdminLog

app = create_app()
with app.app_context():
    logs = AdminLog.query.filter(AdminLog.action == 'UPDATE_SETTINGS').all()
    for log in logs:
        if log.details and len(log.details) > 200:
            log.details = log.details[:197] + "..."
    db.session.commit()
    print("Cleaned up database audit logs.")
