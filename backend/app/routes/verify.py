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

from datetime import datetime, timezone
import logging

import json
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db, redis_client
from ..models import Teacher, AttendanceLog
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
) -> None:
    """Persist an attendance log record."""
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
    
    limit = 10 if action_type == 'check_out' else 4
    attempts_left = max(0, limit - failure_count)
    
    if attempts_left == 0:
        if action_type == 'check_out':
            reason += f". You have exhausted all {limit} check-out attempts. Please contact support."
        else:
            reason += f". You have exhausted all {limit} attempts. Marked as Absent."
    else:
        reason += f". {attempts_left} attempts left."
        
    from flask import jsonify
    return jsonify({
        "status": "failure",
        "reason": reason,
        "attempts_left": attempts_left,
        "timestamp": server_time,
        "contact_support": {
            "phone": "8089602280",
            "email": "shanifshaz546@gmail.com"
        } if attempts_left == 0 else None,
        "details": {
            "gps_distance_m": distance,
            "face_frames": face_frames,
            "total_frames": total_frames,
            "face_distance": face_distance,
        }
    }), 200


def _get_next_action(teacher_id: str) -> str:
    """Determine the next attendance action (check_in or check_out) for today."""
    # Start of current day (UTC)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get last successful log for today
    last_log = AttendanceLog.query.filter(
        AttendanceLog.teacher_id == teacher_id,
        AttendanceLog.status == "success",
        AttendanceLog.timestamp >= today_start
    ).order_by(AttendanceLog.timestamp.desc()).first()
    
    # Simple alternating logic: if none today or last was check_out -> next is check_in
    if not last_log or last_log.action_type == "check_out":
        return "check_in"
    return "check_out"


@verify_bp.route("/attendance", methods=["GET"])
@jwt_required()
def get_teacher_attendance():
    """GET /attendance — returns aggregated attendance logs for the last 4 days."""
    teacher_id = get_jwt_identity()
    
    logs = AttendanceLog.query.filter_by(teacher_id=teacher_id).order_by(AttendanceLog.timestamp.desc()).all()
    
    # Group by date (YYYY-MM-DD)
    from collections import OrderedDict
    grouped = OrderedDict()
    
    for log in logs:
        date_str = log.timestamp.strftime("%Y-%m-%d")
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(log)
        
    aggregated_logs = []
    
    # Take the last 4 distinct days
    for date_str, day_logs in list(grouped.items())[:4]:
        has_success = any(l.status == "success" for l in day_logs)
        status = "success" if has_success else "failure"
        
        if has_success:
            reason = "Present"
        elif len(day_logs) >= 4:
            reason = "Absent"
        else:
            reason = f"Failed ({len(day_logs)}/4 attempts)"
        
        success_logs = [l for l in day_logs if l.status == "success"]
        if success_logs:
            latest_log = success_logs[0]
        else:
            latest_log = day_logs[0]
        
        aggregated_logs.append({
            "id": latest_log.id,
            "teacher_id": latest_log.teacher_id,
            "teacher_name": latest_log.teacher.full_name if latest_log.teacher else None,
            "timestamp": latest_log.timestamp.isoformat(),
            "latitude": latest_log.latitude,
            "longitude": latest_log.longitude,
            "status": status,
            "reason": reason,
            "frames_count": latest_log.frames_count,
            "failure_stage": latest_log.failure_stage,
            "action_type": latest_log.action_type,
        })
        
    return jsonify({
        "logs": aggregated_logs,
        "total": len(aggregated_logs),
        "page": 1,
        "per_page": 20,
        "pages": 1,
        "next_action": _get_next_action(teacher_id),
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

    action_type = _get_next_action(teacher_id)

    # ── Fetch Dynamic Settings ───────────────────────────────────────────────
    from ..models import Setting
    settings_dict = Setting.get_all()
    
    rules = settings_dict.get("attendance_rules", {})
    class_start = rules.get("class_start", "09:00")
    half_day_limit = rules.get("half_day_limit", "10:05")
    absent_limit = rules.get("absent_limit", "11:00")
    half_day_checkout_limit = rules.get("half_day_checkout_limit", "")
    anytime_checkout_full_day = rules.get("anytime_checkout_full_day", False)
    
    limits_cfg = settings_dict.get("verification_limits", {})
    max_checkin = limits_cfg.get("max_checkin_attempts", 4)
    max_checkout = limits_cfg.get("max_checkout_attempts", 10)

    # ── Time-Based Rules Check ───────────────────────────────────────────────
    attendance_mark = 'present'
    current_time_str = datetime.now().strftime("%H:%M")
    
    if action_type == 'check_in':
        if current_time_str > absent_limit:
            attendance_mark = 'half_day'
        elif current_time_str > half_day_limit:
            attendance_mark = 'flagged'
    elif action_type == 'check_out':
        if not anytime_checkout_full_day and half_day_checkout_limit:
            if current_time_str < half_day_checkout_limit:
                attendance_mark = 'half_day'

    # ── Attempt Limit Check ──────────────────────────────────────────────────
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    failure_count = AttendanceLog.query.filter(
        AttendanceLog.teacher_id == teacher_id,
        AttendanceLog.timestamp >= today_start,
        AttendanceLog.status == "failure",
        AttendanceLog.action_type == action_type
    ).count()

    limit = max_checkout if action_type == 'check_out' else max_checkin

    if failure_count >= limit:
        reason = f"You have exhausted all {limit} verification attempts for {action_type.replace('_', ' ')}. Marked as Absent." if action_type == 'check_in' else f"You have exhausted all {limit} check-out attempts. Please contact support."
        
        # If check-in max failed, mark as absent
        if action_type == 'check_in':
            attendance_mark = 'absent'
        
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
            
        _write_log(teacher_id, latitude, longitude, "failure", reason, len(frames), "geofence", action_type=action_type, attendance_mark=attendance_mark)
        return _build_failure_response(teacher_id, reason, distance, 0, len(frames), 1.0, server_time, action_type=action_type)

    success_reason = "Verification successful"

    # ── Step 2: Frame Processing ─────────────────────────────────────────────
    max_frames = cfg.get("MAX_FRAMES", 25)
    images, encodings, landmarks_seq, face_frame_count = process_frames(frames, max_frames)
    total_frames = len(images)

    if total_frames == 0:
        reason = "No valid frames received"
        _write_log(teacher_id, latitude, longitude, "failure", reason, 0, "frame_decode", action_type=action_type, attendance_mark=attendance_mark)
        return _build_failure_response(teacher_id, reason, distance, 0, 0, 1.0, server_time, action_type=action_type)

    # ── Step 3: Face Detection Check ─────────────────────────────────────────
    face_ratio = face_frame_count / total_frames
    min_ratio = cfg.get("MIN_FACE_FRAMES_RATIO", 0.60)

    if face_ratio < min_ratio:
        reason = (
            f"Face not detected in enough frames "
            f"({face_frame_count}/{total_frames}, need {min_ratio*100:.0f}%)"
        )
        _write_log(teacher_id, latitude, longitude, "failure", reason, total_frames, "face_detection", action_type=action_type, attendance_mark=attendance_mark)
        return _build_failure_response(teacher_id, reason, distance, face_frame_count, total_frames, 1.0, server_time, action_type=action_type)

    # ── Step 4: Face Recognition ─────────────────────────────────────────────
    threshold = cfg.get("FACE_RECOGNITION_THRESHOLD", 0.6)
    
    matched, best_distance = compare_encodings(encodings, teacher.face_encoding, threshold)

    if not matched:
        reason = "Face verification failed. The scanned face does not match your registered profile."
        _write_log(teacher_id, latitude, longitude, "failure", reason, total_frames, "face_recognition", action_type=action_type, attendance_mark=attendance_mark)
        return _build_failure_response(teacher_id, reason, distance, face_frame_count, total_frames, best_distance, server_time, action_type=action_type)

    # ── Step 5: Liveness Detection ────────────────────────────────────────────
    ear_threshold = cfg.get("EAR_BLINK_THRESHOLD", 0.25)
    min_blinks = cfg.get("MIN_BLINK_COUNT", 1)
    move_threshold = cfg.get("HEAD_MOVE_THRESHOLD", 5)

    liveness_passed, liveness_reason = run_liveness_checks(
        landmarks_seq, move_threshold
    )

    if not liveness_passed:
        _write_log(teacher_id, latitude, longitude, "failure", liveness_reason,
                   total_frames, "liveness", action_type=action_type, attendance_mark=attendance_mark)
        return _build_failure_response(teacher_id, liveness_reason, distance, face_frame_count, total_frames, best_distance, server_time, action_type=action_type)

    # ── All checks passed → Mark attendance ─────────────────────────────────
    _write_log(teacher_id, latitude, longitude, "success", success_reason, len(frames), action_type=action_type, attendance_mark=attendance_mark)

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
