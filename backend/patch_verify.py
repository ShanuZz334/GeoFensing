import re

with open("app/routes/verify.py", "r") as f:
    content = f.read()

# 1. Replace get_attendance_stats
new_stats = '''@verify_bp.route("/attendance/stats", methods=["GET"])
@jwt_required()
def get_attendance_stats():
    """GET /attendance/stats — returns attendance statistics for month and semester."""
    teacher_id = get_jwt_identity()
    now = datetime.now(timezone.utc)
    
    def get_stats_for_range(start_date, end_date=None, is_sem=False):
        teacher_id = get_jwt_identity()
        from ..models import LeaveRequest, Setting
        
        # Effective range
        effective_start = start_date
        effective_end = end_date or now
        
        # Generate all dates in range
        dates = []
        curr = effective_start.date()
        end_d = effective_end.date()
        while curr <= end_d:
            dates.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)

        # Get logs for teacher in range
        logs = AttendanceLog.query.filter(
            AttendanceLog.teacher_id == teacher_id,
            AttendanceLog.timestamp >= effective_start,
            AttendanceLog.timestamp <= effective_end
        ).order_by(AttendanceLog.timestamp.asc()).all()
        
        days_data = {d: [] for d in dates}
        for log in logs:
            date_str = log.timestamp.strftime("%Y-%m-%d")
            if date_str in days_data:
                days_data[date_str].append(log)
                
        # Get approved leaves
        approved_leaves = LeaveRequest.query.filter(
            LeaveRequest.teacher_id == teacher_id,
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= effective_end.date(),
            LeaveRequest.end_date >= effective_start.date()
        ).all()
        
        approved_leave_dates = {}
        emergency_leaves_used = 0
        for leave in approved_leaves:
            if leave.leave_type == 'emergency' and leave.start_date >= effective_start.date() and leave.start_date <= effective_end.date():
                emergency_leaves_used += 1
            curr_d = leave.start_date
            while curr_d <= leave.end_date:
                approved_leave_dates[curr_d.strftime("%Y-%m-%d")] = leave
                curr_d += timedelta(days=1)
            
        attended = 0
        absent = 0
        approved_full_leaves = 0
        approved_half_leaves = 0
        final_logs = []
        days_processed = 0
        
        settings_dict = Setting.get_all()
        full_day_deduction = float(settings_dict.get("full_day_deduction_pct", 3.0))
        half_day_deduction = float(settings_dict.get("half_day_deduction_pct", 1.5))
        emergency_deduction = float(settings_dict.get("emergency_leave_deduction_pct", 0.5))
        
        unapproved_absences = 0
        unapproved_half_days = 0

        for date_str in sorted(days_data.keys(), reverse=True):
            days_processed += 1
            day_logs = days_data[date_str]
            leave_for_day = approved_leave_dates.get(date_str)
            
            success_logs = [l for l in day_logs if l.status == "success"]
            success_log = success_logs[-1] if success_logs else None
            
            absent_logs = [l for l in day_logs if l.attendance_mark == "absent"]
            absent_log = absent_logs[-1] if absent_logs else None
            
            # If the teacher was granted an approved leave for this day
            if leave_for_day:
                if leave_for_day.is_half_day:
                    approved_half_leaves += 1
                    attended += 0.5
                else:
                    approved_full_leaves += 1
                
                final_logs.append({
                    "id": f"leave_{date_str}",
                    "teacher_id": teacher_id,
                    "timestamp": datetime.fromisoformat(date_str).replace(hour=12, tzinfo=timezone.utc).isoformat(),
                    "status": "success",
                    "status_display": "HALF LEAVE" if leave_for_day.is_half_day else "FULL LEAVE",
                    "action_type": "check_in",
                    "attendance_mark": "leave",
                    "reason": f"Approved {leave_for_day.leave_type.capitalize()} Leave"
                })
                continue

            if success_log:
                if success_log.attendance_mark == "half_day":
                    attended += 0.5
                    absent += 0.5
                    unapproved_half_days += 1
                else:
                    attended += 1
                final_logs.append(success_log.to_dict())
            elif absent_log:
                absent += 1
                unapproved_absences += 1
                final_logs.append(absent_log.to_dict())
            else:
                # Synthetic Absent (only if date <= today)
                synthetic_ts = datetime.fromisoformat(date_str).replace(hour=12, tzinfo=timezone.utc)
                if synthetic_ts.weekday() in [5, 6]:
                    continue  # Skip Saturday (5) and Sunday (6)

                # DO NOT mark absent for today if we haven't passed the absent_limit yet
                if date_str == now.strftime("%Y-%m-%d"):
                    rules = settings_dict.get("attendance_rules", {})
                    absent_limit = rules.get("absent_limit", "11:00")
                    current_time_str = datetime.now().strftime("%H:%M")
                    if current_time_str <= absent_limit:
                        continue

                absent += 1
                unapproved_absences += 1
                final_logs.append({
                    "id": f"syn_{date_str}",
                    "teacher_id": teacher_id,
                    "timestamp": synthetic_ts.isoformat(),
                    "status": "failure",
                    "status_display": "ABSENT",
                    "action_type": "check_in",
                    "attendance_mark": "absent",
                    "reason": "No record found for this day."
                })
        
        # Calculate salary deductions
        deduction_pct = 0.0
        if not is_sem:
            deduction_pct += unapproved_absences * full_day_deduction
            deduction_pct += unapproved_half_days * half_day_deduction
            deduction_pct += emergency_leaves_used * emergency_deduction

        return {
            "attended": attended,
            "absent": absent,
            "approved_full_leaves": approved_full_leaves,
            "approved_half_leaves": approved_half_leaves,
            "emergency_leaves_used": emergency_leaves_used,
            "deduction_pct": round(deduction_pct, 2),
            "unapproved_absences": unapproved_absences,
            "unapproved_half_days": unapproved_half_days,
            "total": days_processed,
            "logs": final_logs
        }

    # Monthly: From start of current month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Semester: From configured start date
    sem_start_str = Setting.get("semester_start_date")
    try:
        sem_start = datetime.fromisoformat(sem_start_str).replace(tzinfo=timezone.utc)
    except:
        sem_start = now - timedelta(days=180)
    
    res_monthly = get_stats_for_range(month_start, is_sem=False)
    res_semester = get_stats_for_range(sem_start, is_sem=True)
    
    return jsonify({
        "monthly": res_monthly,
        "semester": res_semester,
        "verification_limits": Setting.get_all().get("verification_limits", {
            "max_checkin_attempts": 4,
            "max_checkout_attempts": 10
        }),
        "support_contact": Setting.get("support_contact", {
            "phone": "8089602280",
            "email": "shanifshaz546@gmail.com"
        })
    }), 200

@verify_bp.route("/verify", methods=["POST"])'''

# Find the start and end of get_attendance_stats
start_idx = content.find('@verify_bp.route("/attendance/stats", methods=["GET"])')
end_idx = content.find('@verify_bp.route("/verify", methods=["POST"])')

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_stats + content[end_idx + len('@verify_bp.route("/verify", methods=["POST"])'):]

new_leaves = '''
@verify_bp.route("/leaves", methods=["GET"])
@jwt_required()
def get_leave_history():
    teacher_id = get_jwt_identity()
    from ..models import LeaveRequest
    leaves = LeaveRequest.query.filter_by(teacher_id=teacher_id).order_by(LeaveRequest.applied_at.desc()).all()
    
    return jsonify({
        "status": "success",
        "leaves": [l.to_dict() for l in leaves]
    }), 200

@verify_bp.route("/leaves", methods=["POST"])
@jwt_required()
def apply_leave():
    teacher_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "failure", "reason": "No data provided"}), 400
        
    leave_type = data.get("leave_type") # 'normal' or 'emergency'
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    is_half_day = data.get("is_half_day", False)
    reason = data.get("reason", "")
    
    if not leave_type or not start_date_str or not end_date_str:
        return jsonify({"status": "failure", "reason": "Missing required fields"}), 400
        
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"status": "failure", "reason": "Invalid date format, use YYYY-MM-DD"}), 400
        
    if start_date < datetime.utcnow().date() and leave_type == 'normal':
        return jsonify({"status": "failure", "reason": "Normal leave cannot be applied for past dates."}), 400
        
    if start_date > end_date:
        return jsonify({"status": "failure", "reason": "Start date cannot be after end date."}), 400
        
    from ..models import Setting, LeaveRequest
    
    # Validation Rules
    if leave_type == 'normal':
        # Must be at least 16 hours before start_date
        settings_dict = Setting.get_all()
        rules = settings_dict.get("attendance_rules", {})
        class_start = rules.get("class_start", "09:00")
        start_dt = datetime.combine(start_date, datetime.strptime(class_start, "%H:%M").time())
        if (start_dt - datetime.now()).total_seconds() < 16 * 3600:
            return jsonify({"status": "failure", "reason": "Normal leaves must be applied at least 16 hours before the college day starts."}), 400
            
    elif leave_type == 'emergency':
        # Check monthly limit
        settings_dict = Setting.get_all()
        emergency_limit = int(settings_dict.get("emergency_leave_limit", 2))
        
        # Count current month approved and pending emergency leaves
        now = datetime.now()
        month_start = now.replace(day=1).date()
        
        used = LeaveRequest.query.filter(
            LeaveRequest.teacher_id == teacher_id,
            LeaveRequest.leave_type == 'emergency',
            LeaveRequest.status.in_(['approved', 'pending']),
            LeaveRequest.start_date >= month_start
        ).count()
        
        if used >= emergency_limit:
            return jsonify({"status": "failure", "reason": f"You have reached your monthly limit of {emergency_limit} emergency leaves."}), 400
            
    else:
        return jsonify({"status": "failure", "reason": "Invalid leave type. Must be 'normal' or 'emergency'."}), 400
        
    new_leave = LeaveRequest(
        teacher_id=teacher_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        is_half_day=is_half_day,
        reason=reason
    )
    from ..extensions import db
    db.session.add(new_leave)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Leave application submitted successfully.",
        "leave": new_leave.to_dict()
    }), 201
'''

content += new_leaves

with open("app/routes/verify.py", "w") as f:
    f.write(content)

print("Done")
