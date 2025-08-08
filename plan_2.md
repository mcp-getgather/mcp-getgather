# Phase 2: API for rrweb Events Retrieval

## Current State Analysis

### Current rrweb Player Implementation
- **Location**: `frontend/src/pages/replay.tsx:15`
- **Current data source**: `fetch("/output.json")` from public static file
- **URL pattern**: `/replay?id=activity-001` (activity_id in query param)
- **Behavior**: Loads static JSON file, ignores activity_id parameter

### API Infrastructure
- **Main API**: `getgather/api/main.py` using FastAPI
- **Existing routers**: auth, brands, link routes
- **Static mounting**: `/assets` for frontend assets

## Proposed API Design

### New Endpoint
```python
@app.get("/api/events")
async def get_events(activity_id: str):
    """Get rrweb events for a specific activity"""
    # Query rrweb_recordings table by activity_id
    # Return events_json as JSON response
```

### Updated Frontend
```typescript
// Change in replay.tsx:15
const response = await fetch(`/api/events?activity_id=${activityId}`);
```

## Implementation Plan

### 1. Create Events API Route
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
        raise HTTPException(status_code=404, detail=f"No recording found for activity {activity_id}")
    
    return {"events": recording.events_json}
```

### 2. Update Main API
```python
# Add to getgather/api/main.py
from getgather.api.routes.events.endpoints import router as events_router
app.include_router(events_router)
```

### 3. Update Frontend
```typescript
// Update in frontend/src/pages/replay.tsx:15
const response = await fetch(`/api/events?activity_id=${activityId}`);
const data = await response.json();
setEvents(data.events);
```

## Files to Create/Modify

### New Files
- `getgather/api/routes/events/__init__.py`
- `getgather/api/routes/events/endpoints.py`  
- `getgather/database/repositories/rrweb_recordings_repository.py`

### Modified Files
- `getgather/api/main.py` (add events router)
- `frontend/src/pages/replay.tsx` (update fetch URL)

## Backward Compatibility
- Keep `/output.json` static file for development
- API endpoint returns same JSON structure as current static file
- No changes to RRWebPlayer component interface

## Testing
```bash
# Test the new API endpoint
curl "http://localhost:8000/api/events?activity_id=1"

# Should return:
# {"events": [...rrweb events array...]}
```