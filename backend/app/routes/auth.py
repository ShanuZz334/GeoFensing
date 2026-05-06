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

    # Look up teacher
    teacher = Teacher.query.filter_by(reg_no=reg_no, is_active=True).first()

    if teacher is None:
        return jsonify({"error": "Invalid credentials"}), 401

    # Constant-time password check
    if not bcrypt.check_password_hash(teacher.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Issue JWT — identity = teacher_id
    access_token = create_access_token(identity=teacher.teacher_id)

    return jsonify(
        {
            "token": access_token,
            "expires_in": 86400,  # 24 hours in seconds
            "teacher": teacher.to_dict(),
        }
    ), 200

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
    teacher.password_hash = bcrypt.generate_password_hash(data["new_password"]).decode("utf-8")
    teacher.profile_pic = profile_pic
    teacher.face_encoding = encoding
    
    db.session.commit()
    
    return jsonify({"message": "Registration completed successfully", "teacher": teacher.to_dict()}), 200
