-- Patient Safety Database Initialization
-- PostgreSQL 15+

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create audit log table first (no foreign keys)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    user_role VARCHAR(50),
    username VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    action_detail JSONB,
    result VARCHAR(20) NOT NULL,
    previous_hash VARCHAR(64),
    entry_hash VARCHAR(64) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);

-- Revoke UPDATE and DELETE on audit_logs (append-only)
-- Note: This should be done at role level in production
COMMENT ON TABLE audit_logs IS 'Append-only audit log table for PIPA compliance';

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'reporter',
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Create incidents table
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    grade VARCHAR(20) NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    location VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    immediate_action TEXT NOT NULL,
    reported_at TIMESTAMP NOT NULL,
    reporter_name VARCHAR(100),
    root_cause TEXT,
    improvements TEXT,
    patient_info BYTEA,  -- Encrypted
    reporter_id INTEGER NOT NULL REFERENCES users(id),
    department VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(category);
CREATE INDEX IF NOT EXISTS idx_incidents_grade ON incidents(grade);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_reporter_id ON incidents(reporter_id);

-- Create attachments table
CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    storage_uri VARCHAR(500) NOT NULL,
    incident_id INTEGER NOT NULL REFERENCES incidents(id),
    uploaded_by_id INTEGER NOT NULL REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_attachments_incident_id ON attachments(incident_id);

-- Create approvals table
CREATE TABLE IF NOT EXISTS approvals (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES incidents(id),
    approver_id INTEGER NOT NULL REFERENCES users(id),
    level VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    comment TEXT,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approvals_incident_id ON approvals(incident_id);
CREATE INDEX IF NOT EXISTS idx_approvals_level ON approvals(level);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);

-- Insert default admin user (change password in production!)
-- Password: admin123 (hashed with bcrypt)
INSERT INTO users (username, email, hashed_password, full_name, role, is_active)
VALUES (
    'admin',
    'admin@hospital.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYo/NAXY1wQe',
    '시스템관리자',
    'admin',
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- Insert test users for development
INSERT INTO users (username, email, hashed_password, full_name, role, department, is_active)
VALUES
    ('reporter1', 'reporter1@hospital.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYo/NAXY1wQe', '김간호', 'reporter', '301병동', TRUE),
    ('qps1', 'qps1@hospital.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYo/NAXY1wQe', '박QI담당', 'qps_staff', 'QI팀', TRUE),
    ('vicechair', 'vicechair@hospital.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYo/NAXY1wQe', '이부원장', 'vice_chair', NULL, TRUE),
    ('director', 'director@hospital.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYo/NAXY1wQe', '최원장', 'director', NULL, TRUE)
ON CONFLICT (username) DO NOTHING;

-- Grant permissions (adjust for production)
-- GRANT SELECT, INSERT ON audit_logs TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON users, incidents, attachments, approvals TO app_user;
