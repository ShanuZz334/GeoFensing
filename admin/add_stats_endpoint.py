import os

filepath = r"C:\project\ALLBACKUP\GeoFense\backend\app\routes\admin.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

endpoint_code = """
@admin_bp.route("/teachers/<teacher_id>/stats", methods=["GET"])
@jwt_required()
def get_faculty_stats(teacher_id: str):
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    from ..models import Teacher
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({"error": "Faculty not found"}), 404
        
    from .verify import calculate_teacher_stats
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    stats = calculate_teacher_stats(teacher_id, month_start, is_sem=False)
    leaves_this_month = stats.get('approved_full_leaves', 0) + stats.get('approved_half_leaves', 0)
    current_cut_percent = stats.get('deduction_pct', 0.0)
    
    return jsonify({
        "leaves_taken": leaves_this_month,
        "cut_pct": current_cut_percent
    }), 200

"""

# Let's just append it to the end of the file
if "@admin_bp.route(\"/teachers/<teacher_id>/stats\"" not in content:
    with open(filepath, "a", encoding="utf-8") as f:
        f.write("\n" + endpoint_code)
    print("Added /teachers/<id>/stats endpoint to admin.py")
else:
    print("Endpoint already exists")
