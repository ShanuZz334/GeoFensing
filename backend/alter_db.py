from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("Dropping extra leave columns from teachers...")
    try:
        db.session.execute(text("ALTER TABLE teachers DROP COLUMN extra_leaves;"))
        db.session.execute(text("ALTER TABLE teachers DROP COLUMN extra_half_leaves;"))
        db.session.execute(text("ALTER TABLE teachers DROP COLUMN extra_monthly_leaves;"))
        db.session.execute(text("ALTER TABLE teachers DROP COLUMN extra_half_monthly_leaves;"))
        db.session.commit()
        print("Success.")
    except Exception as e:
        print("Error or already dropped:", e)
        db.session.rollback()

    print("Creating all tables (including LeaveRequests)...")
    db.create_all()
    print("Done.")
