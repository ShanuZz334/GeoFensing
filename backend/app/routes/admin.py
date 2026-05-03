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
from ..models import Teacher, AttendanceLog, Setting
from ..services.face_service import add_face_to_collection
from ..utils.validators import validate_teacher_register_payload
from ..utils.geofence_store import get_polygon, save_polygon

admin_bp = Blueprint("admin", __name__)

# Simple admin identity prefix to distinguish from teacher tokens
_ADMIN_PREFIX = "admin:"


def _is_admin(identity: str) -> bool:
    return identity.startswith(_ADMIN_PREFIX)


# ── Admin Login ──────────────────────────────────────────────────────────────

@admin_bp.route("/login", methods=["POST"])
def admin_login():
    """POST /admin/login — returns admin JWT."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    cfg = current_app.config
    if email != cfg.get("ADMIN_EMAIL") or password != cfg.get("ADMIN_PASSWORD"):
        return jsonify({"error": "Invalid admin credentials"}), 401

    token = create_access_token(
        identity=f"{_ADMIN_PREFIX}{email}",
        expires_delta=timedelta(hours=8),
    )
    return jsonify({"token": token, "expires_in": 28800}), 200

# ── Global Settings ──────────────────────────────────────────────────────────

@admin_bp.route("/settings", methods=["GET"])
@jwt_required()
def get_settings():
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    return jsonify(Setting.get_all()), 200

@admin_bp.route("/settings", methods=["PATCH"])
@jwt_required()
def update_settings():
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    data = request.get_json() or {}
    for key, value in data.items():
        setting = Setting.query.get(key)
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.session.add(setting)
    
    db.session.commit()
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

    return jsonify({"message": "Teacher registered successfully", "teacher": teacher.to_dict()}), 201


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
        teacher.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
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

    query = AttendanceLog.query

    if status_filter in ("success", "failure"):
        query = query.filter(AttendanceLog.status == status_filter)
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
