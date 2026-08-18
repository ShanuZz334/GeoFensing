"""
GeoFace Faculty Authentication System - Verification Route

POST /verify  â  Full AI verification pipeline:
  1. Validate JWT
  2. Replay attack check (timestamp freshness)
  3. GPS geofencing (Haversine)
  4. Face detection (â¥60% frames must have a face)
  5. Face recognition (Euclidean distance â¤ threshold)
  6. Liveness check (EAR blink + head movement)
  7. Write attendance log
"""

from datetime import datetime, timezone, timedelta
import logging

import json
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db, redis_client
from ..models import Teacher, AttendanceLog, Setting, EventAttendance, EventCheckpoint
from ..services.geo_service import is_within_geofence
from ..services.face_service import process_frames, compare_encodings
from ..services.liveness_service import run_liveness_checks
from ..services.jwt_service import verify_timestamp_freshness
from ..utils.validators import validate_verify_payload
from ..utils.geofence_store import get_geofence_config

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
    from ..models import Setting
    settings_dict = Setting.get_all()
    demo_mode = settings_dict.get("demo_mode", False) is True

    if demo_mode:
        logger.info(f"Demo mode active: skipping DB save for {teacher_id}")
        if redis_client and action_type in ['check_in', 'check_out']:
            try:
                if status == "success":
                    redis_client.setex(f"demo_action:{teacher_id}", 43200, action_type)
                    redis_client.delete(f"demo_failures:check_in:{teacher_id}")
                    redis_client.delete(f"demo_failures:check_out:{teacher_id}")
                    logger.info(f"Demo mode Redis: success, set demo_action:{teacher_id} = {action_type}")
                else:
                    failures_key = f"demo_failures:{action_type}:{teacher_id}"
                    redis_client.incr(failures_key)
                    redis_client.expire(failures_key, 43200)
                    logger.info(f"Demo mode Redis: failure for {action_type}, incremented {failures_key}")
            except Exception as e:
                logger.warning("Redis tracking error in _write_log demo mode: %s", e)
        return

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
    from ..models import Setting
    settings_dict = Setting.get_all()
    demo_mode = settings_dict.get("demo_mode", False) is True

    if demo_mode:
        failure_count = 0
        if redis_client:
            try:
                failures_key = f"demo_failures:{action_type}:{teacher_id}"
                failures_val = redis_client.get(failures_key)
                if failures_val:
                    failures_val = failures_val.decode('utf-8') if isinstance(failures_val, bytes) else failures_val
                    failure_count = int(failures_val)
            except Exception as e:
                logger.warning("Redis error in build_failure_response: %s", e)
    else:
        today_start = _get_today_start_utc()
        failure_count = AttendanceLog.query.filter(
            AttendanceLog.teacher_id == teacher_id,
            AttendanceLog.timestamp >= today_start,
            AttendanceLog.status == "failure",
            AttendanceLog.action_type == action_type
        ).count()
    
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


def _get_today_start_utc() -> datetime:
    """Returns the UTC datetime corresponding to midnight of the current local day."""
    return datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).replace(tzinfo=None)

def _get_next_action_info(teacher_id: str):
    """Determine the next attendance action and current attempt count."""
    from ..models import Setting
    settings_dict = Setting.get_all()
    demo_mode = settings_dict.get("demo_mode", False) is True

    if demo_mode:
        action = "check_in"
        failures_count = 0
        limit = 4
        if redis_client:
            try:
                demo_action_val = redis_client.get(f"demo_action:{teacher_id}")
                if demo_action_val:
                    demo_action_val = demo_action_val.decode('utf-8') if isinstance(demo_action_val, bytes) else demo_action_val
                    if demo_action_val == "check_in":
                        action = "check_out"
                        limit = 10
                    else:
                        action = "check_in"
                        limit = 4
                demo_failures_key = f"demo_failures:{action}:{teacher_id}"
                failures_val = redis_client.get(demo_failures_key)
                if failures_val:
                    failures_val = failures_val.decode('utf-8') if isinstance(failures_val, bytes) else failures_val
                    failures_count = int(failures_val)
            except Exception as e:
                logger.warning("Redis error in get_next_action_info demo mode: %s", e)
        return action, failures_count, limit

    today_start = _get_today_start_utc()
    
    today_logs = AttendanceLog.query.filter(
        AttendanceLog.teacher_id == teacher_id,
        AttendanceLog.timestamp >= today_start
    ).order_by(AttendanceLog.timestamp.asc()).all()
    
    # Completed: absent logged or successful checkout recorded
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
    limits = settings_dict.get("verification_limits", {"max_checkin_attempts": 4, "max_checkout_attempts": 10})
    limit = limits.get("max_checkout_attempts", 10) if action == "check_out" else limits.get("max_checkin_attempts", 4)

    # Lock check-in after absent_limit if no successful check-in yet
    # (absent_limit is the LATEST time faculty can still check in)
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
    
    from ..models import LeaveRequest, EventAttendance
    
    # Fetch Leaves
    approved_leaves = LeaveRequest.query.filter(
        LeaveRequest.teacher_id == teacher_id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= now.date(),
        LeaveRequest.end_date >= (now - timedelta(days=14)).date()
    ).all()
    
    approved_leave_dates = {}
    for leave in approved_leaves:
        curr_d = leave.start_date
        while curr_d <= leave.end_date:
            approved_leave_dates[curr_d.strftime("%Y-%m-%d")] = leave
            curr_d += timedelta(days=1)
            
    # Fetch Checkpoints
    checkpoints = EventAttendance.query.filter(
        EventAttendance.teacher_id == teacher_id,
        EventAttendance.timestamp >= now - timedelta(days=14)
    ).all()
    
    checkpoints_by_date = {}
    for cp in checkpoints:
        date_str = cp.timestamp.strftime("%Y-%m-%d")
        if date_str not in checkpoints_by_date:
            checkpoints_by_date[date_str] = []
        checkpoints_by_date[date_str].append(cp)

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
    days_added = 0
    
    for date_str in dates_to_check:
        synthetic_ts = datetime.fromisoformat(date_str).replace(hour=12, tzinfo=timezone.utc)
        is_weekend = synthetic_ts.weekday() in [5, 6]
        
        # Checkpoints for this day
        if date_str in checkpoints_by_date:
            for cp in checkpoints_by_date[date_str]:
                aggregated_logs.append({
                    "id": f"cp_{cp.id}",
                    "teacher_id": teacher_id,
                    "timestamp": cp.timestamp.isoformat() + "Z",
                    "status": "success",
                    "status_display": "CHECKPOINT",
                    "action_type": "event_checkpoint",
                    "attendance_mark": "checkpoint",
                    "reason": cp.checkpoint.name if cp.checkpoint else "Event Checkpoint"
                })

        leave_for_day = approved_leave_dates.get(date_str)
        if leave_for_day:
            if not is_weekend:
                aggregated_logs.append({
                    "id": f"leave_{date_str}",
                    "teacher_id": teacher_id,
                    "timestamp": synthetic_ts.isoformat().replace("+00:00", "Z"),
                    "status": "success",
                    "status_display": "HALF LEAVE" if leave_for_day.is_half_day else "FULL LEAVE",
                    "action_type": "check_in",
                    "attendance_mark": "leave",
                    "reason": f"Approved {leave_for_day.leave_type.capitalize()} Leave"
                })
                days_added += 1
            if days_added >= 4:
                break
            continue
        
        if date_str in grouped:
            day_logs = grouped[date_str]

            # Pick the most informative log: last successful, or last failure
            checkin_log = next((l for l in day_logs if l.status == "success" and l.action_type == "check_in"), None)
            checkout_log = next((l for l in day_logs if l.status == "success" and l.action_type == "check_out"), None)
            last_failure = day_logs[-1] if day_logs else None

            if checkout_log:
                # Day complete — final mark is on the checkout log
                mark = checkout_log.attendance_mark
                if mark == 'present':
                    status_display = "FULL DAY"
                    reason = "Full Day Present"
                elif mark == 'half_day':
                    status_display = "HALF DAY"
                    reason = "Half Day"
                else:
                    status_display = "ABSENT"
                    reason = "Absent"
                log_data = checkout_log.to_dict(include_profile_pic=False)
                log_data["status_display"] = status_display
                log_data["reason"] = reason
                aggregated_logs.append(log_data)
            elif checkin_log:
                # Checked in but not yet checked out
                log_data = checkin_log.to_dict(include_profile_pic=False)
                log_data["status_display"] = "CHECKED IN"
                log_data["reason"] = "Checked in — pending checkout"
                aggregated_logs.append(log_data)
            elif last_failure:
                attempts = len([l for l in day_logs if l.status == "failure"])
                log_data = last_failure.to_dict(include_profile_pic=False)
                log_data["status_display"] = "ABSENT"
                log_data["reason"] = f"All {attempts} verification attempt(s) failed"
                aggregated_logs.append(log_data)
            days_added += 1
        else:
            if is_weekend:
                continue
            # Don't show absent for today until after absent_limit has passed
            if date_str == now.strftime("%Y-%m-%d") and current_time_str <= absent_limit:
                continue
                
            aggregated_logs.append({
                "id": f"syn_{date_str}",
                "teacher_id": teacher_id,
                "timestamp": synthetic_ts.isoformat().replace("+00:00", "Z"),
                "status": "failure",
                "status_display": "ABSENT",
                "action_type": "check_in",
                "attendance_mark": "absent",
                "reason": "No scan record"
            })
            days_added += 1
            
        if days_added >= 4:
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


def calculate_teacher_stats(teacher_id, start_date, end_date=None, is_sem=False):
    from ..models import LeaveRequest, Setting, AttendanceLog
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
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

@verify_bp.route("/attendance/stats", methods=["GET"])
@jwt_required()
def get_attendance_stats():
    """GET /attendance/stats - returns attendance statistics for month and semester."""
    teacher_id = get_jwt_identity()
    now = datetime.now(timezone.utc)

    # Monthly: From start of current month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Semester: From configured start date
    from ..models import Setting
    sem_start_str = Setting.get("semester_start_date")
    try:
        sem_start = datetime.fromisoformat(sem_start_str).replace(tzinfo=timezone.utc)
    except:
        sem_start = now - timedelta(days=180)
    
    res_monthly = calculate_teacher_stats(teacher_id, month_start, is_sem=False)
    res_semester = calculate_teacher_stats(teacher_id, sem_start, is_sem=True)
    
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

    # ————————————————————————————————————————————————————————————————————————————————————
    valid, error = validate_verify_payload(data or {})
    if not valid:
        return jsonify({"status": "failure", "reason": error,
                        "timestamp": datetime.now(timezone.utc).isoformat()}), 400

    from ..models import Setting
    settings_dict = Setting.get_all()
    demo_mode = settings_dict.get("demo_mode", False) is True

    frames: list = data["frames"]
    latitude: float = float(data["latitude"])
    longitude: float = float(data["longitude"])
    timestamp: float = float(data["timestamp"])
    checkpoint_id = data.get("checkpoint_id")
    bypass_limits: bool = data.get("bypass_limits", False) or demo_mode
    # Demo mode is active if bypass_limits is set OR if demo geofence coordinates are provided
    is_demo: bool = bypass_limits or ("demo_lat" in data and "demo_lng" in data)
    server_time = datetime.now(timezone.utc).isoformat()

    # ————————————————————————————————————————————————————————————————————————————————————
    if not verify_timestamp_freshness(timestamp):
        return jsonify({
            "status": "failure",
            "reason": "Request timestamp is stale. Possible replay attack.",
            "timestamp": server_time,
        }), 400

    # ————————————————————————————————————————————————————————————————————————————————————
    cache_key = f"teacher:{teacher_id}"
    teacher = None
    
    if redis_client:
        try:
            val = redis_client.get(cache_key)
            if val:
                from types import SimpleNamespace
                data = json.loads(val)
                teacher = SimpleNamespace(**data)
                logger.debug("Cache HIT for teacher:%s", teacher_id)
        except Exception as e:
            logger.warning("Redis cache error: %s", e)

    if not teacher:
        teacher = Teacher.query.filter_by(teacher_id=teacher_id, is_active=True).first()
        if teacher and redis_client:
            try:
                cache_data = {
                    "teacher_id": str(teacher.teacher_id),
                    "face_encoding": teacher.face_encoding,
                    "college_latitude": teacher.college_latitude,
                    "college_longitude": teacher.college_longitude,
                    "department": teacher.department,
                    "reg_no": teacher.reg_no,
                    "full_name": teacher.full_name,
                }
                redis_client.setex(cache_key, 3600, json.dumps(cache_data))
                logger.debug("Cache MISS for teacher:%s, data cached", teacher_id)
            except Exception as e:
                logger.warning("Redis setex error: %s", e)

    if teacher is None:
        return jsonify({"status": "failure", "reason": "Invalid token",
                        "timestamp": server_time}), 401

    if checkpoint_id:
        action_type = "event_checkpoint"
        failure_count = 0
        checkpoint = EventCheckpoint.query.get(checkpoint_id)
        if not checkpoint or not checkpoint.is_active():
            return jsonify({"status": "failure", "reason": "This event checkpoint has expired or does not exist.", "timestamp": server_time}), 400
        if not checkpoint.faculty_qualifies(teacher):
            return jsonify({"status": "failure", "reason": "You are not authorized for this event checkpoint.", "timestamp": server_time}), 403
        
        # Check if already attended
        existing = EventAttendance.query.filter_by(teacher_id=teacher_id, checkpoint_id=checkpoint_id).first()
        if existing:
            return jsonify({"status": "failure", "reason": "You have already marked attendance for this event.", "timestamp": server_time}), 400
    else:
        action_type, failure_count, _ = _get_next_action_info(teacher_id)



    if teacher.face_encoding is None:
        return jsonify({"status": "failure",
                        "reason": "No face encoding registered for this teacher",
                        "timestamp": server_time}), 422
    
    # Override action type for demo scans so admin logs are clearly labelled
    if is_demo and not demo_mode:
        action_type = 'demo_test'

    # ————————————————————————————————————————————————————————————————————————————————————
    from ..models import Setting
    settings_dict = Setting.get_all()
    
    rules = settings_dict.get("attendance_rules", {})
    class_start = rules.get("class_start", "09:00")
    half_day_limit = rules.get("half_day_limit", "10:30")
    absent_limit = rules.get("absent_limit", "13:00")
    class_end = rules.get("class_end", "17:00")
    
    limits_cfg = settings_dict.get("verification_limits", {})
    max_checkin = limits_cfg.get("max_checkin_attempts", 4)
    max_checkout = limits_cfg.get("max_checkout_attempts", 10)

    # ── Time-Based Rules (New Check-in/Checkout Matrix) ───────────────────────
    # Check-in timing: EARLY = before half_day_limit, LATE = after half_day_limit
    # Checkout timing: ON-TIME = at/after class_end, EARLY = before class_end, VERY EARLY = before absent_limit
    #
    # Matrix:
    #   EARLY check-in  + ON-TIME checkout → present  (full day)
    #   EARLY check-in  + EARLY checkout   → half_day (before class_end)
    #   LATE  check-in  + ON-TIME checkout → half_day
    #   LATE  check-in  + EARLY checkout   → absent
    #   *ANY* check-in  + VERY EARLY out   → absent   (before absent_limit)
    #
    attendance_mark = 'present'
    current_time_str = datetime.now().strftime("%H:%M")
    
    if not demo_mode:
        if action_type == 'check_in':
            # At check-in time we only decide if it is LATE (mark tentatively).
            # The final mark (present / half_day / absent) is decided at checkout.
            if current_time_str > half_day_limit:
                # Late check-in — best possible result is half_day (decided at checkout)
                attendance_mark = 'half_day'
            else:
                # Early check-in — could still earn full day
                attendance_mark = 'present'

        elif action_type == 'check_out':
            # Look up today's check-in record
            today_start = _get_today_start_utc()
            check_in_log = AttendanceLog.query.filter(
                AttendanceLog.teacher_id == teacher_id,
                AttendanceLog.action_type == 'check_in',
                AttendanceLog.status == 'success',
                AttendanceLog.timestamp >= today_start
            ).order_by(AttendanceLog.timestamp.asc()).first()

            # Determine checkout timing
            checkout_on_time = current_time_str >= class_end
            checkout_before_absent_limit = current_time_str < absent_limit

            if check_in_log:
                checkin_was_early = check_in_log.attendance_mark == 'present'
                if checkout_before_absent_limit:
                    attendance_mark = 'absent'     # Very early checkout -> absent
                elif checkin_was_early and checkout_on_time:
                    attendance_mark = 'present'    # Full day
                elif checkin_was_early and not checkout_on_time:
                    attendance_mark = 'half_day'   # Early checkout penalty -> half day
                elif not checkin_was_early and checkout_on_time:
                    attendance_mark = 'half_day'   # Late arrival, stayed till end -> half day
                else:
                    attendance_mark = 'absent'     # Late arrival + Early checkout -> absent
            else:
                # No successful check-in found → treat as absent
                attendance_mark = 'absent'

    limit = max_checkout if action_type == 'check_out' else max_checkin
    
    # ââ Mark Logic ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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

    # ââ Step 1: GPS Geofencing âââââââââââââââââââââââââââââââââââââââââââââââ
    # Support for Demo Mode: override geofence if demo params are provided
    demo_lat = data.get("demo_lat")
    demo_lng = data.get("demo_lng")
    demo_radius = data.get("demo_radius")

    college_lat = teacher.college_latitude or cfg["COLLEGE_LATITUDE"]
    college_lon = teacher.college_longitude or cfg["COLLEGE_LONGITUDE"]
    radius = cfg["GEOFENCE_RADIUS_METERS"]
    geofence_config = get_geofence_config()
    buffer_m = cfg.get("GEOFENCE_BUFFER_METERS", 15)

    if demo_lat is not None and demo_lng is not None:
        logger.info("DEMO MODE: Evaluating spoofed coordinates (%s, %s) against real geofences.", latitude, longitude)

    if action_type == 'event_checkpoint':
        from ..services.geo_service import haversine_distance, GeoPoint
        distance = haversine_distance(GeoPoint(latitude, longitude), GeoPoint(checkpoint.lat, checkpoint.lng))
        if distance <= checkpoint.radius:
            authorized = True
            status_code = "SUCCESS"
        else:
            authorized = False
            status_code = "FAILURE_OUTSIDE_RADIUS"
            
        if demo_lat is not None and demo_lng is not None:
             authorized = True
             distance = 0.0
             status_code = "SUCCESS"
    else:
        authorized, distance, status_code = is_within_geofence(
            latitude, longitude, college_lat, college_lon, radius, 
            geofence_config=geofence_config, buffer_meters=buffer_m, 
            action_type=action_type, teacher_dept=teacher.department,
            teacher_reg_no=teacher.reg_no
        )

    # ââ Buffer Zone Check ââââââââââââââââââââââââââââââââââââââââââââââââââââ
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
        if status_code == "FAILURE_OUTSIDE_DEPT":
            reason = "You are inside the college but outside your assigned department block. Please move inside your department block to check in."
        elif status_code == "FAILURE_OUTSIDE_RADIUS":
            reason = f"You are outside the event location. Move closer to {checkpoint.name} ({distance:.1f}m > {checkpoint.radius}m)."
        if demo_lat is not None:
            reason = f"Demo Mode: Outside range ({distance}m > {radius}m)"
            
        _write_log(teacher_id, latitude, longitude, "failure", reason, len(frames), "geofence", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, reason, distance, 0, len(frames), 1.0, server_time, action_type=action_type)

    success_reason = "Verification successful"

    # ââ Step 2: Frame Processing âââââââââââââââââââââââââââââââââââââââââââââ
    max_frames = cfg.get("MAX_FRAMES", 25)
    images, encodings, landmarks_seq, bboxes_seq, face_frame_count = process_frames(frames, max_frames)
    total_frames = len(images)

    if total_frames == 0:
        reason = "No valid frames received"
        _write_log(teacher_id, latitude, longitude, "failure", reason, 0, "frame_decode", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, reason, distance, 0, 0, 1.0, server_time, action_type=action_type)

    # ââ Step 3: Face Detection Check âââââââââââââââââââââââââââââââââââââââââ
    face_ratio = face_frame_count / total_frames
    min_ratio = cfg.get("MIN_FACE_FRAMES_RATIO", 0.60)

    if face_ratio < min_ratio:
        reason = (
            f"Face not detected in enough frames "
            f"({face_frame_count}/{total_frames}, need {min_ratio*100:.0f}%)"
        )
        _write_log(teacher_id, latitude, longitude, "failure", reason, total_frames, "face_detection", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, reason, distance, face_frame_count, total_frames, 1.0, server_time, action_type=action_type)

    # ââ Step 4: Face Recognition âââââââââââââââââââââââââââââââââââââââââââââ
    # Threshold for Euclidean distance on L2-normalized 512-d InsightFace embeddings.
    # buffalo_l same-person distances are typically 0.2â0.5; different people 0.8â1.4.
    # 0.70 is a balanced operating point â real matches comfortably pass, impostors fail.
    threshold = cfg.get("FACE_RECOGNITION_THRESHOLD", 0.70)
    
    matched, best_distance = compare_encodings(encodings, teacher.face_encoding, threshold)

    if not matched:
        reason = "Face verification failed. The scanned face does not match your registered profile."
        _write_log(teacher_id, latitude, longitude, "failure", reason, total_frames, "face_recognition", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, reason, distance, face_frame_count, total_frames, best_distance, server_time, action_type=action_type)

    # ââ Step 5: Liveness Detection ââââââââââââââââââââââââââââââââââââââââââââ
    liveness_passed, liveness_reason = run_liveness_checks(
        images, bboxes_seq
    )

    if not liveness_passed:
        _write_log(teacher_id, latitude, longitude, "failure", liveness_reason,
                   total_frames, "liveness", action_type=action_type, attendance_mark=mark_on_failure, bypass_limits=bypass_limits)
        return _build_failure_response(teacher_id, liveness_reason, distance, face_frame_count, total_frames, best_distance, server_time, action_type=action_type)

    # ── All checks passed → Mark attendance ──────────────────────────────
    if action_type == 'event_checkpoint':
        attendance = EventAttendance(
            checkpoint_id=checkpoint_id,
            teacher_id=teacher_id,
            status="attended"
        )
        db.session.add(attendance)
        db.session.commit()
    else:
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
    
    # Check max active leaves limit
    active_leaves_count = LeaveRequest.query.filter(
        LeaveRequest.teacher_id == teacher_id,
        LeaveRequest.status.in_(['approved', 'pending']),
        LeaveRequest.end_date >= datetime.utcnow().date()
    ).count()
    
    if active_leaves_count >= 2:
        return jsonify({"status": "failure", "reason": "You can only have a maximum of 2 active (pending or approved) leave applications at a time."}), 400
    
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

@verify_bp.route("/holidays", methods=["GET"])
@jwt_required()
def get_upcoming_holidays():
    """GET /holidays - List upcoming holidays."""
    from ..models import Holiday
    from datetime import date
    today = date.today()
    holidays = Holiday.query.filter(Holiday.date >= today).order_by(Holiday.date.asc()).all()
    return jsonify({"holidays": [h.to_dict() for h in holidays]}), 200

@verify_bp.route("/leaves/<id>", methods=["DELETE"])
@jwt_required()
def delete_leave(id):
    """DELETE /leaves/<id> - Delete a leave request if it hasn't passed."""
    teacher_id = get_jwt_identity()
    from ..models import LeaveRequest
    from datetime import date
    leave = LeaveRequest.query.filter_by(id=id, teacher_id=teacher_id).first()
    if not leave:
        return jsonify({"status": "failure", "reason": "Leave request not found."}), 404
        
    if leave.start_date < date.today():
        return jsonify({"status": "failure", "reason": "Cannot delete leaves that have already started or passed."}), 400
        
    from ..extensions import db
    db.session.delete(leave)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Leave request deleted successfully."}), 200
