# Phase 3: Activity Tracking Implementation

## Current State Analysis

### Activity Context Manager (from origin/feat/database)
- **Location**: `getgather/mcp/main.py:17-30`
- **Purpose**: Context manager for tracking activity lifecycle
- **Behavior**: Creates activity record on start, updates end_time on completion
- **Integration**: Used in AuthMiddleware for automatic activity tracking

### Activity Model Structure
- **Base Model**: `getgather/database/models.py` - DBModel with CRUD operations
- **Activity Model**: `getgather/database/repositories/activity_repository.py`
- **Fields**: `brand_id`, `name`, `start_time`, `end_time`, `execution_time_ms`

### Current Usage Pattern
```python
async with activity(brand_id="netflix", name="login"):
    # Tool execution happens here
    # Activity automatically tracks start/end time
```

## Implementation Plan

### 1. Compare and Merge Activity Infrastructure from origin/feat/database

Instead of overriding, compare files first to identify what needs to be added or modified:

```bash
# Compare each file to see differences
diff -u getgather/mcp/main.py <(git show origin/feat/database:getgather/mcp/main.py)
diff -u getgather/database/models.py <(git show origin/feat/database:getgather/database/models.py) || echo "File doesn't exist locally"
diff -u getgather/database/connection.py <(git show origin/feat/database:getgather/database/connection.py) || echo "File doesn't exist locally"
diff -u getgather/database/repositories/activity_repository.py <(git show origin/feat/database:getgather/database/repositories/activity_repository.py) || echo "File doesn't exist locally"
diff -u getgather/database/schema.sql <(git show origin/feat/database:getgather/database/schema.sql) || echo "File doesn't exist locally"
```

### 2. Selective Updates Based on Diff Analysis

Based on comparison results:
- **Missing files**: Create new files from remote branch
- **Modified files**: Merge changes carefully to preserve local modifications
- **main.py**: Add activity context manager and update AuthMiddleware without losing current functionality

### 3. RRWeb Recording Implementation

**Current State**: Database infrastructure exists, but no actual recording mechanism.

**Browser Integration Points**:
- **Patchright/Playwright**: `getgather/browser/session.py` - BrowserSession manages browser contexts
- **Recording Injection Point**: `BrowserSession.start()` (line 51) - where rrweb script should be injected
- **Active Context**: `BrowserSession.context` - browser context where recording happens
- **Active Page**: `BrowserSession.page()` - current page for DOM event capture

**Implementation Components**:

**RRWeb Recording Integration (Context Variables + Recording Manager)**:

**Problem Analysis**:
- Activity tracking (AuthMiddleware) happens before browser session creation
- Browser session lifecycle ≠ Activity lifecycle  
- Multiple browser session entry points
- Need seamless integration without breaking existing APIs

**Solution: Context Variables + Recording Manager**

```python
# 1. Context Variable for Activity Tracking
from contextvars import ContextVar

current_activity: ContextVar[Activity | None] = ContextVar('current_activity', default=None)

# 2. Recording Manager (Handles Lifecycle Mismatches)
class RecordingManager:
    _instance = None
    _active_recordings: dict[int, BrowserSession] = {}  # activity_id -> session
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
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
                # Save to database
                recording = RRWebRecording.from_events(activity_id, events)
                recording.add()

# 3. Enhanced Activity Context Manager
@asynccontextmanager
async def activity(name: str, brand_id: str = ""):
    activity_record = Activity(brand_id=brand_id, name=name, start_time=datetime.now(UTC))
    activity_id = activity_record.add()
    
    # Set context variable so browser sessions can find current activity
    token = current_activity.set(activity_record)
    
    try:
        yield activity_record
    finally:
        # Stop any recordings for this activity
        await RecordingManager.stop_for_activity(activity_id)
        current_activity.reset(token)
        activity_record.update_end_time(datetime.now(UTC))

# 4. Minimal Change to start_browser_session() in getgather/mcp/shared.py
async def start_browser_session(brand_id: BrandIdEnum) -> BrowserSession:
    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.start()
    
    # Auto-start recording if we're in an activity context
    await RecordingManager.start_if_activity_exists(browser_session)
    
    return browser_session

# 5. Enhanced BrowserSession Recording Methods
class BrowserSession:
    async def start_recording(self):
        """Inject rrweb recording script and start capturing events."""
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
        """Stop recording and return captured events."""
        page = await self.page()
        
        # Stop recording and get events
        events = await page.evaluate("""
            if (window.stopRRWebRecording) {
                window.stopRRWebRecording();
            }
            return window.rrwebEvents || [];
        """)
        
        return events
```


### 4. Integration Benefits

**Automatic Integration**:
1. **No Breaking Changes**: Existing APIs unchanged, just enhanced
2. **Lifecycle Management**: Recording Manager handles activity/session lifecycle mismatches  
3. **Graceful Degradation**: Works whether or not browsers are used
4. **Context Propagation**: Context variables flow naturally through async call stack
5. **One-to-one relationship**: Each activity can have one recording
6. **Automatic recording**: Browser sessions during activities are automatically recorded

## Key Features

### Automatic Activity Tracking
- **Tool Execution**: Every MCP tool call creates an activity record
- **Brand Association**: Activities linked to specific brands (netflix, amazon, etc.)
- **Timing**: Automatic start_time and end_time calculation
- **Execution Duration**: Calculated in milliseconds

### Middleware Integration
```python
class AuthMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        async with activity(brand_id=brand_id, name=context.message.name):
            return await call_next(context)
```

### Activity Types Tracked
1. **General Tools**: Tools with "general_tool" tag (no brand_id)
2. **Brand Tools**: Brand-specific tools (netflix_login, amazon_search, etc.)
3. **Auth Activities**: Authentication flows for brand connections

## Files to Compare/Create/Merge

### Files to Compare and Merge
- `getgather/mcp/main.py` - Add activity context manager and enhanced middleware
- `getgather/database/models.py` - Create if missing, merge if exists
- `getgather/database/connection.py` - Create if missing, merge if exists 
- `getgather/database/repositories/activity_repository.py` - Create new file
- `getgather/database/schema.sql` - Create if missing, add activities table if exists

### Extend/Create New
- Add rrweb_recordings table to schema.sql (from plan.md) ✅ Already exists
- Create rrweb_recordings_repository.py (from plan_2.md) ✅ Already exists
- **Create `getgather/recording/manager.py`** - RecordingManager singleton class
- **Modify `getgather/browser/session.py`** - Add start_recording() and stop_recording() methods  
- **Update `getgather/mcp/main.py`** - Enhanced activity context manager with context variable
- **Modify `getgather/mcp/shared.py`** - Add recording integration to start_browser_session()

### Integration Flow (Context Variables + Recording Manager)
1. **AuthMiddleware** calls activity context manager with brand_id
2. **Activity context manager** sets current_activity context variable
3. **Tool execution** calls start_browser_session() 
4. **start_browser_session()** checks current_activity and auto-starts recording
5. **Browser interactions** are recorded via rrweb
6. **Activity ends**: RecordingManager stops recording, saves events to database
7. **Result**: Activity record + linked rrweb recording in database

## Testing Activity Tracking

### Manual Testing
```python
# Test activity creation
from getgather.database.repositories.activity_repository import Activity

activity = Activity(
    brand_id="netflix",
    name="test_login",
    start_time=datetime.now(UTC)
)
activity_id = activity.add()

# Test activity update
activity.update_end_time(datetime.now(UTC))
```

### Integration Testing
```bash
# Run MCP server and execute tools
# Check database for activity records
sqlite3 your_database.db "SELECT * FROM activities ORDER BY created_at DESC LIMIT 10"
```

## Benefits

1. **Automatic Tracking**: Zero-code activity tracking for all MCP tools
2. **Brand Association**: Track which brand each activity belongs to
3. **Performance Metrics**: Execution time tracking for optimization
4. **Audit Trail**: Complete history of all tool executions
5. **RRWeb Integration**: Direct link between activities and screen recordings

## Integration with Existing Plans

- **Plan 1 (Database)**: Activities table already defined, just need rrweb_recordings linkage
- **Plan 2 (API)**: API endpoints can query activities and their associated recordings
- **This Plan**: Provides the activity data that other plans depend on
