from typing import TYPE_CHECKING

from getgather.database.models import RRWebRecording

if TYPE_CHECKING:
    from getgather.browser.session import BrowserSession
    from getgather.database.repositories.activity_repository import Activity


class RecordingManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active_recordings = {}
        return cls._instance

    @classmethod
    def _get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def start_if_activity_exists(cls, session: "BrowserSession") -> None:
        """Start recording if there's a current activity context"""
        from getgather.recording.context import current_activity
        
        if activity := current_activity.get():
            await session.start_recording()
            instance = cls._get_instance()
            instance._active_recordings[activity.id] = session

    @classmethod
    async def stop_for_activity(cls, activity_id: int) -> None:
        """Stop recording and save events for an activity"""
        instance = cls._get_instance()
        if session := instance._active_recordings.pop(activity_id, None):
            events = await session.stop_recording()
            if events:
                recording = RRWebRecording.from_events(activity_id, events)
                recording.add()