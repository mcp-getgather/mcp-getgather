"""Context variables for tracking state across async operations."""

from contextvars import ContextVar

from getgather.database.repositories.activity_repository import Activity

# Context variable to track the current activity across async calls
current_activity: ContextVar[Activity | None] = ContextVar('current_activity', default=None)