"""
GeoFace Faculty Authentication System - Admin Routes

All endpoints require admin JWT. These are called from the admin web panel.

GET    /admin/teachers            List all teachers
POST   /admin/teachers            Register a new teacher
PATCH  /admin/teachers/<id>       Update teacher (name, active status, encoding)
DELETE /admin/teachers/<id>       Deactivate teacher

GET    /admin/attendance          Paginated attendance logs (filterable)
GET    /admin/stats               Dashboard statistics

POST   /admin/encode-face         Extract face encoding from a base64 image
POST   /admin/login               Admin login (separate JWT)
"""

from datetime import datetime, timezone, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from ..extensions import db, bcrypt
from ..models import Teacher, AttendanceLog, Setting, Admin, AdminLog
from ..services.face_service import add_face_to_collection
import json
from ..utils.validators import validate_teacher_register_payload
from ..utils.geofence_store import get_polygon, save_polygon

admin_bp = Blueprint("admin", __name__)

# Simple admin identity prefix to distinguish from teacher tokens
_ADMIN_PREFIX = "admin:"


def _is_admin(identity: str) -> bool:
    return identity.startswith(_ADMIN_PREFIX)

def log_admin_action(identity: str, action: str, details: str = None):
    try:
        admin_reg_no = identity.replace(_ADMIN_PREFIX, "")
        log_entry = AdminLog(admin_reg_no=admin_reg_no, action=action, details=details)
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to log admin action: {e}")


# ── Admin Login ──────────────────────────────────────────────────────────────

@admin_bp.route("/login", methods=["POST"])
def admin_login():
    """POST /admin/login — returns admin JWT."""
    data = request.get_json(silent=True) or {}
    reg_no = data.get("reg_no", "")
    password = data.get("password", "")

    admin = Admin.query.filter_by(reg_no=reg_no).first()
    if not admin or not bcrypt.check_password_hash(admin.password_hash, password):
        return jsonify({"error": "Invalid admin credentials"}), 401
    
    if not admin.is_active:
        return jsonify({"error": "Admin account is deactivated"}), 403

    token = create_access_token(
        identity=f"{_ADMIN_PREFIX}{reg_no}",
        expires_delta=timedelta(hours=8),
    )
    
    # Log successful login
    log_admin_action(f"{_ADMIN_PREFIX}{reg_no}", "LOGIN", "Admin logged in successfully")
    
    return jsonify({
        "token": token, 
        "expires_in": 28800,
        "admin": admin.to_dict()
    }), 200

# ── Global Settings ──────────────────────────────────────────────────────────

@admin_bp.route("/settings", methods=["GET"])
@jwt_required()
def get_settings():
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    current_reg = identity.replace(_ADMIN_PREFIX, "")
    current_admin = Admin.query.filter_by(reg_no=current_reg).first()
    if not current_admin or not current_admin.is_head_admin:
        return jsonify({"error": "Only Head Admins can view settings"}), 403
        
    return jsonify(Setting.get_all()), 200

@admin_bp.route("/settings", methods=["PATCH"])
@jwt_required()
def update_settings():
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    current_reg = identity.replace(_ADMIN_PREFIX, "")
    current_admin = Admin.query.filter_by(reg_no=current_reg).first()
    if not current_admin or not current_admin.is_head_admin:
        return jsonify({"error": "Only Head Admins can modify settings"}), 403
    
    data = request.get_json() or {}
    changes = {}
    for key, value in data.items():
        setting = Setting.query.get(key)
        if setting:
            if setting.value != value:
                changes[key] = f"{setting.value} -> {value}"
            setting.value = value
        else:
            changes[key] = f"None -> {value}"
            setting = Setting(key=key, value=value)
            db.session.add(setting)
    
    db.session.commit()
    if changes:
        log_admin_action(identity, "UPDATE_SETTINGS", json.dumps(changes))
    return jsonify({"message": "Settings updated successfully"}), 200

# ── Teachers CRUD ────────────────────────────────────────────────────────────

@admin_bp.route("/teachers", methods=["GET"])
@jwt_required()
def list_teachers():
    """GET /admin/teachers — return all teachers."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    teachers = Teacher.query.order_by(Teacher.created_at.desc()).all()
    return jsonify({"teachers": [t.to_dict() for t in teachers], "total": len(teachers)}), 200


@admin_bp.route("/teachers", methods=["POST"])
@jwt_required()
def register_teacher():
    """POST /admin/teachers — register a new teacher."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    
    if data.get("is_temporary"):
        reg = data.get("reg_no", "").strip()
        data["full_name"] = "Pending Registration"
        data["email"] = f"temp_{reg}@geoface.local"
        data["department"] = "Pending"

    valid, error = validate_teacher_register_payload(data)
    if not valid:
        return jsonify({"error": error}), 400

    email = data["email"].strip().lower()
    if Teacher.query.filter_by(email=email).first():
        return jsonify({"error": "A teacher with this email already exists"}), 409

    reg_no = data["reg_no"].strip()
    if Teacher.query.filter_by(reg_no=reg_no).first():
        return jsonify({"error": "A teacher with this Registration Number already exists"}), 409

    password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    # Use provided encoding if available, otherwise use dummy
    encoding = data.get("face_encoding", [0.0] * 128)
    profile_pic = data.get("profile_pic")

    teacher = Teacher(
        full_name=data["full_name"].strip(),
        email=email,
        reg_no=data["reg_no"].strip(),
        department=data["department"].strip(),
        password_hash=password_hash,
        face_encoding=encoding,
        profile_pic=profile_pic,
        college_latitude=data.get("college_latitude"),
        college_longitude=data.get("college_longitude"),
    )
    db.session.add(teacher)
    db.session.commit()
    log_admin_action(get_jwt_identity(), "ADD_TEACHER", f"Registered teacher: {teacher.reg_no}")

    return jsonify({"message": "Teacher registered successfully", "teacher": teacher.to_dict()}), 201


# ── Leave Management ─────────────────────────────────────────────────────────

@admin_bp.route("/teachers/search", methods=["GET"])
@jwt_required()
def search_teacher():
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
        
    reg_no = request.args.get("reg_no", "").strip()
    if not reg_no:
        return jsonify({"error": "Registration number required"}), 400
        
    teacher = Teacher.query.filter(Teacher.reg_no.ilike(reg_no)).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
        
    return jsonify(teacher.to_dict()), 200


@admin_bp.route("/teachers/<teacher_id>/leaves", methods=["PATCH"])
@jwt_required()
def update_teacher_leaves(teacher_id):
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
        
    data = request.get_json() or {}
    password = data.get("admin_password", "")
    extra_leaves = data.get("extra_leaves")
    extra_half_leaves = data.get("extra_half_leaves")
    leave_type = data.get("leave_type", "full") # 'full' or 'half'
    quota_type = data.get("quota_type", "semester") # 'semester' or 'monthly'
    
    if extra_leaves is None and extra_half_leaves is None:
        return jsonify({"error": "extra_leaves or extra_half_leaves required"}), 400
        
    # Verify Admin Password
    current_reg = get_jwt_identity().replace(_ADMIN_PREFIX, "")
    current_admin = Admin.query.filter_by(reg_no=current_reg).first()
    
    if not current_admin or not bcrypt.check_password_hash(current_admin.password_hash, password):
        return jsonify({"error": "Invalid admin password"}), 401
        
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
        
    if leave_type == "half" and extra_half_leaves is not None:
        if quota_type == "monthly":
            teacher.extra_half_monthly_leaves = int(extra_half_leaves)
            msg = f"Updated monthly half-day leaves for {teacher.full_name}"
        else:
            teacher.extra_half_leaves = int(extra_half_leaves)
            msg = f"Updated semester half-day leaves for {teacher.full_name}"
    elif extra_leaves is not None:
        if quota_type == "monthly":
            teacher.extra_monthly_leaves = int(extra_leaves)
            msg = f"Updated monthly full-day leaves for {teacher.full_name}"
        else:
            teacher.extra_leaves = int(extra_leaves)
            msg = f"Updated semester full-day leaves for {teacher.full_name}"
        
    db.session.commit()
    log_admin_action(get_jwt_identity(), "UPDATE_LEAVES", msg)
    
    return jsonify({"message": msg, "extra_leaves": teacher.extra_leaves, "extra_half_leaves": teacher.extra_half_leaves, "extra_monthly_leaves": teacher.extra_monthly_leaves, "extra_half_monthly_leaves": teacher.extra_half_monthly_leaves}), 200


# ── Teachers CRUD ────────────────────────────────────────────────────────────


@admin_bp.route("/teachers/<teacher_id>", methods=["PATCH"])
@jwt_required()
def update_teacher(teacher_id: str):
    """PATCH /admin/teachers/<id> — update mutable fields."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    teacher = Teacher.query.get_or_404(teacher_id)
    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        teacher.full_name = data["full_name"].strip()
    if "reg_no" in data:
        teacher.reg_no = data["reg_no"].strip()
    if "department" in data:
        teacher.department = data["department"].strip()
    if "email" in data:
        email = data["email"].strip().lower()
        if email != teacher.email and Teacher.query.filter_by(email=email).first():
            return jsonify({"error": "A teacher with this email already exists"}), 409
        teacher.email = email
    if "password" in data and data["password"].strip():
        password = data["password"].strip()
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
            
        simple_sequences = ["12345678", "abcdefgh", "123456789", "qwertyui", "password"]
        if any(seq in password.lower() for seq in simple_sequences):
            return jsonify({"error": "Password cannot be a simple sequence or common word"}), 400
            
        full_name = data.get("full_name", teacher.full_name)
        name_parts = [p.lower() for p in full_name.split() if len(p) > 2]
        if any(part in password.lower() for part in name_parts):
            return jsonify({"error": "Password cannot contain parts of your name"}), 400
            
        reg_no = data.get("reg_no", teacher.reg_no)
        if reg_no and reg_no.strip().lower() in password.lower():
            return jsonify({"error": "Password cannot contain your Registration Number"}), 400
            
        teacher.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    if "is_active" in data:
        teacher.is_active = bool(data["is_active"])
    if "face_encoding" in data:
        enc = data["face_encoding"]
        if not isinstance(enc, list) or len(enc) != 128:
            return jsonify({"error": "face_encoding must be 128 floats"}), 400
        teacher.face_encoding = enc
    if "college_latitude" in data:
        teacher.college_latitude = float(data["college_latitude"])
    if "college_longitude" in data:
        teacher.college_longitude = float(data["college_longitude"])

    teacher.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    log_admin_action(get_jwt_identity(), "UPDATE_TEACHER", f"Updated teacher: {teacher.reg_no}")
    return jsonify({"message": "Teacher updated", "teacher": teacher.to_dict()}), 200


@admin_bp.route("/teachers/<teacher_id>", methods=["DELETE"])
@jwt_required()
def delete_teacher(teacher_id: str):
    """DELETE /admin/teachers/<id> — permanently delete."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    teacher = Teacher.query.get_or_404(teacher_id)
    db.session.delete(teacher)
    db.session.commit()
    log_admin_action(get_jwt_identity(), "DELETE_TEACHER", f"Deleted teacher: {teacher.reg_no}")
    return jsonify({"message": "Teacher deleted permanently"}), 200


# ── Attendance Logs ──────────────────────────────────────────────────────────

@admin_bp.route("/attendance", methods=["GET"])
@jwt_required()
def get_attendance():
    """GET /admin/attendance — paginated logs with optional filters."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 200)
    status_filter = request.args.get("status")
    teacher_filter = request.args.get("teacher_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    sort_by = request.args.get("sort_by", "timestamp")
    sort_order = request.args.get("sort_order", "desc")
    reg_no_filter = request.args.get("reg_no")
    action_type_filter = request.args.get("action_type")
    attendance_mark_filter = request.args.get("attendance_mark")

    query = AttendanceLog.query

    if status_filter in ("success", "failure"):
        query = query.filter(AttendanceLog.status == status_filter)
    if attendance_mark_filter in ("present", "half_day", "absent", "flagged"):
        query = query.filter(AttendanceLog.attendance_mark == attendance_mark_filter)
    if teacher_filter:
        query = query.filter(AttendanceLog.teacher_id == teacher_filter)
    if date_from:
        query = query.filter(AttendanceLog.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(AttendanceLog.timestamp <= datetime.fromisoformat(date_to))

    if action_type_filter in ("check_in", "check_out"):
        query = query.filter(AttendanceLog.action_type == action_type_filter)
    elif action_type_filter == "who_is_in":
        # Show teachers whose last successful log TODAY is a check_in
        from sqlalchemy import func
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        last_log_sub = db.session.query(
            AttendanceLog.teacher_id,
            func.max(AttendanceLog.timestamp).label("max_ts")
        ).filter(
            AttendanceLog.status == "success",
            AttendanceLog.timestamp >= today_start
        ).group_by(AttendanceLog.teacher_id).subquery()

        query = query.join(
            last_log_sub,
            (AttendanceLog.teacher_id == last_log_sub.c.teacher_id) &
            (AttendanceLog.timestamp == last_log_sub.c.max_ts)
        ).filter(AttendanceLog.action_type == "check_in")

    teacher_joined = False

    if reg_no_filter:
        from ..models import Teacher
        query = query.join(Teacher, AttendanceLog.teacher_id == Teacher.teacher_id)
        teacher_joined = True
        query = query.filter(Teacher.reg_no.ilike(f"%{reg_no_filter}%"))

    if sort_by == "teacher_name":
        if not teacher_joined:
            from ..models import Teacher
            query = query.join(Teacher, AttendanceLog.teacher_id == Teacher.teacher_id)
            teacher_joined = True
        if sort_order == "asc":
            query = query.order_by(Teacher.full_name.asc())
        else:
            query = query.order_by(Teacher.full_name.desc())
    else:
        if sort_order == "asc":
            query = query.order_by(AttendanceLog.timestamp.asc())
        else:
            query = query.order_by(AttendanceLog.timestamp.desc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "logs": [log.to_dict() for log in paginated.items],
        "total": paginated.total,
        "page": page,
        "per_page": per_page,
        "pages": paginated.pages,
    }), 200



@admin_bp.route("/attendance/<log_id>", methods=["PATCH"])
@jwt_required()
def update_attendance_log(log_id: str):
    """PATCH /admin/attendance/<id> — update attendance mark (e.g. resolve flagged)."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    log = AttendanceLog.query.get_or_404(log_id)
    data = request.get_json(silent=True) or {}
    
    if "attendance_mark" in data:
        valid_marks = ["present", "half_day", "absent", "flagged"]
        if data["attendance_mark"] not in valid_marks:
            return jsonify({"error": f"attendance_mark must be one of {valid_marks}"}), 400
        log.attendance_mark = data["attendance_mark"]

    db.session.commit()
    return jsonify({"message": "Attendance log updated", "log": log.to_dict()}), 200

# ── Dashboard Statistics ─────────────────────────────────────────────────────

@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    """GET /admin/stats — summary metrics for dashboard."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_teachers = Teacher.query.filter_by(is_active=True).count()
    total_logs = AttendanceLog.query.count()
    today_success = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= today_start,
        AttendanceLog.status == "success",
    ).count()
    today_failure = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= today_start,
        AttendanceLog.status == "failure",
    ).count()

    # Overall success rate
    total_success = AttendanceLog.query.filter_by(status="success").count()
    success_rate = round(total_success / total_logs * 100, 1) if total_logs > 0 else 0.0

    # Failure breakdown by stage
    from sqlalchemy import func
    stage_breakdown = (
        db.session.query(
            AttendanceLog.failure_stage,
            func.count(AttendanceLog.id).label("count"),
        )
        .filter(AttendanceLog.status == "failure")
        .group_by(AttendanceLog.failure_stage)
        .all()
    )

    return jsonify({
        "total_teachers": total_teachers,
        "total_logs": total_logs,
        "today_success": today_success,
        "today_failure": today_failure,
        "overall_success_rate": success_rate,
        "failure_by_stage": {row.failure_stage or "unknown": row.count for row in stage_breakdown},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }), 200


# ── Geofence Editor ────────────────────────────────────────────────────────────

@admin_bp.route("/geofence", methods=["GET"])
@jwt_required()
def get_geofence():
    """GET /admin/geofence — return the current geofence polygon."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    polygon = get_polygon()
    return jsonify({"polygon": polygon}), 200


@admin_bp.route("/geofence", methods=["PUT"])
@jwt_required()
def update_geofence():
    """PUT /admin/geofence — update the geofence polygon."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    polygon = data.get("polygon")
    if not polygon or not isinstance(polygon, list):
        return jsonify({"error": "Invalid polygon data"}), 400

    if save_polygon(polygon):
        return jsonify({"message": "Geofence updated successfully", "polygon": polygon}), 200
    return jsonify({"error": "Failed to save geofence"}), 500


# ── Face Encoding Helper ──────────────────────────────────────────────────────

@admin_bp.route("/encode-face", methods=["POST"])
@jwt_required()
def encode_face():
    """
    POST /admin/encode-face
    Body: { "image": "<base64-jpeg>" }
    Returns: { "encoding": [128 floats] }

    Used by admin panel webcam capture to generate face encodings
    before registering a new teacher.
    """
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    b64_image = data.get("image")
    if not b64_image:
        return jsonify({"error": "image field is required"}), 400

    encoding = add_face_to_collection(b64_image)
    if not encoding:
        return jsonify({"error": "No face detected in the provided image"}), 422

    return jsonify({
        "encoding": encoding, 
        "message": "Face detected successfully",
        "image": b64_image # Echo back image for registration
    }), 200


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

    # 1. Flagged Logs (Legacy)
    flagged_logs = AttendanceLog.query.filter_by(attendance_mark='flagged', status='success').all()
    for log in flagged_logs:
        alerts.append({
            "id": f"flagged_{log.id}",
            "type": "flagged_log",
            "title": "Flagged Attendance Log",
            "description": f"Teacher {log.teacher.full_name if log.teacher else 'Unknown'} has a flagged log: {log.reason}",
            "teacher_id": log.teacher_id,
            "teacher_name": log.teacher.full_name if log.teacher else 'Unknown',
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
                "description": f"Teacher {ci.teacher.full_name if ci.teacher else 'Unknown'} checked in over 12 hours ago but never checked out.",
                "teacher_id": ci.teacher_id,
                "teacher_name": ci.teacher.full_name if ci.teacher else 'Unknown',
                "timestamp": ci.timestamp.isoformat(),
                "log_id": ci.id
            })

    # 3. Unusual Activity (> 5 failures today)
    failures = db.session.query(
        AttendanceLog.teacher_id,
        func.count(AttendanceLog.id).label('fail_count')
    ).filter(
        AttendanceLog.status == 'failure',
        AttendanceLog.timestamp >= today_start
    ).group_by(AttendanceLog.teacher_id).having(func.count(AttendanceLog.id) > 5).all()

    for f in failures:
        t = Teacher.query.get(f.teacher_id)
        t_name = t.full_name if t else "Unknown"
        alerts.append({
            "id": f"unusual_{f.teacher_id}",
            "type": "unusual_activity",
            "title": "Unusual Activity Detected",
            "description": f"Teacher {t_name} has {f.fail_count} failed verification attempts today.",
            "teacher_id": f.teacher_id,
            "teacher_name": t_name,
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
            
            # Create a synthetic check-out log to resolve the state
            co = AttendanceLog(
                teacher_id=log.teacher_id,
                action_type='check_out',
                status='success',
                reason=f'Admin Resolved: {action}',
                attendance_mark=log.attendance_mark if action != 'force_checkout' else 'present',
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


# ── Admin Management ─────────────────────────────────────────────────────────

@admin_bp.route("/admins", methods=["GET"])
@jwt_required()
def get_admins():
    """GET /admin/admins — return all admins."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    admins = Admin.query.order_by(Admin.created_at.desc()).all()
    return jsonify([a.to_dict() for a in admins]), 200

@admin_bp.route("/admins", methods=["POST"])
@jwt_required()
def create_admin():
    """POST /admin/admins — create new admin (Head Admin only)."""
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    current_reg = identity.replace(_ADMIN_PREFIX, "")
    current_admin = Admin.query.filter_by(reg_no=current_reg).first()
    if not current_admin or not current_admin.is_head_admin:
        return jsonify({"error": "Only a Head Admin can create new administrators"}), 403

    data = request.get_json() or {}
    reg_no = data.get("reg_no", "").strip()
    name = data.get("name", "").strip()
    password = data.get("password", "")
    
    if not reg_no or not name or len(password) < 8:
        return jsonify({"error": "Name, Registration Number, and a strong password (min 8 chars) are required"}), 400
        
    if Admin.query.filter_by(reg_no=reg_no).first():
        return jsonify({"error": "Administrator with this Registration Number already exists"}), 409
        
    is_head_admin = bool(data.get("is_head_admin", False))
    head_admin_password = data.get("head_admin_password", "")

    # Head Admin specific checks
    if is_head_admin:
        head_admin_count = Admin.query.filter_by(is_head_admin=True).count()
        if head_admin_count >= 2:
            return jsonify({"error": "Maximum of 2 Head Admins are allowed. Remove one before promoting another."}), 400
        if not head_admin_password or not bcrypt.check_password_hash(current_admin.password_hash, head_admin_password):
            return jsonify({"error": "Your Head Admin password is required to grant Head Admin privileges"}), 401

    new_admin = Admin(
        name=name,
        reg_no=reg_no,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        is_head_admin=is_head_admin
    )
    db.session.add(new_admin)
    db.session.commit()

    log_admin_action(identity, "CREATE_ADMIN", f"Created {'Head Admin' if is_head_admin else 'Admin'}: {reg_no}")
    return jsonify({"message": "Administrator created successfully", "admin": new_admin.to_dict()}), 201

@admin_bp.route("/admins/<admin_id>", methods=["DELETE"])
@jwt_required()
def delete_admin(admin_id):
    """DELETE /admin/admins/<id> — remove an admin (Head Admin only, requires password)."""
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    current_reg = identity.replace(_ADMIN_PREFIX, "")
    current_admin = Admin.query.filter_by(reg_no=current_reg).first()
    
    if not current_admin or not current_admin.is_head_admin:
        return jsonify({"error": "Only a Head Admin can remove administrators"}), 403
        
    data = request.get_json() or {}
    password = data.get("password", "")
    
    if not bcrypt.check_password_hash(current_admin.password_hash, password):
        return jsonify({"error": "Invalid Head Admin password verification"}), 401
        
    target_admin = Admin.query.get(admin_id)
    if not target_admin:
        return jsonify({"error": "Administrator not found"}), 404
        
    if target_admin.id == current_admin.id:
        return jsonify({"error": "You cannot delete your own Head Admin account"}), 400
        
    target_reg = target_admin.reg_no
    db.session.delete(target_admin)
    db.session.commit()
    
    log_admin_action(identity, "DELETE_ADMIN", f"Deleted admin: {target_reg}")
    return jsonify({"message": "Administrator removed successfully"}), 200

# ── Audit Logs ───────────────────────────────────────────────────────────────

@admin_bp.route("/logs", methods=["GET"])
@jwt_required()
def get_audit_logs():
    """GET /admin/logs — return all audit logs."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(500).all()
    return jsonify([l.to_dict() for l in logs]), 200
