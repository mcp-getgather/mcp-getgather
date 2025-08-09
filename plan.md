# Plan: Store rrweb Events in SQLite Database

## Analysis Summary
- **rrweb data**: 757 events with types 2, 3, 4 containing `{type, timestamp, data}` structure
- **Existing activity table**: Found in `origin/feat/database` branch with schema for tracking activities
- **Current branch**: No database infrastructure exists yet

## Proposed Data Structure

```sql
-- Activity table schema (unchanged from origin/feat/database)
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,                     -- Unique identifier for each activity
    brand_id TEXT NOT NULL,                                   -- Brand/website being automated (e.g., "netflix", "amazon")
    name TEXT NOT NULL,                                       -- Human-readable activity name (e.g., "Web Scraping Session")
    start_time TIMESTAMP NOT NULL,                            -- When the activity began
    end_time TIMESTAMP NULL,                                  -- When the activity completed (NULL if still running)
    execution_time_ms INTEGER NULL,                           -- Total duration in milliseconds
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP   -- When this record was created
);

-- New rrweb recordings table (only addition needed)
CREATE TABLE IF NOT EXISTS rrweb_recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,                     -- Unique identifier for each recording
    activity_id INTEGER NOT NULL UNIQUE,                      -- Links to activities table - one recording per activity
    events_json TEXT NOT NULL,                                -- Complete rrweb events array as JSON string (use JSONB for efficiency)
    event_count INTEGER NOT NULL,                             -- Number of events in the recording
    start_timestamp INTEGER NOT NULL,                         -- Timestamp of first event (from events_json->'$[0].timestamp')
    end_timestamp INTEGER NOT NULL,                           -- Timestamp of last event (from events_json->'$[#-1].timestamp')
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- When this record was stored in database
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

-- Index for fast retrieval by activity
CREATE INDEX IF NOT EXISTS idx_rrweb_recordings_activity_id ON rrweb_recordings(activity_id);
```

## Implementation Steps

1. **Copy database infrastructure**: Bring existing database files as-is from origin/feat/database
2. **Add rrweb table**: Extend schema with rrweb_recordings table
3. **Create rrweb models**: Follow existing Activity pattern
4. **Add repository**: Create rrweb_recordings_repository.py

**Note**: For testing, you can manually insert the output.json data or create a simple migration script

## Files to Copy from origin/feat/database

```bash
# Core database infrastructure
git show origin/feat/database:getgather/database/connection.py > getgather/database/connection.py
git show origin/feat/database:getgather/database/models.py > getgather/database/models.py
git show origin/feat/database:getgather/database/migrate.py > getgather/database/migrate.py

# Repository pattern
git show origin/feat/database:getgather/database/repositories/activity_repository.py > getgather/database/repositories/activity_repository.py
git show origin/feat/database:getgather/database/repositories/brand_state_repository.py > getgather/database/repositories/brand_state_repository.py

# Schema (extend this with rrweb_recordings table)
git show origin/feat/database:getgather/database/schema.sql > getgather/database/schema.sql

# Configuration (if database path is defined here)
git show origin/feat/database:getgather/config.py > getgather/config.py
```

## Simple Migration Script Example
```python
import json
import sqlite3
from datetime import datetime

# Load output.json
with open('getgather/api/frontend/output.json', 'r') as f:
    events = json.load(f)

# Insert into database
conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# Create sample activity
activity_id = cursor.execute("""
    INSERT INTO activities (brand_id, name, start_time) 
    VALUES (?, ?, ?)
""", ("test", "Sample Recording", datetime.now())).lastrowid

# Insert rrweb recording
cursor.execute("""
    INSERT INTO rrweb_recordings (activity_id, events_json, event_count, start_timestamp, end_timestamp)
    VALUES (?, ?, ?, ?, ?)
""", (
    activity_id,
    json.dumps(events),
    len(events),
    events[0]['timestamp'],
    events[-1]['timestamp']
))

conn.commit()
conn.close()
```

## Key Design Decisions
- **Foreign key relationship**: Link recordings to activities for logical grouping
- **JSONB storage**: Use SQLite's binary JSONB format for efficient storage and querying
- **JSON operators**: Leverage `->` and `->>` operators for easy data extraction
- **Single query retrieval**: Get complete rrweb data with `SELECT events_json FROM rrweb_recordings WHERE activity_id = ?`

## SQLite JSON Query Examples
```sql
-- Get all events for an activity
SELECT events_json FROM rrweb_recordings WHERE activity_id = 1;

-- Get event count without parsing JSON
SELECT event_count FROM rrweb_recordings WHERE activity_id = 1;

-- Extract specific event by index
SELECT events_json -> '$[0]' FROM rrweb_recordings WHERE activity_id = 1;

-- Get events of specific type
SELECT json_extract(value, '$') FROM rrweb_recordings, json_each(events_json)
WHERE activity_id = 1 AND json_extract(value, '$.type') = 3;
```
- **Indexing**: Add indexes on activity_id and timestamp for efficient retrieval
- **Retrieval**: Query all events for an activity using `activity_id`

## rrweb Event Analysis
- **Event types found**: Type 2 (2 events), Type 3 (753 events), Type 4 (2 events)
- **Event structure**: `{type, timestamp, data}` where data varies by type
- **Data sizes**: Range from 76 to 28,753 characters per event
- **Total events**: 757 events in current output.json