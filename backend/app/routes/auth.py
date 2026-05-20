"""
GeoFace Faculty Authentication System - Authentication Routes

POST /login  →  Validates credentials, returns JWT token
GET  /health →  Health check endpoint
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from ..extensions import bcrypt, db
from ..models import Teacher
from ..utils.validators import validate_login_payload, validate_teacher_register_payload
from ..services.face_service import add_face_to_collection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/health", methods=["GET"])
def health_check():
    """Service health probe."""
    return jsonify(
        {
            "status": "healthy",
            "service": "GeoFace Faculty Authentication System",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ), 200

@auth_bp.route("/settings", methods=["GET"])
def get_public_settings():
    """Public endpoint to fetch settings for the mobile app."""
    from ..models import Setting
    return jsonify(Setting.get_all()), 200


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /login

    Body:
    Response 200:
        { "token": "<JWT>", "teacher": { ... }, "expires_in": 86400 }

    Response 401:
        { "error": "Invalid credentials" }
    """
    data = request.get_json(silent=True)

    # Validate input
    valid, error = validate_login_payload(data or {})
    if not valid:
        return jsonify({"error": error}), 400

    reg_no = data["reg_no"].strip()
    password = data["password"]
    device_id = data.get("device_id")

    if not device_id:
        return jsonify({"error": "Device ID is required for login"}), 400

    # Look up teacher
    teacher = Teacher.query.filter_by(reg_no=reg_no, is_active=True).first()

    if teacher is None:
        return jsonify({"error": "Invalid credentials"}), 401

    # Constant-time password check
    if not bcrypt.check_password_hash(teacher.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Block pending teachers
    if teacher.department == "Pending" or teacher.full_name == "Pending Registration":
        return jsonify({"error": "Account registration is pending. Please contact admin to complete registration."}), 403

    # Check Single-Device Lock
    from .. import extensions
    if extensions.redis_client:
        active_device_key = f"active_device:{teacher.teacher_id}"
        active_device = extensions.redis_client.get(active_device_key)
        if active_device and active_device.decode("utf-8") != device_id:
            return jsonify({"error": "You are currently logged in on another device. Please log out there first."}), 403
        
        # Lock device for 5 hours (18000 seconds)
        extensions.redis_client.setex(active_device_key, 18000, device_id)

    # Issue JWT — identity = teacher_id
    access_token = create_access_token(identity=teacher.teacher_id)

    return jsonify(
        {
            "token": access_token,
            "expires_in": 86400,  # 24 hours in seconds
            "teacher": teacher.to_dict(),
        }
    ), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """POST /logout — clears device lock."""
    teacher_id = get_jwt_identity()
    from .. import extensions
    if extensions.redis_client:
        extensions.redis_client.delete(f"active_device:{teacher_id}")
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    POST /reset-password
    Expects: { "reg_no": "...", "totp": "...", "new_password": "..." }
    """
    data = request.get_json(silent=True) or {}
    reg_no = data.get("reg_no", "").strip()
    totp = data.get("totp", "").strip()
    new_password = data.get("new_password", "").strip()

    if not reg_no or not totp or not new_password:
        return jsonify({"error": "Registration Number, TOTP, and New Password are required"}), 400

    from .. import extensions
    import logging
    logger = logging.getLogger('flask.app')
    
    if not extensions.redis_client:
        logger.error("Redis client is None in reset_password")
        return jsonify({"error": "Internal server error: Redis not configured"}), 500

    stored_totp = extensions.redis_client.get("admin_reset_totp")
    logger.info(f"Retrieved stored_totp from Redis: {stored_totp}")
    if not stored_totp:
        return jsonify({"error": "TOTP has expired or was not generated. Please ask admin to generate a new one."}), 400

    if stored_totp.decode("utf-8") != totp:
        return jsonify({"error": "Invalid TOTP"}), 401

    teacher = Teacher.query.filter_by(reg_no=reg_no, is_active=True).first()
    if not teacher:
        return jsonify({"error": "Teacher not found or inactive"}), 404

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    # Invalidate TOTP so it can't be reused
    extensions.redis_client.delete("admin_reset_totp")

    # Update password
    teacher.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    
    # Add to audit log
    from ..models import AdminLog
    log_entry = AdminLog(admin_reg_no="SYSTEM", action="PASSWORD RESET", details=f"Teacher {teacher.reg_no} reset password via TOTP")
    db.session.add(log_entry)
    
    db.session.commit()

    return jsonify({"message": "Password reset successfully. You can now login."}), 200

@auth_bp.route("/complete_setup", methods=["PATCH"])
@jwt_required()
def complete_setup():
    """
    PATCH /complete_setup
    Completes registration for a teacher with temporary access.
    """
    teacher_id = get_jwt_identity()
    teacher = Teacher.query.get(teacher_id)
    
    if not teacher or not teacher.is_active:
        return jsonify({"error": "Teacher not found or inactive"}), 404
        
    if not (teacher.email.endswith('@geoface.local') or teacher.department == 'Pending'):
        return jsonify({"error": "Account is already fully registered"}), 400

    data = request.get_json(silent=True) or {}
    
    # We must construct a valid payload for the existing validator
    payload_to_validate = {
        "full_name": data.get("full_name"),
        "email": data.get("email"),
        "department": data.get("department"),
        "role": data.get("role"),
        "phone_no": data.get("phone_no"),
        "password": data.get("new_password"),
        "reg_no": teacher.reg_no,
        "face_encoding": [0.0]*512 # dummy to pass validation, real one calculated below
    }
    
    valid, error = validate_teacher_register_payload(payload_to_validate)
    if not valid:
        return jsonify({"error": error}), 400
        
    email = data["email"].strip().lower()
    if Teacher.query.filter(Teacher.email == email, Teacher.teacher_id != teacher_id).first():
        return jsonify({"error": "A teacher with this email already exists"}), 409
        
    profile_pic = data.get("profile_pic")
    if not profile_pic:
        return jsonify({"error": "Profile picture is required for face registration"}), 400
        
    encoding = add_face_to_collection(profile_pic)
    if not encoding:
        return jsonify({"error": "Failed to detect face in the provided image. Please take a clearer photo."}), 400
        
    teacher.full_name = data["full_name"].strip()
    teacher.email = email
    teacher.department = data["department"].strip()
    teacher.role = data["role"].strip()
    teacher.phone_no = data["phone_no"].strip()
    teacher.password_hash = bcrypt.generate_password_hash(data["new_password"]).decode("utf-8")
    teacher.profile_pic = profile_pic
    teacher.face_encoding = encoding
    
    db.session.commit()
    
    return jsonify({"message": "Registration completed successfully", "teacher": teacher.to_dict()}), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    """GET /me — returns the current authenticated teacher's latest profile data."""
    teacher_id = get_jwt_identity()
    teacher = Teacher.query.get(teacher_id)
    if not teacher or not teacher.is_active:
        return jsonify({"error": "Teacher not found or inactive"}), 404
    return jsonify({"teacher": teacher.to_dict()}), 200

@auth_bp.route("/profile/update", methods=["PATCH"])
@jwt_required()
def update_profile():
    """
    PATCH /profile/update
    Updates teacher profile details and display picture.
    Does NOT affect face recognition encodings.
    """
    teacher_id = get_jwt_identity()
    teacher = Teacher.query.get(teacher_id)
    
    if not teacher or not teacher.is_active:
        return jsonify({"error": "Teacher not found or inactive"}), 404
        
    data = request.get_json(silent=True) or {}
    
    if "email" in data:
        email = data["email"].strip().lower()
        if Teacher.query.filter(Teacher.email == email, Teacher.teacher_id != teacher_id).first():
            return jsonify({"error": "A teacher with this email already exists"}), 409
        teacher.email = email
        
    if "phone_no" in data:
        teacher.phone_no = data["phone_no"].strip()
        
    if "password" in data and len(data["password"]) >= 8:
        teacher.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        
    if "profile_pic" in data:
        teacher.profile_pic = data["profile_pic"]
        # Note: We purposely DO NOT update face_encoding here, as requested by the user,
        # to ensure the original security registration remains active.
        
    db.session.commit()
    
    return jsonify({"message": "Profile updated successfully", "teacher": teacher.to_dict()}), 200
