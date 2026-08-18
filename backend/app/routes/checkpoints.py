"""
GeoFace Faculty Authentication System - Event Checkpoint Routes
Handles CRUD for event/seminar checkpoints and faculty attendance at them.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from math import radians, sin, cos, sqrt, atan2

from ..models import EventCheckpoint, Teacher
from ..extensions import db

checkpoints_bp = Blueprint("checkpoints", __name__)


def _is_admin(identity: str) -> bool:
    return isinstance(identity, str) and identity.startswith("admin:")


def _haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Return distance in meters between two GPS coords."""
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ── Admin: Create Checkpoint ─────────────────────────────────────────────────
@checkpoints_bp.route("/admin/checkpoints", methods=["POST"])
@jwt_required()
def create_checkpoint():
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"status": "failure", "reason": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    lat = data.get("lat")
    lng = data.get("lng")
    radius = float(data.get("radius", 50))
    restriction_type = data.get("restriction_type", "all")
    departments = data.get("departments", [])
    faculty_reg_nos = data.get("faculty_reg_nos", [])
    starts_at_str = data.get("starts_at")
    expires_at_str = data.get("expires_at")

    if not name or lat is None or lng is None:
        return jsonify({"status": "failure", "reason": "name, lat, lng are required"}), 400
    if not expires_at_str:
        return jsonify({"status": "failure", "reason": "expires_at is required"}), 400

    try:
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
        starts_at = datetime.fromisoformat(starts_at_str.replace("Z", "+00:00")).replace(tzinfo=None) if starts_at_str else datetime.utcnow()
    except (ValueError, AttributeError):
        return jsonify({"status": "failure", "reason": "Invalid datetime format. Use ISO 8601."}), 400

    is_compulsory = data.get("is_compulsory", False)

    if expires_at <= datetime.utcnow():
        return jsonify({"status": "failure", "reason": "expires_at must be in the future"}), 400

    admin_id = identity.replace("admin:", "")

    cp = EventCheckpoint(
        name=name,
        lat=float(lat),
        lng=float(lng),
        radius=radius,
        restriction_type=restriction_type,
        departments=departments if restriction_type == "department" else [],
        faculty_reg_nos=faculty_reg_nos if restriction_type == "faculty" else [],
        is_compulsory=bool(is_compulsory),
        starts_at=starts_at,
        expires_at=expires_at,
        created_by=admin_id,
    )
    db.session.add(cp)
    db.session.commit()

    return jsonify({"status": "success", "checkpoint": cp.to_dict()}), 201


# ── Admin: List All Checkpoints ──────────────────────────────────────────────
@checkpoints_bp.route("/admin/checkpoints", methods=["GET"])
@jwt_required()
def list_checkpoints():
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"status": "failure", "reason": "Admin access required"}), 403

    # Return all non-expired checkpoints
    now = datetime.utcnow()
    checkpoints = EventCheckpoint.query.filter(
        EventCheckpoint.expires_at > now
    ).order_by(EventCheckpoint.created_at.desc()).all()

    return jsonify({"checkpoints": [cp.to_dict() for cp in checkpoints]}), 200


# ── Admin: Delete Checkpoint ─────────────────────────────────────────────────
@checkpoints_bp.route("/admin/checkpoints/<cp_id>", methods=["DELETE"])
@jwt_required()
def delete_checkpoint(cp_id):
    identity = get_jwt_identity()
    if not _is_admin(identity):
        return jsonify({"status": "failure", "reason": "Admin access required"}), 403

    cp = EventCheckpoint.query.get(cp_id)
    if not cp:
        return jsonify({"status": "failure", "reason": "Checkpoint not found"}), 404

    db.session.delete(cp)
    db.session.commit()
    return jsonify({"status": "success", "message": "Checkpoint deleted"}), 200


# ── Faculty: Get My Active Checkpoints ───────────────────────────────────────
@checkpoints_bp.route("/checkpoints/mine", methods=["GET"])
@jwt_required()
def get_my_checkpoints():
    teacher_id = get_jwt_identity()
    if _is_admin(teacher_id):
        return jsonify({"status": "failure", "reason": "Faculty access required"}), 403

    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({"status": "failure", "reason": "Faculty not found"}), 404

    now = datetime.utcnow()
    active_cps = EventCheckpoint.query.filter(
        EventCheckpoint.starts_at <= now,
        EventCheckpoint.expires_at > now,
    ).all()

    # Filter by qualification
    qualified = [cp.to_dict() for cp in active_cps if cp.faculty_qualifies(teacher)]

    return jsonify({"checkpoints": qualified}), 200


# ── Faculty: Mark Attendance at Checkpoint ────────────────────────────────────
@checkpoints_bp.route("/checkpoints/<cp_id>/attend", methods=["POST"])
@jwt_required()
def attend_checkpoint(cp_id):
    teacher_id = get_jwt_identity()
    if _is_admin(teacher_id):
        return jsonify({"status": "failure", "reason": "Faculty access required"}), 403

    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({"status": "failure", "reason": "Faculty not found"}), 404

    cp = EventCheckpoint.query.get(cp_id)
    if not cp:
        return jsonify({"status": "failure", "reason": "Checkpoint not found"}), 404

    if not cp.is_active():
        return jsonify({"status": "failure", "reason": "This checkpoint has expired or not yet started"}), 400

    if not cp.faculty_qualifies(teacher):
        return jsonify({"status": "failure", "reason": "You are not assigned to this checkpoint"}), 403

    data = request.get_json(silent=True) or {}
    lat = data.get("lat")
    lng = data.get("lng")

    if lat is None or lng is None:
        return jsonify({"status": "failure", "reason": "lat and lng are required"}), 400

    distance = _haversine_distance(float(lat), float(lng), cp.lat, cp.lng)
    buffer = 20  # 20m GPS buffer
    if distance > cp.radius + buffer:
        return jsonify({
            "status": "failure",
            "reason": f"You are {round(distance)}m away from the checkpoint. You need to be within {round(cp.radius)}m.",
            "distance_m": round(distance),
        }), 400

    return jsonify({
        "status": "success",
        "message": "Attendance marked successfully!",
        "checkpoint_name": cp.name,
        "distance_m": round(distance),
    }), 200
