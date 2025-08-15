import asyncio
from typing import Any


class RRWebEventManager:
    """In-memory storage for RRWeb events tied to activities."""
    
    def __init__(self):
        self._events: dict[int, list[dict[str, Any]]] = {}  # activity_id -> events
        self._lock = asyncio.Lock()
    
    async def add_event_to_activity(self, activity_id: int, event: dict[str, Any]) -> None:
        """Add an RRWeb event to an activity."""
        async with self._lock:
            if activity_id not in self._events:
                self._events[activity_id] = []
            self._events[activity_id].append(event)
    
    async def get_events_by_activity_id(self, activity_id: int) -> list[dict[str, Any]]:
        """Get all events for an activity."""
        async with self._lock:
            return self._events.get(activity_id, []).copy()
    
    async def get_recording_counts(self) -> dict[int, int]:
        """Get event counts per activity."""
        async with self._lock:
            return {activity_id: len(events) for activity_id, events in self._events.items()}
    
    async def clear_events_for_activity(self, activity_id: int) -> None:
        """Clear all events for a specific activity."""
        async with self._lock:
            if activity_id in self._events:
                del self._events[activity_id]


# Global instance
rrweb_event_manager = RRWebEventManager()