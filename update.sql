ALTER TABLE attendance_logs ADD COLUMN IF NOT EXISTS attendance_mark VARCHAR(20) DEFAULT 'present';

CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB NOT NULL
);

INSERT INTO settings (key, value) VALUES 
('attendance_rules', '{"class_start": "09:00", "half_day_limit": "10:05", "absent_limit": "11:00"}'),
('verification_limits', '{"max_checkin_attempts": 4, "max_checkout_attempts": 10}')
ON CONFLICT (key) DO NOTHING;
