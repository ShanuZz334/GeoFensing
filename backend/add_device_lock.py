from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("Adding locked_device_id to teachers...")
    try:
        db.session.execute(text("ALTER TABLE teachers ADD COLUMN locked_device_id VARCHAR(255);"))
        db.session.commit()
        print("Success.")
    except Exception as e:
        print("Error or already added:", e)
        db.session.rollback()
