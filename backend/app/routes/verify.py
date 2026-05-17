"""
GeoFace Faculty Authentication System - Verification Route

POST /verify  →  Full AI verification pipeline:
  1. Validate JWT
  2. Replay attack check (timestamp freshness)
  3. GPS geofencing (Haversine)
  4. Face detection (≥60% frames must have a face)
  5. Face recognition (Euclidean distance ≤ threshold)
  6. Liveness check (EAR blink + head movement)
  7. Write attendance log
"""

from datetime import datetime, timezone, timedelta
import logging

import json
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db, redis_client
from ..models import Teacher, AttendanceLog, Setting
from ..services.geo_service import is_within_geofence
from ..services.face_service import process_frames, compare_encodings
from ..services.liveness_service import run_liveness_checks
from ..services.jwt_service import verify_timestamp_freshness
from ..utils.validators import validate_verify_payload
from ..utils.geofence_store import get_polygon

logger = logging.getLogger(__name__)
verify_bp = Blueprint("verify", __name__)


def _write_log(
    teacher_id: str,
    latitude: float,
    longitude: float,
    status: str,
    reason: str,
    frames_count: int,
    failure_stage: str = None,
    action_type: str = None,
    attendance_mark: str = 'present',
    bypass_limits: bool = False,
) -> None:
    """Persist an attendance log record."""
    if bypass_limits:
        logger.info(f"Demo mode bypass active: skipping DB save for {teacher_id}")
        return

    log = AttendanceLog(
        teacher_id=teacher_id,
        timestamp=datetime.now(timezone.utc),
        latitude=latitude,
        longitude=longitude,
        status=status,
        reason=reason,
        frames_count=frames_count,
        failure_stage=failure_stage,
        action_type=action_type,
        attendance_mark=attendance_mark,
    )
    db.session.add(log)
    db.session.commit()


def _build_failure_response(teacher_id, reason, distance, face_frames, total_frames, face_distance, server_time, action_type='check_in'):
    """Build a standard failure response with remaining attempts count."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    failure_count = AttendanceLog.query.filter(
        AttendanceLog.teacher_id == teacher_id,
        AttendanceLog.timestamp >= today_start,
        AttendanceLog.status == "failure",
        AttendanceLog.action_type == action_type
    ).count()
    
    from ..models import Setting
    settings_dict = Setting.get_all()
    limits_cfg = settings_dict.get("verification_limits", {})
    max_checkin = limits_cfg.get("max_checkin_attempts", 4)
    max_checkout = limits_cfg.get("max_checkout_attempts", 10)
    
    limit = max_checkout if action_type == 'check_out' else max_checkin
    attempts_left = max(0, limit - failure_count)
    
    if attempts_left == 0:
        if action_type == 'check_out':
            if "exhausted" not in reason:
                reason += f". You have exhausted all {limit} check-out attempts. Please contact support."
        else:
            if "exhausted" not in reason:
                reason += f". You have exhausted all {limit} attempts. Marked as Absent."
    else:
        if "attempts left" not in reason:
            reason += f". {attempts_left} attempts left."
        
    return jsonify({
        "status": "failure",
        "reason": reason,
        "attempts_left": attempts_left,
        "timestamp": server_time,
        "contact_support": {
            "phone": "8089602280",
            "email": "shanifshaz546@gmail.com"
        } if (attempts_left == 0 and action_type == 'check_out') else None,
        "details": {
            "gps_distance_m": distance,
            "face_frames": face_frames,
            "total_frames": total_frames,
            "face_distance": face_distance,
        }
    }), 200


def _get_next_action_info(teacher_id: str):
    """Determine the next attendance action and current attempt count."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_logs = AttendanceLog.query.filter(
        AttendanceLog.teacher_id == teacher_id,
        AttendanceLog.timestamp >= today_start
    ).order_by(AttendanceLog.timestamp.asc()).all()
    
    # Check for completed states
    if any(log.attendance_mark == "absent" for log in today_logs):
        return "completed", 0, 4
        
    if any(log.status == "success" and log.action_type == "check_out" for log in today_logs):
        return "completed", 0, 10
        
    # Determine action
    check_ins = [log for log in today_logs if log.status == "success" and log.action_type == "check_in"]
    action = "check_out" if check_ins else "check_in"
    
    # Count failures for this action
    failures = [log for log in today_logs if log.status == "failure" and log.action_type == action]
    
    # Get limits
    settings_dict = Setting.get_all()
    limits = settings_dict.get("verification_limits", {"max_checkin_attempts": 4, "max_checkout_attempts": 10})
    limit = limits.get("max_checkout_attempts", 10) if action == "check_out" else limits.get("max_checkin_attempts", 4)

    # ── Server-side absent_limit enforcement ─────────────────────────────────
    # If the teacher has no check-in yet and the absent_limit time has passed,
    # return 'completed' so the mobile app's scan button stays locked.
    if action == "check_in":
        try:
            rules = settings_dict.get("attendance_rules", {})
            absent_limit = rules.get("absent_limit", "")
            if absent_limit:
                current_time_str = datetime.now().strftime("%H:%M")
                if current_time_str > absent_limit:
                    return "completed", 0, limit
        except Exception:
            pass
    
    return action, len(failures), limit


def _get_next_action(teacher_id: str) -> str:
    action, _, _ = _get_next_action_info(teacher_id)
    return action


@verify_bp.route("/attendance", methods=["GET"])
@jwt_required()
def get_teacher_attendance():
    """GET /attendance — returns aggregated attendance logs for the last 4 days."""
    teacher_id = get_jwt_identity()
    
    now = datetime.now(timezone.utc)
    dates_to_check = []
    curr = now
    
    # Generate up to 14 days back to find 4 valid working days
    for _ in range(14):
        dates_to_check.append(curr.strftime("%Y-%m-%d"))
        curr -= timedelta(days=1)
        
    logs = AttendanceLog.query.filter(
        AttendanceLog.teacher_id == teacher_id,
        AttendanceLog.timestamp >= now - timedelta(days=14)
    ).order_by(AttendanceLog.timestamp.desc()).all()
    
    from collections import OrderedDict
    grouped = OrderedDict()
    
    for log in logs:
        date_str = log.timestamp.strftime("%Y-%m-%d")
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(log)
        
    settings_dict = Setting.get_all()
    rules = settings_dict.get("attendance_rules", {})
    absent_limit = rules.get("absent_limit", "11:00")
    current_time_str = datetime.now().strftime("%H:%M")
    
    aggregated_logs = []
    
    for date_str in dates_to_check:
        synthetic_ts = datetime.fromisoformat(date_str).replace(hour=12, tzinfo=timezone.utc)
        is_weekend = synthetic_ts.weekday() in [5, 6]
        
        if date_str in grouped:
            day_logs = grouped[date_str]
            has_success = any(l.status == "success" for l in day_logs)
            status = "success" if has_success else "failure"
            
            success_logs = [l for l in day_logs if l.status == "success"]
            if success_logs:
                latest_log = success_logs[0]
            else:
                latest_log = day_logs[0]
                
            if has_success:
                if latest_log.attendance_mark == 'flagged':
                    reason = "Flagged / Processing"
                    status_display = "FLAGGED"
                elif latest_log.attendance_mark == 'half_day':
                    reason = "Half Day"
                    status_display = "HALF DAY"
                elif latest_log.attendance_mark == 'absent':
                    reason = "Absent"
                    status_display = "ABSENT"
                else:
                    reason = "Present"
                    status_display = "SUCCESS"
            elif len(day_logs) >= 4:
                reason = "Absent"
                status_display = "FAILURE"
            else:
                reason = f"Failed ({len(day_logs)}/4 attempts)"
                status_display = "FAILURE"
            
            log_data = latest_log.to_dict()
            log_data["status"] = status
            log_data["reason"] = reason
            log_data["status_display"] = status_display
            aggregated_logs.append(log_data)
        else:
            if is_weekend:
                continue
            if date_str == now.strftime("%Y-%m-%d") and current_time_str <= absent_limit:
                continue
                
            aggregated_logs.append({
                "id": f"syn_{date_str}",
                "teacher_id": teacher_id,
                "timestamp": synthetic_ts.isoformat(),
                "status": "failure",
                "status_display": "ABSENT",
                "action_type": "check_in",
                "attendance_mark": "absent",
                "reason": "No scan record"
            })
            
        if len(aggregated_logs) >= 4:
            break
        
    action, attempts, limit = _get_next_action_info(teacher_id)
    return jsonify({
        "logs": aggregated_logs,
        "total": len(aggregated_logs),
        "page": 1,
        "per_page": 20,
        "pages": 1,
        "next_action": action,
        "current_attempts": attempts,
        "max_attempts": limit
    }), 200


@verify_bp.route("/attendance/stats", methods=["GET"])
@jwt_required()
def get_attendance_stats():
    """GET /attendance/stats — returns attendance statistics for month and semester."""
    teacher_id = get_jwt_identity()
    now = datetime.now(timezone.utc)
    
    def get_stats_for_range(start_date, end_date=None, is_sem=False):
        teacher_id = get_jwt_identity()
        
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
            
        attended = 0
        absent = 0
        taken_full_leaves = 0
        taken_half_leaves = 0
        final_logs = []
        approved_full_leaves = 0
        days_processed = 0
        for date_str in sorted(days_data.keys(), reverse=True):
            days_processed += 1
            day_logs = days_data[date_str]
            
            success_logs = [l for l in day_logs if l.status == "success"]
            success_log = success_logs[-1] if success_logs else None
            
            leave_logs = [l for l in day_logs if l.attendance_mark == "leave"]
            leave_log = leave_logs[-1] if leave_logs else None
            
            absent_logs = [l for l in day_logs if l.attendance_mark == "absent"]
            absent_log = absent_logs[-1] if absent_logs else None
            
            if success_log:
                if success_log.attendance_mark == "half_day":
                    attended += 0.5
                    absent += 0.5
                    taken_half_leaves += 1
                else:
                    attended += 1
                final_logs.append(success_log.to_dict())
            elif leave_log:
                taken_full_leaves += 1
                approved_full_leaves += 1
                log_data = leave_log.to_dict()
                log_data.update({
                    "status": "success",
                    "status_display": "LEAVE",
                    "attendance_mark": "leave",
                    "reason": "Approved Leave"
                })
                final_logs.append(log_data)
            elif absent_log:
                absent += 1
                taken_full_leaves += 1 # Absences count as full leaves taken
                final_logs.append(absent_log.to_dict())
            else:
                # Synthetic Absent (only if date <= today)
                synthetic_ts = datetime.fromisoformat(date_str).replace(hour=12, tzinfo=timezone.utc)
                if synthetic_ts.weekday() in [5, 6]:
                    continue  # Skip Saturday (5) and Sunday (6)

                # DO NOT mark absent for today if we haven't passed the absent_limit yet
                if date_str == now.strftime("%Y-%m-%d"):
                    settings_dict = Setting.get_all()
                    rules = settings_dict.get("attendance_rules", {})
                    absent_limit = rules.get("absent_limit", "11:00")
                    current_time_str = datetime.now().strftime("%H:%M")
                    if current_time_str <= absent_limit:
                        continue # Skip marking absent, they still have time

                absent += 1
                taken_full_leaves += 1 # Absences count as full leaves taken
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
            
        # Get leave settings
        try:
            val = Setting.get("monthly_allotted_leaves", "2")
            allotted_monthly = int(val) if val and str(val).strip() else 2
        except:
            allotted_monthly = 2
            
        try:
            val_half = Setting.get("monthly_allotted_half_leaves", "2")
            allotted_half_monthly = int(val_half) if val_half and str(val_half).strip() else 2
        except:
            allotted_half_monthly = 2
            
        teacher = Teacher.query.get(teacher_id)
        extra_leaves = teacher.extra_leaves if teacher and teacher.extra_leaves else 0
        extra_half_leaves = teacher.extra_half_leaves if teacher and hasattr(teacher, 'extra_half_leaves') and teacher.extra_half_leaves else 0
        extra_monthly_leaves = teacher.extra_monthly_leaves if teacher and hasattr(teacher, 'extra_monthly_leaves') and teacher.extra_monthly_leaves else 0
        extra_half_monthly_leaves = teacher.extra_half_monthly_leaves if teacher and hasattr(teacher, 'extra_half_monthly_leaves') and teacher.extra_half_monthly_leaves else 0
        
        if is_sem:
            # Full semester quota
            allotted = (allotted_monthly * 6) + extra_leaves
            allotted_half = (allotted_half_monthly * 6) + extra_half_leaves
        else:
            # Current month quota
            allotted = allotted_monthly + extra_monthly_leaves
            allotted_half = allotted_half_monthly + extra_half_monthly_leaves
            
        # How many of the absent days are "covered" by the leave quota
        # These should appear as attended in the pie chart centre.
        # Only absences (not actual check-ins) count against leave quota.
        absences_only = taken_full_leaves - approved_full_leaves
        leaves_covered_absent = min(absences_only, max(0, allotted - approved_full_leaves))
        
        # The leave counter should only show consumed quota, capped at the quota
        leaves_quota_used = min(taken_full_leaves, allotted)
        
        return {
            "attended": attended,
            "absent": absent,
            "approved_full_leaves": approved_full_leaves,
            "taken_full_leaves": taken_full_leaves,
            "leaves_quota_used": leaves_quota_used,
            "leaves_covered_absent": leaves_covered_absent,
            "allotted_full_leaves": allotted,
            "taken_half_leaves": taken_half_leaves,
            "allotted_half_leaves": allotted_half,
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
    
    # Prove ranges in logs
    print(f"[STATS] Request for {teacher_id}")
    print(f"[STATS] Monthly range: {month_start.date()} to {now.date()}")
    print(f"[STATS] Semester range: {sem_start.date()} to {now.date()}")
    
    res_monthly = get_stats_for_range(month_start, is_sem=False)
    res_semester = get_stats_for_range(sem_start, is_sem=True)
    
    print(f"[STATS] Monthly results - Total days: {res_monthly['total']}, Attended: {res_monthly['attended']}")
    
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


@verify_bp.route("/verify", methods=["POST"])
@jwt_required()
def verify():
    """
    POST /verify

    Headers:
        Authorization: Bearer <JWT>

    Body:
    {
        "frames":    ["<base64-jpeg>", ...],   // 1-25 frames
        "latitude":  10.8501,
        "longitude": 76.2714,
        "timestamp": 1712994533.123            // UNIX epoch seconds
    }

    Response 200:
    {
        "status":    "success" | "failure",
        "reason":    "...",
        "timestamp": "2026-04-13T05:00:00Z"
    }
    """
    cfg = current_app.config
    teacher_id: str = get_jwt_identity()
    data = request.get_json(silent=True)

    # ── Validate payload ─────────────────────────────────────────────────────
    valid, error = validate_verify_payload(data or {})
    if not valid:
        return jsonify({"status": "failure", "reason": error,
                        "timestamp": datetime.now(timezone.utc).isoformat()}), 400

    frames: list = data["frames"]
    latitude: float = float(data["latitude"])
    longitude: float = float(data["longitude"])
    timestamp: float = float(data["timestamp"])
    bypass_limits: bool = data.get("bypass_limits", False)
    # Demo mode is active if bypass_limits is set OR if demo geofence coordinates are provided
    is_demo: bool = bypass_limits or ("demo_lat" in data and "demo_lng" in data)
    server_time = datetime.now(timezone.utc).isoformat()

    # ── Replay attack guard ──────────────────────────────────────────────────
    if not verify_timestamp_freshness(timestamp):
        return jsonify({
            "status": "failure",
            "reason": "Request timestamp is stale. Possible replay attack.",
            "timestamp": server_time,
        }), 400

    # ── Load teacher (with Redis caching) ────────────────────────────────────
    cache_key = f"teacher:{teacher_id}"
    teacher = None
    
    if redis_client:
        try:
            val = redis_client.get(cache_key)
            if val:
                data = json.loads(val)
                # Create a proxy object to avoid changing attribute access code
                teacher = type('TeacherProxy', (object,), data)
                logger.debug("Cache HIT for teacher:%s", teacher_id)
        except Exception as e:
            logger.warning("Redis cache error: %s", e)

    if not teacher:
        teacher = Teacher.query.filter_by(teacher_id=teacher_id, is_active=True).first()
        if teacher and redis_client:
            try:
                cache_data = {
                    "teacher_id": teacher.teacher_id,
                    "face_encoding": teacher.face_encoding,
                    "college_latitude": teacher.college_latitude,
                    "college_longitude": teacher.college_longitude,
                }
                redis_client.setex(cache_key, 3600, json.dumps(cache_data))
                logger.debug("Cache MISS for teacher:%s, data cached", teacher_id)
            except Exception as e:
                logger.warning("Redis setex error: %s", e)

    if teacher is None:
        return jsonify({"status": "failure", "reason": "Invalid token",
                        "timestamp": server_time}), 401

    if teacher.face_encoding is None:
        return jsonify({"status": "failure",
                        "reason": "No face encoding registered for this teacher",
                        "timestamp": server_time}), 422

    action_type, failure_count, _ = _get_next_action_info(teacher_id)
    
    # Override action type for demo scans so admin logs are clearly labelled
    if is_demo:
        action_type = 'demo_test'

    # ── Fetch Dynamic Settings ───────────────────────────────────────────────
    from ..models import Setting
    settings_dict = Setting.get_all()
    
    rules = settings_dict.get("attendance_rules", {})
    class_start = rules.get("class_start", "09:00")
    half_day_limit = rules.get("half_day_limit", "10:05")
    absent_limit = rules.get("absent_limit", "11:00")
    half_day_checkout_limit = rules.get("half_day_checkout_limit", "")
    anytime_checkout_full_day = rules.get("anytime_checkout_full_day", False)
    min_working_hours = float(rules.get("min_working_hours", 3))
    
    limits_cfg = settings_dict.get("verification_limits", {})
    max_checkin = limits_cfg.get("max_checkin_attempts", 4)
    max_checkout = limits_cfg.get("max_checkout_attempts", 10)

    # ── Time-Based Rules Check ───────────────────────────────────────────────
    attendance_mark = 'present'
    current_time_str = datetime.now().strftime("%H:%M")
    
    if action_type == 'check_in':
        if current_time_str > absent_limit:
            # Arrived after absent_limit — mark absent immediately
            attendance_mark = 'absent'
        elif current_time_str > half_day_limit:
            # Arrived between half_day_limit and absent_limit — half day
            attendance_mark = 'half_day'
        elif current_time_str > class_start:
            # Arrived after class_start but before half_day_limit — flag for admin review
            attendance_mark = 'flagged'
    elif action_type == 'check_out':
        if not anytime_checkout_full_day and half_day_checkout_limit:
            if current_time_str < half_day_checkout_limit:
                attendance_mark = 'half_day'
                
        # Factor in check-in state
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        check_in_log = AttendanceLog.query.filter(
            AttendanceLog.teacher_id == teacher_id,
            AttendanceLog.action_type == 'check_in',
            AttendanceLog.status == 'success',
            AttendanceLog.timestamp >= today_start
        ).order_by(AttendanceLog.timestamp.desc()).first()

        if check_in_log:
            # 1. Configurable Minimum Gap Rule
            # Check if the gap between check-in and check-out is less than min_working_hours
            time_diff = datetime.utcnow() - check_in_log.timestamp
            if time_diff.total_seconds() < (min_working_hours * 3600):
                attendance_mark = 'absent'
            else:
                # 2. Inherit/Combine Check-in State
                ci_mark = check_in_log.attendance_mark
                if ci_mark == 'absent':
                    attendance_mark = 'absent'
                elif ci_mark == 'flagged':
                    attendance_mark = 'flagged'
                elif ci_mark == 'half_day':
                    if attendance_mark == 'half_day':
                        attendance_mark = 'absent'  # Missed both halves
                    else:
                        attendance_mark = 'half_day'

    limit = max_checkout if action_type == 'check_out' else max_checkin
    
    # ── Mark Logic ──────────────────────────────────────────────────────────
    # 'attendance_mark' will now be used as 'mark_on_success'
    # We define a separate 'mark_on_failure' to avoid flagging failed attempts.
    
    mark_on_success = attendance_mark
    mark_on_failure = 'present'
    
    if mark_on_success == 'absent':
        mark_on_failure = 'absent'
    
    if action_type == 'check_in' and failure_count + 1 >= limit:
        mark_on_failure = 'absent'

    if not bypass_limits and failure_count >= limit:
        reason = f"You have exhausted all {limit} verification attempts for {action_type.replace('_', ' ')}. Marked as Absent." if action_type == 'check_in' else f"You have exhausted all {limit} check-out attempts. Please contact support."
        
        # If check-in max failed, mark as absent and persist the record
        if action_type == 'check_in':
            attendance_mark = 'absent'
        
        # Persist the exhausted-attempt event so it shows in admin logs
        _write_log(
            teacher_id, latitude, longitude, "failure", reason,
            len(frames),
            failure_stage="attempt_limit",
            action_type=action_type,
            attendance_mark=mark_on_failure,
            bypass_limits=bypass_limits,
        )
        
        return jsonify({
            "status": "failure",
            "reason": reason,
            "timestamp": server_time,
            "contact_support": {
                "phone": "8089602280",
                "email": "shanifshaz546@gmail.com"
            } if action_type == 'check_out' else None,
        }), 200

    # ── Step 1: GPS Geofencing ───────────────────────────────────────────────
    # Support for Demo Mode: override geofence if demo params are provided
    demo_lat = data.get("demo_lat")
    demo_lng = data.get("demo_lng")
    demo_radius = data.get("demo_radius")

    if demo_lat is not None and demo_lng is not None:
        college_lat = float(demo_lat)
        college_lon = float(demo_lng)
        radius = float(demo_radius or cfg["GEOFENCE_RADIUS_METERS"])
        polygon = None  # Disable polygon in demo mode for simple radius check
        buffer_m = 0
        logger.info("DEMO MODE: Using geofence center (%s, %s) with radius %sm", 
                    college_lat, college_lon, radius)
    else:
        college_lat = teacher.college_latitude or cfg["COLLEGE_LATITUDE"]
        college_lon = teacher.college_longitude or cfg["COLLEGE_LONGITUDE"]
        radius = cfg["GEOFENCE_RADIUS_METERS"]
        polygon = get_polygon()
        buffer_m = cfg.get("GEOFENCE_BUFFER_METERS", 15)

    authorized, distance, status_code = is_within_geofence(
        latitude, longitude, college_lat, college_lon, radius, polygon, buffer_m
    )

    # ── Buffer Zone Check ────────────────────────────────────────────────────
    if status_code == "WARNING_NEAR_BOUNDARY":
        reason = f"You are in the buffer zone ({distance:.1f}m). Please move inside the campus and try again."
        return jsonify({
            "status": "failure",
            "reason": reason,
            "timestamp": server_time,
            "details": {
                "gps_distance_m": distance,
                "face_frames": 0,
                "total_frames": len(frames),
                "face_distance": 1.0,
            }
        }), 200

    if not authorized:
        reason = f"Outside college premises (Geofence: ACCESS DENIED)"
        if demo_lat is not None:
            reason = f"Demo Mode: Outside range ({distance}m > {radius}m)"
            
        _write_log(teacher_id, latitude, longitude, "failure", reason, len(frames), "geofence", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, reason, distance, 0, len(frames), 1.0, server_time, action_type=action_type)

    success_reason = "Verification successful"

    # ── Step 2: Frame Processing ─────────────────────────────────────────────
    max_frames = cfg.get("MAX_FRAMES", 25)
    images, encodings, landmarks_seq, bboxes_seq, face_frame_count = process_frames(frames, max_frames)
    total_frames = len(images)

    if total_frames == 0:
        reason = "No valid frames received"
        _write_log(teacher_id, latitude, longitude, "failure", reason, 0, "frame_decode", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, reason, distance, 0, 0, 1.0, server_time, action_type=action_type)

    # ── Step 3: Face Detection Check ─────────────────────────────────────────
    face_ratio = face_frame_count / total_frames
    min_ratio = cfg.get("MIN_FACE_FRAMES_RATIO", 0.60)

    if face_ratio < min_ratio:
        reason = (
            f"Face not detected in enough frames "
            f"({face_frame_count}/{total_frames}, need {min_ratio*100:.0f}%)"
        )
        _write_log(teacher_id, latitude, longitude, "failure", reason, total_frames, "face_detection", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, reason, distance, face_frame_count, total_frames, 1.0, server_time, action_type=action_type)

    # ── Step 4: Face Recognition ─────────────────────────────────────────────
    # Threshold for Euclidean distance on L2-normalized 512-d InsightFace embeddings.
    # buffalo_l same-person distances are typically 0.2–0.5; different people 0.8–1.4.
    # 0.70 is a balanced operating point — real matches comfortably pass, impostors fail.
    threshold = cfg.get("FACE_RECOGNITION_THRESHOLD", 0.70)
    
    matched, best_distance = compare_encodings(encodings, teacher.face_encoding, threshold)

    if not matched:
        reason = "Face verification failed. The scanned face does not match your registered profile."
        _write_log(teacher_id, latitude, longitude, "failure", reason, total_frames, "face_recognition", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, reason, distance, face_frame_count, total_frames, best_distance, server_time, action_type=action_type)

    # ── Step 5: Liveness Detection ────────────────────────────────────────────
    liveness_passed, liveness_reason = run_liveness_checks(
        images, bboxes_seq
    )

    if not liveness_passed:
        _write_log(teacher_id, latitude, longitude, "failure", liveness_reason,
                   total_frames, "liveness", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, liveness_reason, distance, face_frame_count, total_frames, best_distance, server_time, action_type=action_type)

    # ── All checks passed → Mark attendance ─────────────────────────────────
    _write_log(teacher_id, latitude, longitude, "success", success_reason, len(frames), action_type=action_type, attendance_mark=mark_on_success, bypass_limits=bypass_limits)

    logger.info(
        "Verification SUCCESS: teacher=%s type=%s distance_m=%.2f frames=%d/%d face_dist=%.4f",
        teacher_id, action_type, distance, face_frame_count, total_frames, best_distance
    )

    return jsonify({
        "status": "success",
        "reason": f"Verification successful - {action_type.replace('_', ' ').title()}",
        "action_type": action_type,
        "timestamp": server_time,
        "details": {
            "gps_distance_m": distance,
            "face_frames": face_frame_count,
            "total_frames": total_frames,
            "face_distance": best_distance,
        },
    }), 200
