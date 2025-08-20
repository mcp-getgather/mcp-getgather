-- Schema for the database tables

-- Brand states table
CREATE TABLE IF NOT EXISTS brand_states (
    brand_id TEXT PRIMARY KEY,
    browser_profile_id TEXT NOT NULL,
    is_connected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
