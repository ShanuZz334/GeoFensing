def get_attendance_stats():
    """GET /attendance/stats - returns attendance statistics for month and semester."""
    teacher_id = get_jwt_identity()
    now = datetime.now(timezone.utc)
    
    def get_stats_for_range(start_date, end_date=None, is_sem=False):
        teacher_id = get_jwt_identity()
        from ..models import LeaveRequest, Setting, Teacher, EventCheckpoint, EventAttendance
        
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

            # Get the final day state from checkout (if it exists)
            checkin_log = next((l for l in day_logs if l.status == "success" and l.action_type == "check_in"), None)
            checkout_log = next((l for l in day_logs if l.status == "success" and l.action_type == "check_out"), None)

            if checkout_log:
                # Final mark is on the checkout log
                mark = checkout_log.attendance_mark
                if mark == "present":
                    attended += 1
                elif mark == "half_day":
                    attended += 0.5
                    absent += 0.5
                    unapproved_half_days += 1
                else:
                    absent += 1
                    unapproved_absences += 1
                final_logs.append(checkout_log.to_dict(include_profile_pic=False))
            elif checkin_log:
                # Checked in but never checked out — treat as absent (EOD close)
                absent += 1
                unapproved_absences += 1
                log_data = checkin_log.to_dict(include_profile_pic=False)
                log_data["status_display"] = "ABSENT"
                log_data["reason"] = "No checkout recorded"
                log_data["attendance_mark"] = "absent"
                final_logs.append(log_data)
            else:
                if day_logs:
                    # Only failure logs — count as absent
                    absent += 1
                    unapproved_absences += 1
                    log_data = day_logs[-1].to_dict(include_profile_pic=False)
                    log_data["status_display"] = "ABSENT"
                    log_data["reason"] = "All verification attempts failed"
                    log_data["attendance_mark"] = "absent"
                    final_logs.append(log_data)
                else:
                    # Synthetic Absent (no logs at all for this day)
                    synthetic_ts = datetime.fromisoformat(date_str).replace(hour=12, tzinfo=timezone.utc)
                    if synthetic_ts.weekday() in [5, 6]:
                        continue  # Skip weekend

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

    # Calculate Events
    events_stats = {
        "total_mandatory": 0,
        "attended": 0,
        "missed": 0,
        "deduction_pct": 0.0
    }
    
    from ..models import Teacher, EventCheckpoint, EventAttendance, Setting
    teacher = Teacher.query.filter_by(teacher_id=teacher_id).first()
    if teacher:
        # Get all expired checkpoints created this month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        checkpoints = EventCheckpoint.query.filter(
            EventCheckpoint.expires_at < now,
            EventCheckpoint.created_at >= month_start
        ).all()
        
        settings_dict = Setting.get_all()
        checkpoint_miss_deduction = float(settings_dict.get("checkpoint_miss_deduction_pct", 1.0))
        
        for cp in checkpoints:
            if cp.faculty_qualifies(teacher):
                events_stats["total_mandatory"] += 1
                
                # Check attendance
                attendance = EventAttendance.query.filter_by(
                    checkpoint_id=cp.id,
                    teacher_id=teacher_id
                ).first()
                
                if attendance and attendance.status == "attended":
                    events_stats["attended"] += 1
                else:
                    events_stats["missed"] += 1
                    events_stats["deduction_pct"] += checkpoint_miss_deduction
                    
    # Add event deduction to monthly global deduction
    if events_stats["deduction_pct"] > 0:
        res_monthly["deduction_pct"] = round(res_monthly["deduction_pct"] + events_stats["deduction_pct"], 2)

    res_semester = get_stats_for_range(sem_start, is_sem=True)
    
    return jsonify({
        "monthly": res_monthly,
        "semester": res_semester,
        "events": events_stats,
        "verification_limits": Setting.get_all().get("verification_limits", {
            "max_checkin_attempts": 4,
            "max_checkout_attempts": 10
        }),
        "support_contact": Setting.get("support_contact", {
            "phone": "8089602280",
            "email": "shanifshaz546@gmail.com"
        })
    }), 200

