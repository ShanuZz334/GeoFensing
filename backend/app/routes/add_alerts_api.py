import os

file_path = r'c:\project\ALLBACKUP\GeoFense\backend\app\routes\admin.py'

with open(file_path, 'a', encoding='utf-8') as f:
    f.write('''

# ── Alert Center ─────────────────────────────────────────────────────────────

@admin_bp.route("/alerts", methods=["GET"])
@jwt_required()
def get_alerts():
    """GET /admin/alerts — fetch actionable alerts."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    from sqlalchemy import func
    from datetime import timedelta, timezone
    
    alerts = []
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    twelve_hours_ago = datetime.now(timezone.utc) - timedelta(hours=12)

    # 1. Flagged Logs
    flagged_logs = AttendanceLog.query.filter_by(attendance_mark='flagged').all()
    for log in flagged_logs:
        alerts.append({
            "id": f"flagged_{log.id}",
            "type": "flagged_log",
            "title": "Flagged Attendance Log",
            "description": f"Teacher {log.teacher_name} has a flagged log: {log.reason}",
            "teacher_id": log.teacher_id,
            "teacher_name": log.teacher_name,
            "timestamp": log.timestamp.isoformat(),
            "log_id": log.id
        })

    # 2. Abandoned Check-ins (Checked in > 12h ago, no check out today)
    # We find all check_ins today that are older than 12h.
    # Then we check if there is a check_out for that teacher AFTER the check_in.
    old_checkins = AttendanceLog.query.filter(
        AttendanceLog.action_type == 'check_in',
        AttendanceLog.status == 'success',
        AttendanceLog.timestamp >= today_start,
        AttendanceLog.timestamp < twelve_hours_ago
    ).all()
    
    for ci in old_checkins:
        has_checkout = AttendanceLog.query.filter(
            AttendanceLog.teacher_id == ci.teacher_id,
            AttendanceLog.action_type == 'check_out',
            AttendanceLog.status == 'success',
            AttendanceLog.timestamp > ci.timestamp
        ).first()
        if not has_checkout:
            alerts.append({
                "id": f"abandoned_{ci.id}",
                "type": "abandoned_checkin",
                "title": "Abandoned Check-in",
                "description": f"Teacher {ci.teacher_name} checked in over 12 hours ago but never checked out.",
                "teacher_id": ci.teacher_id,
                "teacher_name": ci.teacher_name,
                "timestamp": ci.timestamp.isoformat(),
                "log_id": ci.id
            })

    # 3. Unusual Activity (> 5 failures today)
    failures = db.session.query(
        AttendanceLog.teacher_id,
        AttendanceLog.teacher_name,
        func.count(AttendanceLog.id).label('fail_count')
    ).filter(
        AttendanceLog.status == 'failure',
        AttendanceLog.timestamp >= today_start
    ).group_by(AttendanceLog.teacher_id, AttendanceLog.teacher_name).having(func.count(AttendanceLog.id) > 5).all()

    for f in failures:
        alerts.append({
            "id": f"unusual_{f.teacher_id}",
            "type": "unusual_activity",
            "title": "Unusual Activity Detected",
            "description": f"Teacher {f.teacher_name} has {f.fail_count} failed verification attempts today.",
            "teacher_id": f.teacher_id,
            "teacher_name": f.teacher_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # Sort alerts by timestamp desc
    alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({"alerts": alerts}), 200

@admin_bp.route("/alerts/resolve", methods=["POST"])
@jwt_required()
def resolve_alert():
    """POST /admin/alerts/resolve — resolve an alert."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    alert_type = data.get("type")
    action = data.get("action")
    log_id = data.get("log_id")
    teacher_id = data.get("teacher_id")

    if alert_type == "flagged_log" and log_id:
        log = AttendanceLog.query.get(log_id)
        if log:
            log.attendance_mark = action # 'present', 'absent', 'half_day'
            db.session.commit()
            return jsonify({"message": f"Log marked as {action}"}), 200
            
    elif alert_type == "abandoned_checkin" and log_id:
        # For abandoned check-in, the admin might want to auto-checkout or mark absent
        log = AttendanceLog.query.get(log_id)
        if log:
            if action == 'mark_absent':
                log.attendance_mark = 'absent'
            elif action == 'mark_half_day':
                log.attendance_mark = 'half_day'
            elif action == 'force_checkout':
                # Create a synthetic check-out log
                co = AttendanceLog(
                    teacher_id=log.teacher_id,
                    teacher_name=log.teacher_name,
                    action_type='check_out',
                    status='success',
                    reason='Admin Force Checkout',
                    attendance_mark='present',
                    latitude=log.latitude,
                    longitude=log.longitude
                )
                db.session.add(co)
            db.session.commit()
            return jsonify({"message": f"Abandoned check-in resolved via {action}"}), 200

    elif alert_type == "unusual_activity" and teacher_id:
        if action == "dismiss":
            # Just dismiss (no DB change needed if we just ignore it, but we could add an 'acknowledged' flag to failures)
            # For now, just delete the failures for today to clear the alert, or better yet, mark them 'flagged'.
            # Actually, easiest is just to delete the spam failures to clean the DB.
            from datetime import timezone, datetime
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            AttendanceLog.query.filter(
                AttendanceLog.teacher_id == teacher_id,
                AttendanceLog.status == 'failure',
                AttendanceLog.timestamp >= today_start
            ).delete()
            db.session.commit()
            return jsonify({"message": "Unusual activity alerts dismissed (spam cleared)."}), 200

    return jsonify({"error": "Invalid resolution payload"}), 400
''')

