from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

from nanoid import generate

from getgather.camel_model import CamelModel
from getgather.logs import logger

FRIENDLY_CHARS: str = "23456789abcdefghijkmnpqrstuvwxyz"


class SessionData(CamelModel):
    """Pydantic model for hosted link session data."""

    brand_id: str
    profile_id: str | None
    redirect_url: str
    status: str
    status_message: str | None = None
    created_at: str
    expires_at: str
    extract_result: Any | None


class SessionDataUpdate(CamelModel):
    """A subset of SessionData fields that can be updated."""

    status: str
    status_message: str | None = None
    extract_result: list[dict[str, Any]] | None = None
    profile_id: str | None = None


class HostedLinkManager:
    """
    Manages creation, storage, retrieval, and update of hosted link sessions.
    In production, swap out the in-memory store for a persistent database.
    """

    _session_store: ClassVar[dict[str, SessionData]] = {}

    @classmethod
    def create_session(
        cls,
        brand_id: str,
        redirect_url: str,
        url_lifetime_seconds: int = 900,
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new hosted link session with the given parameters."""
        session_id = generate(FRIENDLY_CHARS, 6)
        expiration_time = datetime.now(timezone.utc) + timedelta(seconds=url_lifetime_seconds)
        session_data = SessionData(
            brand_id=brand_id,
            profile_id=profile_id,
            redirect_url=redirect_url,
            status="pending",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            expires_at=expiration_time.replace(tzinfo=None).isoformat() + "Z",
            extract_result=None,
        )
        cls._session_store[session_id] = session_data
        logger.info(f"Created hosted link session {session_id} for brand {brand_id}")
        return {
            "session_id": session_id,
            "expiration": session_data.expires_at,
            **session_data.model_dump(),
        }

    @classmethod
    def get_session_data(cls, session_id: str) -> SessionData | None:
        """Retrieve session data for the given session ID."""
        session_data = cls._session_store.get(session_id)
        if session_data and cls.is_expired(session_data):
            if session_data.status != "expired":
                session_data.status = "expired"
                logger.debug(f"Updated session {session_id} status to expired during retrieval")
        return session_data

    @classmethod
    def update_session(cls, session_id: str, update_data: SessionDataUpdate) -> SessionData | None:
        """Update session data and return the updated session data."""

        session_data = cls._session_store.get(session_id)
        if not session_data:
            return None

        if cls.is_expired(session_data):
            session_data.status = "expired"
            logger.warning(f"Attempted to update expired session {session_id}")
            return None

        update_dict = update_data.model_dump(exclude_none=True)
        if update_dict:
            updated_session = session_data.model_copy(update=update_dict)
            cls._session_store[session_id] = updated_session
            logger.info(f"Updated hosted link session {session_id} with data: {update_data}")
            return updated_session
        return session_data

    @classmethod
    def is_expired(cls, session_data: SessionData) -> bool:
        """Check if the given session data represents an expired session."""
        expires_at_str = str(session_data.expires_at).replace("Z", "+00:00")
        expires_at = datetime.fromisoformat(expires_at_str)
        return datetime.now(timezone.utc) > expires_at
