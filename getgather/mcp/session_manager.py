import logging
from typing import Any, ClassVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SessionData(BaseModel):
    """Pydantic model for hosted link session data."""

    connected_brand: list[str]
    browser_profile_id: str


class SessionManager:
    """
    Manages creation, storage, retrieval, and update of brand auth status.
    """

    _session_store: ClassVar[dict[str, SessionData]] = {}

    @classmethod
    def create_session(
        cls,
        browser_profile_id: str,
        session_id: str | None = None,
    ) -> str:
        """Create a new session with the given parameters."""
        session_key = session_id or "local"
        if session_key not in cls._session_store:
            cls._session_store[session_key] = SessionData(
                connected_brand=[], browser_profile_id=browser_profile_id
            )
        return session_key

    @classmethod
    def is_brand_connected(cls, brand_id: str, session_id: str | None = None) -> bool:
        """Retrieve brand auth status for the given session ID."""
        session_key = session_id or "local"
        if session_key not in cls._session_store:
            raise ValueError(f"Session {session_key} not found")
        return brand_id in cls._session_store[session_key].connected_brand

    @classmethod
    def update_connected_brand(
        cls,
        brand_id: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new brand auth status with the given parameters."""
        session_key = session_id or "local"
        if session_key not in cls._session_store:
            raise ValueError(f"Session {session_key} not found")
        if brand_id not in cls._session_store[session_key].connected_brand:
            cls._session_store[session_key].connected_brand.append(brand_id)
        return {"session_id": session_id, "brand_id": brand_id}

    @classmethod
    def get_browser_profile_id(cls, session_id: str | None = None) -> str:
        """Retrieve brand auth status for the given session ID."""
        session_key = session_id or "local"
        if session_key not in cls._session_store:
            raise ValueError(f"Session {session_key} not found")
        return cls._session_store[session_key].browser_profile_id
