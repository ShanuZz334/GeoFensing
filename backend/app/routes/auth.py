"""
GeoFace Faculty Authentication System - Authentication Routes

POST /login  →  Validates credentials, returns JWT token
GET  /health →  Health check endpoint
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from ..extensions import bcrypt
from ..models import Teacher
from ..utils.validators import validate_login_payload

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


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /login

    Body:
        { "email": "...", "password": "..." }

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

    email = data["email"].strip().lower()
    reg_no = data["reg_no"].strip()
    password = data["password"]

    # Look up teacher
    teacher = Teacher.query.filter_by(email=email, reg_no=reg_no, is_active=True).first()

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
