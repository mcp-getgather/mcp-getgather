# RRWeb Recording Architecture

## Overview

This document outlines the complete architecture for integrating rrweb (record and replay web) functionality into the MCP GetGather system. The architecture consists of three main components: database storage, API endpoints, and automatic activity tracking with browser recording.

## Architecture Components

### 1. Database Layer

#### Core Tables

```sql
-- Activities table (tracks user operations)
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id TEXT NOT NULL,                               -- Brand/website (e.g., "netflix", "amazon")
    name TEXT NOT NULL,                                   -- Activity name (e.g., "login", "search")
    start_time TIMESTAMP NOT NULL,                        -- Activity start time
    end_time TIMESTAMP NULL,                              -- Activity end time (NULL if running)
    execution_time_ms INTEGER NULL,                       -- Duration in milliseconds
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- RRWeb recordings table (stores browser interaction recordings)
CREATE TABLE IF NOT EXISTS rrweb_recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL UNIQUE,                  -- One recording per activity
    events_json TEXT NOT NULL,                            -- Complete rrweb events as JSON
    event_count INTEGER NOT NULL,                         -- Number of events
    start_timestamp INTEGER NOT NULL,                     -- First event timestamp
    end_timestamp INTEGER NOT NULL,                       -- Last event timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

-- Performance index
CREATE INDEX IF NOT EXISTS idx_rrweb_recordings_activity_id ON rrweb_recordings(activity_id);
```

#### Data Models

```python
# Base model with CRUD operations
class DBModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    created_at: datetime | None = None

# RRWeb recording model
class RRWebRecording(DBModel):
    activity_id: int
    events_json: str
    event_count: int
    start_timestamp: int
    end_timestamp: int
    
    @property
    def events(self) -> list[dict[str, Any]]:
        """Parse and return events as Python list"""
        return json.loads(self.events_json)
    
    @classmethod
    def from_events(cls, activity_id: int, events: list[dict[str, Any]]) -> Self:
        """Create recording from rrweb events list"""
        return cls(
            activity_id=activity_id,
            events_json=json.dumps(events),
            event_count=len(events),
            start_timestamp=events[0]["timestamp"] if events else 0,
            end_timestamp=events[-1]["timestamp"] if events else 0
        )
```

### 2. API Layer

#### Events Endpoint

```python
# File: getgather/api/routes/events/endpoints.py
from fastapi import APIRouter, HTTPException
from getgather.database.repositories.rrweb_recordings_repository import RrwebRecordingsRepository

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("")
async def get_events(activity_id: str):
    """Get rrweb events for a specific activity"""
    recording = RrwebRecordingsRepository.get_by_activity_id(activity_id)
    if not recording:
        raise HTTPException(
            status_code=404, 
            detail=f"No recording found for activity {activity_id}"
        )
    
    return {"events": recording.events}
```

#### Frontend Integration

```typescript
// Updated replay.tsx
const response = await fetch(`/api/events?activity_id=${activityId}`);
const data = await response.json();
setEvents(data.events);
```

### 3. Activity Tracking & Recording System

#### Context Management

```python
from contextvars import ContextVar
from getgather.database.repositories.activity_repository import Activity

# Global context variable for current activity
current_activity: ContextVar[Activity | None] = ContextVar('current_activity', default=None)
```

#### Recording Manager

```python
class RecordingManager:
    """Manages browser recording lifecycle across activity contexts"""
    
    _instance = None
    _active_recordings: dict[int, BrowserSession] = {}
    
    @classmethod 
    async def start_if_activity_exists(cls, session: BrowserSession):
        """Start recording if there's a current activity context"""
        if activity := current_activity.get():
            await session.start_recording()
            cls._instance._active_recordings[activity.id] = session
    
    @classmethod
    async def stop_for_activity(cls, activity_id: int):
        """Stop recording and save events for an activity"""
        if session := cls._instance._active_recordings.pop(activity_id, None):
            events = await session.stop_recording()
            if events:
                recording = RRWebRecording.from_events(activity_id, events)
                recording.add()
```

#### Enhanced Activity Context Manager

```python
@asynccontextmanager
async def activity(name: str, brand_id: str = "") -> AsyncGenerator[None, None]:
    """Context manager for tracking activity lifecycle with recording"""
    activity_record = Activity(
        brand_id=brand_id,
        name=name,
        start_time=datetime.now(UTC),
    )
    activity_id = activity_record.add()
    
    # Set context variable for browser sessions to discover
    token = current_activity.set(activity_record)
    
    try:
        yield
    finally:
        # Stop any recordings for this activity
        await RecordingManager.stop_for_activity(activity_id)
        current_activity.reset(token)
        activity_record.update_end_time(end_time=datetime.now(UTC))
```

#### Browser Session Integration

```python
class BrowserSession:
    async def start_recording(self):
        """Inject rrweb recording script and start capturing events"""
        page = await self.page()
        
        # Inject rrweb recording script
        await page.add_script_tag(url="https://cdn.jsdelivr.net/npm/rrweb@2/dist/rrweb.min.js")
        
        # Start recording
        await page.evaluate("""
            window.rrwebEvents = [];
            window.stopRRWebRecording = rrweb.record({
                emit(event) {
                    window.rrwebEvents.push(event);
                }
            });
        """)

    async def stop_recording(self) -> list:
        """Stop recording and return captured events"""
        page = await self.page()
        
        events = await page.evaluate("""
            if (window.stopRRWebRecording) {
                window.stopRRWebRecording();
            }
            return window.rrwebEvents || [];
        """)
        
        return events

# Auto-start recording in browser sessions
async def start_browser_session(brand_id: BrandIdEnum) -> BrowserSession:
    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.start()
    
    # Auto-start recording if we're in an activity context
    await RecordingManager.start_if_activity_exists(browser_session)
    
    return browser_session
```

#### Middleware Integration

```python
class AuthMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]):
        """Automatically track all tool executions as activities"""
        if not context.fastmcp_context:
            return await call_next(context)

        tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)

        # Track general tools
        if "general_tool" in tool.tags:
            async with activity(name=context.message.name):
                return await call_next(context)

        # Track brand-specific tools
        brand_id = context.message.name.split("_")[0]
        async with activity(brand_id=brand_id, name=context.message.name):
            return await call_next(context)
```

## Integration Flow

1. **Tool Execution**: User calls MCP tool (e.g., `netflix_login`)
2. **Activity Creation**: AuthMiddleware creates activity record and sets context variable
3. **Browser Session**: Tool starts browser session, which auto-detects activity context
4. **Recording Start**: Browser session injects rrweb script and begins recording
5. **User Interactions**: All DOM events captured by rrweb
6. **Activity End**: Context manager triggers recording stop and database save
7. **Data Storage**: Activity record + rrweb events saved with foreign key relationship

## File Structure

```
getgather/
├── database/
│   ├── models.py                     # DBModel, RRWebRecording
│   ├── schema.sql                    # Database tables
│   ├── repositories/
│   │   ├── activity_repository.py    # Activity CRUD
│   │   └── rrweb_recordings_repository.py  # Recording CRUD
├── recording/
│   ├── context.py                    # current_activity context variable
│   └── manager.py                    # RecordingManager class
├── browser/
│   └── session.py                    # Enhanced with recording methods
├── mcp/
│   ├── main.py                       # Enhanced activity context manager
│   └── shared.py                     # Auto-recording browser session
└── api/
    ├── main.py                       # Include events router
    └── routes/events/
        └── endpoints.py              # /api/events endpoint
```

## Key Benefits

1. **Automatic Integration**: Zero-code recording for all browser-based MCP tools
2. **Lifecycle Management**: Handles activity/session mismatches gracefully
3. **One-to-One Mapping**: Each activity gets exactly one recording
4. **Context Propagation**: Uses Python contextvars for seamless integration
5. **No Breaking Changes**: Existing APIs remain unchanged
6. **Performance Tracking**: Complete audit trail with timing data
7. **Replay Capability**: Full browser interaction replay via rrweb player

## RRWeb Event Analysis

- **Event Types**: Type 2 (meta), Type 3 (DOM mutations), Type 4 (interactions)
- **Event Structure**: `{type, timestamp, data}` where data varies by type
- **Storage Format**: JSON string in SQLite with efficient JSONB querying
- **Typical Size**: 76 to 28,753 characters per event, ~757 events per session

## Query Examples

```sql
-- Get all events for an activity
SELECT events_json FROM rrweb_recordings WHERE activity_id = 1;

-- Get event count without parsing JSON
SELECT event_count FROM rrweb_recordings WHERE activity_id = 1;

-- Get events of specific type
SELECT json_extract(value, '$') FROM rrweb_recordings, json_each(events_json)
WHERE activity_id = 1 AND json_extract(value, '$.type') = 3;
```