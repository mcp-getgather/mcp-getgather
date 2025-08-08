-- Schema for the database tables

-- Brand states table
CREATE TABLE IF NOT EXISTS brand_states (
    brand_id TEXT PRIMARY KEY,
    browser_profile_id TEXT NOT NULL,
    is_connected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Activities table
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id TEXT NOT NULL,
    name TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NULL,
    execution_time_ms INTEGER NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- rrweb recordings table
CREATE TABLE IF NOT EXISTS rrweb_recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL UNIQUE,
    events_json TEXT NOT NULL,
    event_count INTEGER NOT NULL,
    start_timestamp INTEGER NOT NULL,
    end_timestamp INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

-- Index for fast retrieval by activity
CREATE INDEX IF NOT EXISTS idx_rrweb_recordings_activity_id ON rrweb_recordings(activity_id);
