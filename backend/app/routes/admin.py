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
from ..utils.geofence_store import get_geofence_config, save_geofence_config

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
    from ..extensions import redis_client
    
    data = request.get_json(silent=True) or {}
    reg_no = data.get("reg_no", "")
    password = data.get("password", "")

    # Brute-force protection: Max 5 attempts per 15 mins per IP
    ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip_addr:
        ip_addr = ip_addr.split(',')[0].strip()
    rate_key = f"rate_limit:admin_login:{ip_addr}"

    if redis_client:
        attempts = redis_client.get(rate_key)
        if attempts and int(attempts) >= 5:
            return jsonify({"error": "Too many failed attempts. Try again in 15 minutes."}), 429

    admin = Admin.query.filter_by(reg_no=reg_no).first()
    if not admin or not bcrypt.check_password_hash(admin.password_hash, password):
        if redis_client:
            redis_client.incr(rate_key)
            redis_client.expire(rate_key, 900)  # 15 mins
        return jsonify({"error": "Invalid admin credentials"}), 401
    
    if not admin.is_active:
        return jsonify({"error": "Admin account is deactivated"}), 403

    if redis_client:
        redis_client.delete(rate_key)

    token = create_access_token(
        identity=f"{_ADMIN_PREFIX}{reg_no}",
        expires_delta=timedelta(hours=5),
    )
    
    # Log successful login
    log_admin_action(f"{_ADMIN_PREFIX}{reg_no}", "LOGIN", "Admin logged in successfully")
    
    return jsonify({
        "token": token, 
        "expires_in": 18000,
        "admin": admin.to_dict()
    }), 200

# ── Get Current Admin ───────────────────────────────────────────────────────

@admin_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_admin():
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
    reg_no = identity.replace(_ADMIN_PREFIX, "")
    admin = Admin.query.filter_by(reg_no=reg_no).first()
    if not admin:
        return jsonify({"error": "Admin not found"}), 404
    return jsonify(admin.to_dict()), 200

# ── TOTP Generation ──────────────────────────────────────────────────────────

@admin_bp.route("/generate-totp", methods=["POST"])
@jwt_required()
def generate_totp():
    """POST /admin/generate-totp — generates a 30s TOTP for teacher password resets."""
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    import secrets
    totp_code = f"{secrets.randbelow(1_000_000):06d}"
    
    from ..models import Setting
    settings_dict = Setting.get_all()
    limits_cfg = settings_dict.get("verification_limits", {})
    totp_duration = int(limits_cfg.get("totp_duration", 300))
    
    from .. import extensions
    if extensions.redis_client:
        extensions.redis_client.setex("admin_reset_totp", totp_duration, totp_code)
        import logging
        logging.getLogger('flask.app').info(f"Generated TOTP {totp_code} in Redis: {extensions.redis_client.get('admin_reset_totp')} at URL {extensions.redis_client.connection_pool.connection_kwargs}")
        return jsonify({"totp": totp_code, "expires_in": totp_duration}), 200
        
    return jsonify({"error": "Redis not available. Cannot generate TOTP."}), 500


@admin_bp.route("/teachers/<teacher_id>/reset-temp-password", methods=["POST"])
@jwt_required()
def reset_temp_password(teacher_id):
    """POST /admin/teachers/<id>/reset-temp-password - generates a new temp password if face is not encoded."""
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    teacher = Teacher.query.filter_by(teacher_id=teacher_id).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
        
    has_face = bool(teacher.face_encoding and any(v != 0 for v in teacher.face_encoding))
    if has_face:
        return jsonify({"error": "Cannot reset password. Teacher has already completed face registration."}), 400
        
    import secrets
    from ..services.email_service import send_credentials_email
    
    raw_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    teacher.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")
    db.session.commit()
    
    log_admin_action(identity, "RESET_TEMP_PASSWORD", f"Reset temporary password for faculty: {teacher.reg_no}")
    
    email_sent = False
    if teacher.email:
        email_sent = send_credentials_email(teacher.email, teacher.full_name, teacher.reg_no, raw_password)
    
    return jsonify({
        "message": "Temporary password reset and emailed successfully." if email_sent else "Password reset successfully, but email not configured or failed.",
        "password": raw_password # Can keep this for debug/logs if needed
    }), 200


@admin_bp.route("/teachers/<teacher_id>/allow-face-reregister", methods=["POST"])
@jwt_required()
def allow_face_reregister(teacher_id):
    """POST /admin/teachers/<id>/allow-face-reregister — Grant teacher a 4hr window to re-scan face."""
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403

    teacher = Teacher.query.filter_by(teacher_id=teacher_id).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    from datetime import timedelta
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Don't re-grant if already active
    if teacher.face_reregister_until and teacher.face_reregister_until > now:
        remaining = int((teacher.face_reregister_until - now).total_seconds())
        return jsonify({
            "message": "Permission already active",
            "remaining_seconds": remaining
        }), 200

    teacher.face_reregister_until = now + timedelta(hours=4)
    db.session.commit()

    log_admin_action(identity, "ALLOW_FACE_REREGISTER", f"Granted face re-registration to {teacher.reg_no} for 4 hours")

    return jsonify({
        "message": f"Face re-registration enabled for {teacher.full_name} for 4 hours.",
        "expires_at": teacher.face_reregister_until.isoformat(),
        "remaining_seconds": 14400
    }), 200

@admin_bp.route("/devices/reset-all", methods=["POST"])
@jwt_required()
def reset_all_device_locks():
    """POST /admin/devices/reset-all — clears all active device session locks (Head Admin only)."""
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403

    current_reg = identity.replace(_ADMIN_PREFIX, "")
    current_admin = Admin.query.filter_by(reg_no=current_reg).first()
    if not current_admin or not current_admin.is_head_admin:
        return jsonify({"error": "Only Head Admins can reset all device locks"}), 403

    teachers = Teacher.query.filter(Teacher.locked_device_id.isnot(None)).all()
    count = len(teachers)
    for teacher in teachers:
        teacher.locked_device_id = None
    
    db.session.commit()

    log_admin_action(identity, "RESET_ALL_DEVICES", f"Cleared {count} permanent device lock(s)")
    return jsonify({"message": f"All device locks cleared. {count} device(s) released."}), 200

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
            # If both existing and new value are dicts, merge them (preserve unset sub-keys)
            if isinstance(setting.value, dict) and isinstance(value, dict):
                merged = {**setting.value, **value}
                if merged != setting.value:
                    diff_old = {}
                    diff_new = {}
                    for k, v in merged.items():
                        if k not in setting.value or setting.value[k] != v:
                            if k in setting.value:
                                diff_old[k] = setting.value[k]
                            diff_new[k] = v
                    changes[key] = f"{diff_old} -> {diff_new}"
                setting.value = merged
            else:
                if setting.value != value:
                    changes[key] = f"{setting.value} -> {value}"
                setting.value = value
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(setting, "value")
        else:
            changes[key] = f"None -> {value}"
            setting = Setting(key=key, value=value)
            db.session.add(setting)
    
    db.session.commit()
    if changes:
        # Check if geofence_config was changed to avoid dumping massive coordinate arrays
        if "geofence_config" in changes:
            changes["geofence_config"] = "Geofence Configuration Updated"
            
        details_str = json.dumps(changes)
            
        log_admin_action(identity, "UPDATE_SETTINGS", details_str)
    return jsonify({"message": "Settings updated successfully"}), 200

# ── Teachers CRUD ────────────────────────────────────────────────────────────

@admin_bp.route("/teachers/<teacher_id>/resend_email", methods=["POST"])
@jwt_required()
def resend_teacher_email(teacher_id):
    """
    POST /admin/teachers/<id>/resend_email
    Resends the welcome email (new password generated) to the teacher.
    """
    verify_admin()
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
        
    if teacher.setup_complete:
        return jsonify({"error": "Teacher has already completed setup"}), 400

    # Auto-generate new 8-character password
    import secrets
    import string
    raw_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    teacher.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")
    
    db.session.commit()

    # Send the email
    from ..services.email_service import send_teacher_registration_email
    send_teacher_registration_email(
        to_email=teacher.email,
        name=teacher.full_name,
        reg_no=teacher.reg_no,
        password=raw_password,
        role=teacher.role,
        department=teacher.department
    )
    
    return jsonify({"message": "Email resent successfully"}), 200

@admin_bp.route("/teachers", methods=["GET"])
@jwt_required()
def list_teachers():
    """GET /admin/teachers — return paginated teachers."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    # Query params
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    status = request.args.get("status", "").strip()
    face = request.args.get("face", "").strip()

    query = Teacher.query

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                Teacher.full_name.ilike(search_filter),
                Teacher.reg_no.ilike(search_filter),
                Teacher.email.ilike(search_filter)
            )
        )
    
    if department:
        query = query.filter(Teacher.department.ilike(f"%{department}%"))

    if status == 'active':
        query = query.filter(Teacher.is_active == True)
    elif status == 'inactive':
        query = query.filter(Teacher.is_active == False)

    if face == 'yes':
        query = query.filter(Teacher.face_encoding != None)
    elif face == 'no':
        query = query.filter(Teacher.face_encoding == None)

    pagination = query.order_by(Teacher.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "teachers": [t.to_dict() for t in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page
    }), 200

# ── Bulk Import Teachers (CSV) ──────────────────────────────────────────────

@admin_bp.route("/teachers/import", methods=["POST"])
@jwt_required()
def import_teachers_csv():
    """POST /admin/teachers/import — bulk register teachers from CSV."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    import csv
    from io import StringIO
    
    stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_reader = csv.DictReader(stream)
    
    # Required columns in CSV: reg_no
    # Optional columns: full_name, email, department, role, phone_no
    success_count = 0
    errors = []
    credentials = []

    from ..services.email_service import send_credentials_email
    
    for row_num, row in enumerate(csv_reader, start=2): # Row 1 is header
        reg_no = row.get("reg_no", "").strip()
        if not reg_no:
            errors.append(f"Row {row_num}: Missing reg_no")
            continue
            
        if Teacher.query.filter_by(reg_no=reg_no).first():
            errors.append(f"Row {row_num}: reg_no {reg_no} already exists")
            continue
            
        email = row.get("email", "").strip().lower()
        if not email:
            errors.append(f"Row {row_num}: Missing email (Required for auto-sending credentials)")
            continue
            
        if Teacher.query.filter_by(email=email).first():
            errors.append(f"Row {row_num}: email {email} already exists")
            continue
            
        # Set defaults
        full_name = row.get("full_name", "").strip() or "Pending Registration"
        department = row.get("department", "").strip() or "Pending"
        role = row.get("role", "").strip() or "Pending"
        phone_no = row.get("phone_no", "").strip() or "Pending"
        
        import secrets
        import string
        
        # Auto-generate temporary password
        raw_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")
        
        teacher = Teacher(
            full_name=full_name,
            email=email,
            reg_no=reg_no,
            department=department,
            role=role,
            phone_no=phone_no,
            password_hash=password_hash,
            face_encoding=[0.0] * 512,
        )
        db.session.add(teacher)
        success_count += 1
        
        # Attempt to send email
        email_sent = send_credentials_email(email, full_name, reg_no, raw_password)
        if not email_sent:
             errors.append(f"Row {row_num}: Teacher created, but failed to send email to {email}")
        
        credentials.append({
            "reg_no": reg_no,
            "full_name": full_name,
            "password": raw_password,
            "email_sent": email_sent
        })
        
    db.session.commit()
    log_admin_action(get_jwt_identity(), "IMPORT_TEACHERS", f"Imported {success_count} faculty members from CSV")
    
    return jsonify({
        "message": f"Successfully imported {success_count} teachers. Credentials have been emailed.",
        "errors": errors,
        "credentials": credentials
    }), 200


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

    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    if Teacher.query.filter_by(email=email).first():
        return jsonify({"error": "A teacher with this email already exists"}), 409

    reg_no = data.get("reg_no", "").strip()
    if not reg_no:
        return jsonify({"error": "Registration Number is required"}), 400

    if Teacher.query.filter_by(reg_no=reg_no).first():
        return jsonify({"error": "A teacher with this Registration Number already exists"}), 409

    import secrets
    import string
    
    # Auto-generate 8-character password
    raw_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    # Use provided encoding if available, otherwise use dummy (InsightFace uses 512 dims)
    encoding = data.get("face_encoding", [0.0] * 512)
    profile_pic = data.get("profile_pic")

    teacher = Teacher(
        full_name=data.get("full_name", "").strip(),
        email=email,
        reg_no=reg_no,
        department=data.get("department", "").strip(),
        role=data.get("role", "").strip(),
        phone_no=data.get("phone_no", "").strip(),
        password_hash=password_hash,
        face_encoding=encoding,
        profile_pic=profile_pic,
        college_latitude=data.get("college_latitude"),
        college_longitude=data.get("college_longitude"),
    )
    db.session.add(teacher)
    db.session.commit()
    log_admin_action(get_jwt_identity(), "ADD_TEACHER", f"Registered faculty: {teacher.reg_no}")

    # Send Credentials Email
    email_sent = False
    if not email.endswith("@geoface.local"):
        from ..services.email_service import send_credentials_email
        email_sent = send_credentials_email(email, teacher.full_name, reg_no, raw_password)

    return jsonify({
        "message": "Teacher registered successfully. Credentials emailed." if email_sent else ("Teacher registered successfully." if email.endswith("@geoface.local") else "Teacher registered successfully. Email not configured or failed."), 
        "teacher": teacher.to_dict()
    }), 201


# ── Autocomplete / Search ────────────────────────────────────────────────────────

@admin_bp.route("/teachers/autocomplete", methods=["GET"])
@jwt_required()
def autocomplete_teachers():
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
        
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([]), 200
        
    try:
        teachers = Teacher.query.filter(Teacher.reg_no.like(f"%{q}%")).limit(10).all()
        results = [{"reg_no": t.reg_no, "full_name": t.full_name} for t in teachers if t.reg_no]
        return jsonify(results), 200
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

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


@admin_bp.route("/teachers/<teacher_id>", methods=["GET"])
@jwt_required()
def get_teacher(teacher_id: str):
    """GET /admin/teachers/<id> — fetch a single teacher's latest data."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    teacher = Teacher.query.get_or_404(teacher_id)
    return jsonify({"teacher": teacher.to_dict()}), 200


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
    if "phone_no" in data:
        teacher.phone_no = data["phone_no"].strip()
    if "role" in data:
        teacher.role = data["role"].strip()

    if "is_active" in data:
        teacher.is_active = bool(data["is_active"])
    if "face_encoding" in data:
        enc = data["face_encoding"]
        if not isinstance(enc, list) or len(enc) != 512:
            return jsonify({"error": "face_encoding must be 512 floats"}), 400
        teacher.face_encoding = enc
    if "college_latitude" in data:
        teacher.college_latitude = float(data["college_latitude"])
    if "college_longitude" in data:
        teacher.college_longitude = float(data["college_longitude"])

    teacher.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    from .. import extensions
    if extensions.redis_client:
        extensions.redis_client.delete(f"teacher:{teacher.teacher_id}")
        
    log_admin_action(get_jwt_identity(), "UPDATE_TEACHER", f"Updated faculty: {teacher.reg_no}")
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
    log_admin_action(get_jwt_identity(), "DELETE_TEACHER", f"Deleted faculty: {teacher.reg_no}")
    return jsonify({"message": "Teacher deleted permanently"}), 200


@admin_bp.route("/teachers/<teacher_id>/release-device", methods=["POST"])
@jwt_required()
def release_device_lock(teacher_id: str):
    """POST /admin/teachers/<id>/release-device — clear the device lock."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.locked_device_id = None
    teacher.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    log_admin_action(get_jwt_identity(), "RELEASE_DEVICE", f"Released device lock for faculty: {teacher.reg_no}")
    return jsonify({"message": "Device lock released successfully"}), 200

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

    # Exclude Demo Mode and Auto-marked absent by default so pagination works correctly
    exclude_system = request.args.get("exclude_system", "true").lower() == "true"
    if exclude_system:
        from sqlalchemy import or_
        query = query.filter(
            or_(AttendanceLog.reason.is_(None), ~AttendanceLog.reason.contains("Demo Mode")),
            or_(AttendanceLog.reason.is_(None), ~AttendanceLog.reason.contains("Auto-marked absent"))
        )

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


# ── Monthly Attendance Report ───────────────────────────────────────────────

@admin_bp.route("/reports/monthly", methods=["GET"])
@jwt_required()
def monthly_report():
    """GET /admin/reports/monthly — aggregated attendance for a given month."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    try:
        year = int(request.args.get("year", datetime.today().year))
        month = int(request.args.get("month", datetime.today().month))
    except ValueError:
        return jsonify({"error": "Invalid year or month"}), 400

    from calendar import monthrange
    num_days = monthrange(year, month)[1]
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    logs = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= start_date,
        AttendanceLog.timestamp < end_date
    ).all()
    
    teachers = Teacher.query.order_by(Teacher.full_name.asc()).all()
    
    report = []
    
    for teacher in teachers:
        # Group logs by day for this teacher
        teacher_logs = [log for log in logs if log.teacher_id == teacher.teacher_id]
        
        present_count = 0
        absent_count = 0
        half_day_count = 0
        
        days_data = {}
        for d in range(1, num_days + 1):
            days_data[str(d)] = "—"
            
        for log in teacher_logs:
            day = str(log.timestamp.day)
            mark = log.attendance_mark
            
            # Use the most successful/highest priority mark for the day
            if mark == "present":
                days_data[day] = "P"
                present_count += 1
            elif mark == "half_day" and days_data[day] != "P":
                days_data[day] = "HD"
                half_day_count += 1
            elif mark == "absent" and days_data[day] not in ("P", "HD"):
                days_data[day] = "A"
                absent_count += 1
                
        report.append({
            "teacher_id": teacher.teacher_id,
            "reg_no": teacher.reg_no or "N/A",
            "full_name": teacher.full_name,
            "department": teacher.department,
            "present": present_count,
            "absent": absent_count,
            "half_day": half_day_count,
            "days": days_data
        })
        
    return jsonify({
        "year": year,
        "month": month,
        "num_days": num_days,
        "report": report
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
    inactive_teachers = Teacher.query.filter_by(is_active=False).count()
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

    from datetime import timedelta
    yesterday_start = today_start - timedelta(days=1)

    yesterday_success = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= yesterday_start,
        AttendanceLog.timestamp < today_start,
        AttendanceLog.status == "success",
    ).count()

    yesterday_failure = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= yesterday_start,
        AttendanceLog.timestamp < today_start,
        AttendanceLog.status == "failure",
    ).count()
    
    yesterday_total = yesterday_success + yesterday_failure
    yesterday_rate = round(yesterday_success / yesterday_total * 100, 1) if yesterday_total > 0 else 0.0
    
    # Current month trend for sparklines and chart
    from sqlalchemy import cast, Date
    import calendar
    
    year, month = today_start.year, today_start.month
    days_in_month = calendar.monthrange(year, month)[1]
    trend_start = today_start.replace(day=1)
    
    trend_data_query = (
        db.session.query(
            cast(AttendanceLog.timestamp, Date).label('date'),
            AttendanceLog.status,
            func.count(AttendanceLog.id).label('count')
        )
        .filter(AttendanceLog.timestamp >= trend_start)
        .filter(db.or_(AttendanceLog.reason == None, ~AttendanceLog.reason.ilike("%Auto-Mark%")))
        .group_by(cast(AttendanceLog.timestamp, Date), AttendanceLog.status)
        .all()
    )
    
    trend = {}
    for i in range(days_in_month):
        d = (trend_start + timedelta(days=i)).date()
        trend[str(d)] = {"success": 0, "failure": 0}
        
    for row in trend_data_query:
        d_str = str(row.date)
        if d_str in trend:
            trend[d_str][row.status] = row.count
            
    success_trend = [trend[k]["success"] for k in sorted(trend.keys())]
    failure_trend = [trend[k]["failure"] for k in sorted(trend.keys())]

    return jsonify({
        "total_teachers": total_teachers,
        "inactive_teachers": inactive_teachers,
        "total_logs": total_logs,
        "today_success": today_success,
        "today_failure": today_failure,
        "overall_success_rate": success_rate,
        "yesterday_success": yesterday_success,
        "yesterday_failure": yesterday_failure,
        "yesterday_rate": yesterday_rate,
        "success_trend": success_trend,
        "failure_trend": failure_trend,
        "trend_month": trend_start.strftime("%B %Y"),
        "trend_days": days_in_month,
        "failure_by_stage": {row.failure_stage or "unknown": row.count for row in stage_breakdown},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }), 200


# ── Geofence Editor ────────────────────────────────────────────────────────────

@admin_bp.route("/geofence", methods=["GET"])
@jwt_required()
def get_geofence():
    """GET /admin/geofence — return the current geofence config."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    config = get_geofence_config()
    return jsonify({"geofence_config": config, "polygon": config.get("main_polygon", [])}), 200


@admin_bp.route("/geofence", methods=["PUT"])
@jwt_required()
def update_geofence():
    """PUT /admin/geofence — update the geofence configuration."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    
    # Check if this is a new config object or old polygon array
    if data and "geofence_config" in data:
        config = data["geofence_config"]
    else:
        # Fallback for old API payload format
        polygon = data.get("polygon") if data else None
        if not polygon or not isinstance(polygon, list):
            raw = request.get_data(as_text=True)
            return jsonify({"error": f"Invalid polygon data. Data keys: {list(data.keys()) if isinstance(data, dict) else type(data)}. Raw len: {len(raw)}"}), 400
        config = get_geofence_config()
        config["main_polygon"] = polygon
        
    if save_geofence_config(config):
        return jsonify({"message": "Geofence updated successfully", "geofence_config": config}), 200
    return jsonify({"error": "Failed to save geofence config"}), 500


# ── Face Encoding Helper ──────────────────────────────────────────────────────

@admin_bp.route("/encode-face", methods=["POST"])
@jwt_required()
def encode_face():
    """
    POST /admin/encode-face
    Body: { "image": "<base64-jpeg>" }
    Returns: { "encoding": [512 floats] }

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
    flagged_logs = AttendanceLog.query.filter_by(attendance_mark='flagged', status='success', is_alert_resolved=False).all()
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
        AttendanceLog.timestamp < twelve_hours_ago,
        AttendanceLog.is_alert_resolved == False
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
        AttendanceLog.timestamp >= today_start,
        AttendanceLog.is_alert_resolved == False
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

    # 4. Spoof Detection (Liveness failures today)
    spoofs = AttendanceLog.query.filter(
        AttendanceLog.status == 'failure',
        AttendanceLog.failure_stage == 'liveness',
        AttendanceLog.timestamp >= today_start,
        AttendanceLog.is_alert_resolved == False
    ).all()

    for s in spoofs:
        alerts.append({
            "id": f"spoof_{s.id}",
            "type": "spoof_detected",
            "title": "Spoofing Attempt Detected",
            "description": f"Teacher {s.teacher.full_name if s.teacher else 'Unknown'} failed liveness check: {s.reason}",
            "teacher_id": s.teacher_id,
            "teacher_name": s.teacher.full_name if s.teacher else 'Unknown',
            "timestamp": s.timestamp.isoformat(),
            "log_id": s.id
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
            log.is_alert_resolved = True
            
            # Find checkout log for the same day and cascade resolution
            from datetime import timezone, datetime
            today_start = log.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start.replace(hour=23, minute=59, second=59)
            
            checkout_log = AttendanceLog.query.filter(
                AttendanceLog.teacher_id == log.teacher_id,
                AttendanceLog.action_type == 'check_out',
                AttendanceLog.status == 'success',
                AttendanceLog.timestamp >= today_start,
                AttendanceLog.timestamp <= today_end
            ).order_by(AttendanceLog.timestamp.desc()).first()
            
            if checkout_log:
                if action == 'absent':
                    checkout_log.attendance_mark = 'absent'
                elif action == 'half_day':
                    checkout_log.attendance_mark = 'half_day'
                elif action == 'present':
                    # Re-evaluate checkout time in case it was flagged
                    from ..models import Setting
                    settings_dict = Setting.get_all()
                    rules = settings_dict.get("attendance_rules", {})
                    half_day_checkout_limit = rules.get("half_day_checkout_limit", "")
                    anytime_checkout_full_day = rules.get("anytime_checkout_full_day", False)
                    
                    co_time_str = checkout_log.timestamp.strftime("%H:%M")
                    
                    if not anytime_checkout_full_day and half_day_checkout_limit and co_time_str < half_day_checkout_limit:
                        checkout_log.attendance_mark = 'half_day'
                    else:
                        checkout_log.attendance_mark = 'present'
                        
            db.session.commit()
            return jsonify({"message": f"Log marked as {action}"}), 200
            
    elif alert_type == "abandoned_checkin" and log_id:
        # For abandoned check-in, the admin might want to auto-checkout or mark absent
        log = AttendanceLog.query.get(log_id)
        if log:
            log.is_alert_resolved = True
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
            from datetime import timezone, datetime
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            logs = AttendanceLog.query.filter(
                AttendanceLog.teacher_id == teacher_id,
                AttendanceLog.status == 'failure',
                AttendanceLog.timestamp >= today_start,
                AttendanceLog.is_alert_resolved == False
            ).all()
            for fl in logs:
                fl.is_alert_resolved = True
            db.session.commit()
            return jsonify({"message": "Unusual activity alerts dismissed (spam cleared)."}), 200

    elif alert_type == "spoof_detected" and log_id:
        if action == "dismiss":
            log = AttendanceLog.query.get(log_id)
            if log:
                log.is_alert_resolved = True
                db.session.commit()
                return jsonify({"message": "Spoof alert dismissed"}), 200

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

    profile_pic = data.get("profile_pic", None)

    new_admin = Admin(
        name=name,
        reg_no=reg_no,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        profile_pic=profile_pic,
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

@admin_bp.route("/admins/<admin_id>", methods=["PATCH"])
@jwt_required()
def update_admin(admin_id):
    """PATCH /admin/admins/<id> — update an admin."""
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    current_reg = identity.replace(_ADMIN_PREFIX, "")
    current_admin = Admin.query.filter_by(reg_no=current_reg).first()
    
    target_admin = Admin.query.get(admin_id)
    if not target_admin:
        return jsonify({"error": "Administrator not found"}), 404
        
    # Only head admin or the admin themselves can edit their profile
    if not current_admin.is_head_admin and target_admin.id != current_admin.id:
        return jsonify({"error": "Unauthorized to edit this administrator"}), 403

    data = request.get_json() or {}
    
    if "name" in data:
        target_admin.name = data["name"].strip()
    if "profile_pic" in data:
        target_admin.profile_pic = data["profile_pic"]
    if "password" in data and data["password"]:
        if len(data["password"]) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        target_admin.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        
    db.session.commit()
    log_admin_action(identity, "UPDATE_ADMIN", f"Updated admin: {target_admin.reg_no}")
    return jsonify({"message": "Administrator updated successfully", "admin": target_admin.to_dict()}), 200

# ── Audit Logs ───────────────────────────────────────────────────────────────

@admin_bp.route("/logs", methods=["GET"])
@jwt_required()
def get_audit_logs():
    """GET /admin/logs — return all audit logs."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(500).all()
    return jsonify([l.to_dict() for l in logs]), 200


# ── Auto-Absent Job ──────────────────────────────────────────────────────────

def run_auto_absent_job(app=None):
    """
    Mark all active teachers who have not checked in today as absent,
    but only if the absent_limit time has already passed.

    This function is safe to call multiple times (idempotent):
    teachers who already have an absent or success record today are skipped.
    Weekends (Saturday=5, Sunday=6) are also skipped.

    Can be called from the APScheduler background job or the admin endpoint.
    Returns a dict with 'marked' count and 'skipped' count.
    """
    from ..extensions import db
    from ..models import Teacher, AttendanceLog, Setting

    use_ctx = app is not None
    ctx = app.app_context() if use_ctx else None
    if ctx:
        ctx.push()

    try:
        now = datetime.now(timezone.utc)

        # Skip weekends
        if now.weekday() in (5, 6):
            return {"marked": 0, "skipped": 0, "reason": "Weekend — skipped"}

        # Check absent_limit setting
        settings_dict = Setting.get_all()
        rules = settings_dict.get("attendance_rules", {})
        absent_limit = rules.get("absent_limit", "")
        if not absent_limit:
            return {"marked": 0, "skipped": 0, "reason": "absent_limit not configured"}

        current_time_str = datetime.now().strftime("%H:%M")
        if current_time_str <= absent_limit:
            return {
                "marked": 0,
                "skipped": 0,
                "reason": f"Absent limit ({absent_limit}) has not passed yet (now {current_time_str})"
            }

        # Range: start of today (UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Find all active teachers
        active_teachers = Teacher.query.filter_by(is_active=True).all()

        marked = 0
        skipped = 0

        for teacher in active_teachers:
            # Check if any attendance record exists today for this teacher
            existing = AttendanceLog.query.filter(
                AttendanceLog.teacher_id == teacher.teacher_id,
                AttendanceLog.timestamp >= today_start,
            ).first()

            if existing:
                skipped += 1
                continue

            # No record — insert synthetic absent
            absent_log = AttendanceLog(
                teacher_id=teacher.teacher_id,
                timestamp=datetime.now(timezone.utc),
                latitude=None,
                longitude=None,
                status="failure",
                reason=f"Auto-marked absent: did not check in before absent limit ({absent_limit})",
                frames_count=0,
                failure_stage="auto_absent",
                action_type="check_in",
                attendance_mark="absent",
            )
            db.session.add(absent_log)
            marked += 1

        db.session.commit()
        return {"marked": marked, "skipped": skipped}

    except Exception as e:
        db.session.rollback()
        raise e
    finally:
        if ctx:
            ctx.pop()


@admin_bp.route("/trigger-auto-absent", methods=["POST"])
@jwt_required()
def trigger_auto_absent():
    """
    POST /admin/trigger-auto-absent

    Manually trigger the auto-absent job.
    Marks all active teachers with no attendance record today as absent,
    only if the absent_limit time has already passed.
    Head Admin only.
    """
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403

    current_reg = identity.replace(_ADMIN_PREFIX, "")
    current_admin = Admin.query.filter_by(reg_no=current_reg).first()
    if not current_admin or not current_admin.is_head_admin:
        return jsonify({"error": "Only Head Admins can trigger the auto-absent job"}), 403

    try:
        result = run_auto_absent_job()
        log_admin_action(
            identity,
            "TRIGGER_AUTO_ABSENT",
            f"Marked {result.get('marked', 0)} teachers absent, skipped {result.get('skipped', 0)}"
        )
        return jsonify({
            "message": "Auto-absent job completed",
            **result
        }), 200
    except Exception as e:
        return jsonify({"error": f"Auto-absent job failed: {str(e)}"}), 500


# ── Holidays ─────────────────────────────────────────────────────────────────

@admin_bp.route("/holidays", methods=["GET"])
@jwt_required()
def get_holidays():
    """GET /admin/holidays — list all holidays."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    from ..models.holiday import Holiday
    holidays = Holiday.query.order_by(Holiday.date.asc()).all()
    return jsonify({"holidays": [h.to_dict() for h in holidays]}), 200

@admin_bp.route("/holidays", methods=["POST"])
@jwt_required()
def create_holiday():
    """POST /admin/holidays — create a holiday."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    data = request.get_json(silent=True) or {}
    date_str = data.get("date")
    name = data.get("name")
    is_full_day = data.get("is_full_day", True)

    if not date_str or not name:
        return jsonify({"error": "date and name are required"}), 400

    from ..models.holiday import Holiday
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if Holiday.query.filter_by(date=dt).first():
        return jsonify({"error": "A holiday on this date already exists"}), 409

    holiday = Holiday(date=dt, name=name.strip(), is_full_day=bool(is_full_day))
    db.session.add(holiday)
    db.session.commit()
    
    log_admin_action(get_jwt_identity(), "CREATE_HOLIDAY", f"Added holiday: {name} on {date_str}")
    return jsonify({"message": "Holiday created", "holiday": holiday.to_dict()}), 201

@admin_bp.route("/holidays/<int:holiday_id>", methods=["DELETE"])
@jwt_required()
def delete_holiday(holiday_id: int):
    """DELETE /admin/holidays/<id> — remove a holiday."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    from ..models.holiday import Holiday
    holiday = Holiday.query.get_or_404(holiday_id)
    db.session.delete(holiday)
    db.session.commit()

    log_admin_action(get_jwt_identity(), "DELETE_HOLIDAY", f"Removed holiday: {holiday.name}")
    return jsonify({"message": "Holiday removed"}), 200


@admin_bp.route("/leaves", methods=["GET"])
@jwt_required()
def get_admin_leaves():
    """GET /admin/leaves - list leave requests."""
    if not _is_admin(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
        
    from ..models import LeaveRequest, Teacher
    
    status_filter = request.args.get("status")
    type_filter = request.args.get("type")
    reg_no_filter = request.args.get("reg_no")
    
    query = LeaveRequest.query
    
    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)
        
    if type_filter and type_filter != 'all':
        query = query.filter_by(leave_type=type_filter)
        
    if reg_no_filter:
        query = query.join(Teacher).filter(Teacher.reg_no.like(f"%{reg_no_filter}%"))
        
    leaves = query.order_by(LeaveRequest.applied_at.desc()).all()
        
    from .verify import calculate_teacher_stats
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
    result = []
    for l in leaves:
        d = l.to_dict()
        teacher = Teacher.query.get(l.teacher_id)
        d['teacher_name'] = teacher.full_name if teacher else "Unknown"
        d['teacher_reg_no'] = teacher.reg_no if teacher else "N/A"
        d['teacher_profile_pic'] = teacher.profile_pic if teacher else None
        
        if teacher:
            stats = calculate_teacher_stats(teacher.teacher_id, month_start, is_sem=False)
            d['leaves_this_month'] = stats.get('approved_full_leaves', 0) + stats.get('approved_half_leaves', 0)
            d['current_cut_percent'] = stats.get('deduction_pct', 0.0)
        else:
            d['leaves_this_month'] = 0
            d['current_cut_percent'] = 0.0
            
        result.append(d)
        
    return jsonify({"leaves": result}), 200

@admin_bp.route("/leaves/<id>", methods=["PATCH"])
@jwt_required()
def update_leave_status(id: str):
    """PATCH /admin/leaves/<id> - approve or reject a leave request."""
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    reg_no = identity.replace(_ADMIN_PREFIX, "")
    from ..models import Admin, LeaveRequest
    admin = Admin.query.filter_by(reg_no=reg_no).first()
    if not admin:
        return jsonify({"error": "Admin not found"}), 404
        
    leave = LeaveRequest.query.get_or_404(id)
    
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    
    if new_status not in ["approved", "rejected"]:
        return jsonify({"error": "Invalid status. Must be 'approved' or 'rejected'"}), 400
        
    leave.status = new_status
    leave.reviewed_at = datetime.utcnow()
    leave.reviewed_by = admin.id
    
    db.session.commit()
    
    # Log the action
    from ..models import AdminLog, Teacher
    teacher = Teacher.query.get(leave.teacher_id)
    reg_no_display = teacher.reg_no if teacher else leave.teacher_id
    log = AdminLog(
        admin_reg_no=admin.reg_no, 
        action=f"leave_{new_status}", 
        details=f"{new_status.capitalize()} leave request for faculty {reg_no_display}"
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({"message": f"Leave {new_status} successfully", "leave": leave.to_dict()}), 200


@admin_bp.route("/teachers/<teacher_id>/stats", methods=["GET"])
@jwt_required()
def get_faculty_stats(teacher_id: str):
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403
        
    from ..models import Teacher
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({"error": "Faculty not found"}), 404
        
    from .verify import calculate_teacher_stats
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    stats = calculate_teacher_stats(teacher_id, month_start, is_sem=False)
    leaves_this_month = stats.get('approved_full_leaves', 0) + stats.get('approved_half_leaves', 0)
    current_cut_percent = stats.get('deduction_pct', 0.0)
    
    # Calculate today's status
    from ..models import AttendanceLog, LeaveRequest
    from datetime import timedelta
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    today_status = "Not Checked In"
    
    # Check for leave today
    leave_today = LeaveRequest.query.filter(
        LeaveRequest.teacher_id == teacher_id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= today_start.date(),
        LeaveRequest.end_date >= today_start.date()
    ).first()
    
    if leave_today:
        today_status = "Half Day Leave" if leave_today.is_half_day else "On Leave"
    else:
        # Check logs
        latest_log = AttendanceLog.query.filter(
            AttendanceLog.teacher_id == teacher_id,
            AttendanceLog.timestamp >= today_start,
            AttendanceLog.timestamp < today_end
        ).order_by(AttendanceLog.timestamp.desc()).first()
        
        if latest_log:
            if latest_log.attendance_mark == "absent":
                today_status = "Absent"
            elif latest_log.action_type == "check_in":
                today_status = "In Campus"
            elif latest_log.action_type == "check_out" or latest_log.action_type == "completed":
                today_status = "Checked Out"
                
    return jsonify({
        "teacher": teacher.to_dict(),
        "today_status": today_status,
        "leaves_taken": leaves_this_month,
        "cut_pct": current_cut_percent
    }), 200

