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
from ..models import Teacher, AttendanceLog
from ..services.face_service import add_face_to_collection
from ..utils.validators import validate_teacher_register_payload

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

    password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    # Use provided encoding if available, otherwise use dummy
    encoding = data.get("face_encoding", [0.0] * 128)
    profile_pic = data.get("profile_pic")

    teacher = Teacher(
        full_name=data["full_name"].strip(),
        email=email,
        reg_no=data["reg_no"].strip(),
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

    query = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc())

    if status_filter in ("success", "failure"):
        query = query.filter_by(status=status_filter)
    if teacher_filter:
        query = query.filter_by(teacher_id=teacher_filter)
    if date_from:
        query = query.filter(AttendanceLog.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(AttendanceLog.timestamp <= datetime.fromisoformat(date_to))

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "logs": [log.to_dict() for log in paginated.items],
        "total": paginated.total,
        "page": page,
        "per_page": per_page,
        "pages": paginated.pages,
    }), 200


# ── Dashboard Statistics ─────────────────────────────────────────────────────

@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    """GET /admin/stats — summary metrics for dashboard."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

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
