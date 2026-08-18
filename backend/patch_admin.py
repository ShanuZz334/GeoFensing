with open("app/routes/admin.py", "a") as f:
    f.write("""

@admin_bp.route("/leaves", methods=["GET"])
@jwt_required()
def get_admin_leaves():
    \"\"\"GET /admin/leaves — list leave requests.\"\"\"
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
        
    from ..models import LeaveRequest, Teacher
    
    status_filter = request.args.get("status")
    query = LeaveRequest.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    leaves = query.order_by(LeaveRequest.applied_at.desc()).all()
        
    result = []
    for l in leaves:
        d = l.to_dict()
        teacher = Teacher.query.get(l.teacher_id)
        d['teacher_name'] = teacher.full_name if teacher else "Unknown"
        d['teacher_reg_no'] = teacher.reg_no if teacher else "N/A"
        result.append(d)
        
    return jsonify({"leaves": result}), 200

@admin_bp.route("/leaves/<id>", methods=["PATCH"])
@jwt_required()
def update_leave_status(id: str):
    \"\"\"PATCH /admin/leaves/<id> — approve or reject a leave request.\"\"\"
    admin_id = get_jwt_identity()
    if not _is_admin(admin_id):
        return jsonify({"error": "Admin access required"}), 403
        
    from ..models import LeaveRequest
    leave = LeaveRequest.query.get_or_404(id)
    
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    
    if new_status not in ["approved", "rejected"]:
        return jsonify({"error": "Invalid status. Must be 'approved' or 'rejected'"}), 400
        
    leave.status = new_status
    leave.reviewed_at = datetime.utcnow()
    leave.reviewed_by = admin_id
    
    db.session.commit()
    
    # Log the action
    _log_admin_action(admin_id, f"{new_status.capitalize()} leave request for teacher {leave.teacher_id}")
    
    return jsonify({"message": f"Leave {new_status} successfully", "leave": leave.to_dict()}), 200
""")
