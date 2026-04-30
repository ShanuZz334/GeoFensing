"""
GeoFace Faculty Authentication System - Test Suite
Tests for core backend services (no external AI dependencies needed).
"""

import math
import pytest

# ── Geo Service Tests ─────────────────────────────────────────────────────────


def test_haversine_zero_distance():
    from app.services.geo_service import haversine_distance, GeoPoint
    point = GeoPoint(latitude=10.8505, longitude=76.2711)
    assert haversine_distance(point, point) == pytest.approx(0.0, abs=1e-3)


def test_haversine_known_distance():
    """Known distance between two points ~100m apart."""
    from app.services.geo_service import haversine_distance, GeoPoint
    # Two points approximately 111m apart (roughly 0.001 degree latitude)
    a = GeoPoint(latitude=10.8505, longitude=76.2711)
    b = GeoPoint(latitude=10.8515, longitude=76.2711)
    dist = haversine_distance(a, b)
    # 0.001° latitude ≈ 111m
    assert 100 < dist < 125


def test_geofence_within_radius():
    from app.services.geo_service import is_within_geofence
    # Point at college center should be inside
    inside, dist, status = is_within_geofence(
        latitude=10.8505,
        longitude=76.2711,
        center_lat=10.8505,
        center_lon=76.2711,
        radius_meters=200,
    )
    assert inside is True
    assert dist == pytest.approx(0.0, abs=1.0)


def test_geofence_just_inside():
    from app.services.geo_service import is_within_geofence
    # ~100m north of college center
    inside, dist, status = is_within_geofence(
        latitude=10.8514,
        longitude=76.2711,
        center_lat=10.8505,
        center_lon=76.2711,
        radius_meters=200,
    )
    assert inside is True
    assert dist < 200


def test_geofence_outside_radius():
    from app.services.geo_service import is_within_geofence
    # ~500m north — outside 200m radius
    inside, dist, status = is_within_geofence(
        latitude=10.8550,
        longitude=76.2711,
        center_lat=10.8505,
        center_lon=76.2711,
        radius_meters=200,
    )
    assert inside is False
    assert dist > 200


def test_geofence_different_city():
    from app.services.geo_service import is_within_geofence
    # Mumbai — far away
    inside, dist, status = is_within_geofence(
        latitude=19.0760,
        longitude=72.8777,
        center_lat=10.8505,
        center_lon=76.2711,
        radius_meters=200,
    )
    assert inside is False
    assert dist > 900_000  # Mumbai is ~984km away


# ── JWT Service Tests ─────────────────────────────────────────────────────────

def test_timestamp_freshness_fresh(app):
    """A current timestamp should be considered fresh."""
    import time
    from app.services.jwt_service import verify_timestamp_freshness

    now = time.time()
    with app.app_context():
        app.config["TIMESTAMP_MAX_AGE_SECONDS"] = 30
        assert verify_timestamp_freshness(now) is True


def test_timestamp_freshness_stale(app):
    """A timestamp 60s old should be rejected."""
    import time
    from app.services.jwt_service import verify_timestamp_freshness

    stale = time.time() - 60
    with app.app_context():
        app.config["TIMESTAMP_MAX_AGE_SECONDS"] = 30
        assert verify_timestamp_freshness(stale) is False


def test_timestamp_freshness_future(app):
    """A timestamp 60s in the future should be rejected."""
    import time
    from app.services.jwt_service import verify_timestamp_freshness

    future = time.time() + 60
    with app.app_context():
        app.config["TIMESTAMP_MAX_AGE_SECONDS"] = 30
        assert verify_timestamp_freshness(future) is False


# ── Liveness Service Tests ────────────────────────────────────────────────────


def _make_left_landmarks(x_nose=100, y_nose=200):
    return {
        'left_eye': [(60, 100)],
        'right_eye': [(80, 100)],
        'nose_bridge': [(65, y_nose)] # Closer to left eye
    }

def _make_middle_landmarks(x_nose=100, y_nose=200):
    return {
        'left_eye': [(60, 100)],
        'right_eye': [(80, 100)],
        'nose_bridge': [(70, y_nose)] # Centered
    }

def _make_right_landmarks(x_nose=100, y_nose=200):
    return {
        'left_eye': [(60, 100)],
        'right_eye': [(80, 100)],
        'nose_bridge': [(75, y_nose)] # Closer to right eye
    }

def test_liveness_passes_with_head_movement():
    from app.services.liveness_service import check_head_movement_sequence
    seq = (
        [_make_left_landmarks()] * 3
        + [_make_middle_landmarks()] * 3
        + [_make_right_landmarks()] * 3
    )
    passed, reason = check_head_movement_sequence(seq)
    assert passed is True

def test_liveness_fails_no_head_movement():
    from app.services.liveness_service import check_head_movement_sequence
    seq = [_make_middle_landmarks() for _ in range(9)]
    passed, reason = check_head_movement_sequence(seq)
    assert passed is False
    assert "LEFT" in reason



# ── Validator Tests ───────────────────────────────────────────────────────────


def test_validate_login_valid():
    from app.utils.validators import validate_login_payload
    ok, err = validate_login_payload({"email": "test@college.edu", "reg_no": "REG123", "password": "pass123"})
    assert ok is True
    assert err is None


def test_validate_login_missing_email():
    from app.utils.validators import validate_login_payload
    ok, err = validate_login_payload({"reg_no": "REG123", "password": "pass123"})
    assert ok is False
    assert "Email" in err


def test_validate_login_bad_email():
    from app.utils.validators import validate_login_payload
    ok, err = validate_login_payload({"email": "not-an-email", "reg_no": "REG123", "password": "pass123"})
    assert ok is False


def test_validate_login_short_password():
    from app.utils.validators import validate_login_payload
    ok, err = validate_login_payload({"email": "t@x.com", "reg_no": "REG123", "password": "ab"})
    assert ok is False
    assert "6" in err


def test_validate_verify_valid():
    import time
    from app.utils.validators import validate_verify_payload
    ok, err = validate_verify_payload({
        "frames": ["img1", "img2"],
        "latitude": 10.8505,
        "longitude": 76.2711,
        "timestamp": time.time(),
    })
    assert ok is True


def test_validate_verify_missing_gps():
    import time
    from app.utils.validators import validate_verify_payload
    ok, err = validate_verify_payload({
        "frames": ["img1"],
        "timestamp": time.time(),
    })
    assert ok is False
    assert "GPS" in err


def test_validate_verify_too_many_frames():
    import time
    from app.utils.validators import validate_verify_payload
    ok, err = validate_verify_payload({
        "frames": ["x"] * 60,
        "latitude": 10.0, "longitude": 76.0,
        "timestamp": time.time(),
    })
    assert ok is False
    assert "Too many" in err


def test_validate_verify_invalid_lat():
    import time
    from app.utils.validators import validate_verify_payload
    ok, err = validate_verify_payload({
        "frames": ["x"],
        "latitude": 200,  # ← out of range
        "longitude": 76.0,
        "timestamp": time.time(),
    })
    assert ok is False
    assert "Latitude" in err


# ── Flask App Integration Tests ────────────────────────────────────────────────

@pytest.fixture
def app():
    """Create a test Flask application."""
    import os
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum!"
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-also-minimum!"
    from app import create_app
    application = create_app("testing")
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_setup(app):
    from app.extensions import db
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"


def test_login_missing_body(client, db_setup):
    res = client.post("/login", json={})
    assert res.status_code == 400


def test_login_invalid_credentials(client, db_setup):
    res = client.post("/login", json={
        "email": "nobody@college.edu",
        "reg_no": "REG123",
        "password": "password123",
    })
    assert res.status_code == 401


def test_verify_without_token(client, db_setup):
    res = client.post("/verify", json={})
    assert res.status_code == 401  # JWT required returns 401


def test_verify_invalid_token(client, db_setup):
    import time
    res = client.post(
        "/verify",
        headers={"Authorization": "Bearer invalid.token.here"},
        json={
            "frames": ["test"],
            "latitude": 10.8505,
            "longitude": 76.2711,
            "timestamp": time.time(),
        },
    )
    assert res.status_code == 422
