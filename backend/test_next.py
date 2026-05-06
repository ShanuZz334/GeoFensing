from app import create_app
from app.routes.verify import _get_next_action
app = create_app()
with app.app_context():
    # the teacher id from logs
    tid = "fcb28a09-c615-4f6d-b26c-fc873b2af259"
    action = _get_next_action(tid)
    print(f"NEXT ACTION IS: {action}")
