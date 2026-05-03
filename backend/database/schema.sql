-- ==============================================================================
-- GeoFace Faculty Authentication System - PostgreSQL Schema
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- TEACHERS
-- ==============================================================================

CREATE TABLE IF NOT EXISTS teachers (
    teacher_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name        VARCHAR(200)  NOT NULL,
    email            VARCHAR(255)  NOT NULL UNIQUE,
    reg_no           VARCHAR(100)  UNIQUE,
    department       VARCHAR(100),
    profile_pic      TEXT,
    password_hash    VARCHAR(255)  NOT NULL,
    -- 128-element float array stored as JSONB for efficient indexing
    face_encoding    JSONB,
    -- Optional per-teacher geofence (overrides global config when set)
    college_latitude  DOUBLE PRECISION,
    college_longitude DOUBLE PRECISION,
    is_active        BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teachers_email     ON teachers(email);
CREATE INDEX IF NOT EXISTS idx_teachers_is_active ON teachers(is_active);

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_timestamp_teachers ON teachers;
CREATE TRIGGER set_timestamp_teachers
    BEFORE UPDATE ON teachers
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();


-- ==============================================================================
-- ATTENDANCE LOGS
-- ==============================================================================

CREATE TABLE IF NOT EXISTS attendance_logs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id       UUID          NOT NULL REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    timestamp        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    latitude         DOUBLE PRECISION,
    longitude        DOUBLE PRECISION,
    status           VARCHAR(20)   NOT NULL DEFAULT 'failure'
                         CHECK (status IN ('success', 'failure')),
    reason           VARCHAR(500)  NOT NULL DEFAULT '',
    frames_count     INTEGER,
    -- Which pipeline stage caused failure (NULL on success)
    failure_stage    VARCHAR(100),
    -- "check_in" or "check_out"
    action_type      VARCHAR(20),
    -- "present", "half_day", or "absent"
    attendance_mark  VARCHAR(20)   NOT NULL DEFAULT 'present',
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attendance_teacher   ON attendance_logs(teacher_id);
CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_attendance_status    ON attendance_logs(status);
CREATE INDEX IF NOT EXISTS idx_attendance_date      ON attendance_logs(DATE(timestamp));

-- ==============================================================================
-- SETTINGS
-- ==============================================================================

CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB NOT NULL
);

INSERT INTO settings (key, value) VALUES 
('attendance_rules', '{"class_start": "09:00", "half_day_limit": "10:05", "absent_limit": "11:00"}'),
('verification_limits', '{"max_checkin_attempts": 4, "max_checkout_attempts": 10}')
ON CONFLICT (key) DO NOTHING;



-- ==============================================================================
-- SEED DATA — Default admin teacher for testing
-- Password: Admin@1234  (bcrypt hash below)
-- ==============================================================================

INSERT INTO teachers (teacher_id, full_name, email, password_hash, is_active)
VALUES (
    uuid_generate_v4(),
    'Admin Teacher',
    'admin@college.edu',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8H.sHZ4tYlT5yFqMb7e',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- ==============================================================================
-- HELPFUL VIEWS
-- ==============================================================================

CREATE OR REPLACE VIEW vw_today_attendance AS
SELECT
    t.full_name,
    t.email,
    a.timestamp,
    a.status,
    a.reason,
    a.latitude,
    a.longitude
FROM attendance_logs a
JOIN teachers t ON t.teacher_id = a.teacher_id
WHERE a.timestamp::date = CURRENT_DATE
ORDER BY a.timestamp DESC;


CREATE OR REPLACE VIEW vw_attendance_summary AS
SELECT
    t.teacher_id,
    t.full_name,
    COUNT(*) FILTER (WHERE a.status = 'success') AS success_count,
    COUNT(*) FILTER (WHERE a.status = 'failure') AS failure_count,
    COUNT(*) AS total_attempts,
    MAX(a.timestamp) FILTER (WHERE a.status = 'success') AS last_success
FROM teachers t
LEFT JOIN attendance_logs a ON a.teacher_id = t.teacher_id
GROUP BY t.teacher_id, t.full_name;
