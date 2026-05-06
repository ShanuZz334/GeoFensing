from app import create_app
from app.models import Teacher
app = create_app()
with app.app_context():
    t = Teacher.query.filter_by(teacher_id="fcb28a09-c615-4f6d-b26c-fc873b2af259").first()
    print(t.full_name if t else "NOT FOUND")
