from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

from nanoid import generate

from getgather.camel_model import CamelModel
from getgather.config import settings
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger

FRIENDLY_CHARS: str = "23456789abcdefghijkmnpqrstuvwxyz"


class LinkData(CamelModel):
    """Pydantic model for hosted link data."""

    brand_id: BrandIdEnum
    profile_id: str | None
    redirect_url: str
    status: str
    status_message: str | None = None
    created_at: str
    expires_at: str
    extract_result: Any | None


class LinkDataUpdate(CamelModel):
    """A subset of LinkData fields that can be updated."""

    status: str
    status_message: str | None = None
    extract_result: list[dict[str, Any]] | None = None
    profile_id: str | None = None


class HostedLinkManager:
    """
    Manages creation, storage, retrieval, and update of hosted links.
    In production, swap out the in-memory store for a persistent database.
    """

    _link_store: ClassVar[dict[str, LinkData]] = {}

    @classmethod
    def _generate_link_id(cls) -> str:
        """Generate a link id that encodes the server name and a 6-letter random string."""
        return f"{settings.SERVER_NAME}{generate(FRIENDLY_CHARS, 6)}"

    @classmethod
    def create_link(
        cls,
        brand_id: BrandIdEnum,
        redirect_url: str,
        url_lifetime_seconds: int = 900,
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new hosted link with the given parameters."""
        link_id = cls._generate_link_id()
        expiration_time = datetime.now(timezone.utc) + timedelta(seconds=url_lifetime_seconds)
        link_data = LinkData(
            brand_id=brand_id,
            profile_id=profile_id,
            redirect_url=redirect_url,
            status="pending",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            expires_at=expiration_time.replace(tzinfo=None).isoformat() + "Z",
            extract_result=None,
        )
        cls._link_store[link_id] = link_data
        logger.info(f"Created hosted link {link_id} for brand {brand_id}")
        return {
            "link_id": link_id,
            "expiration": link_data.expires_at,
            **link_data.model_dump(),
        }

    @classmethod
    def get_link_data(cls, link_id: str) -> LinkData | None:
        """Retrieve link data for the given link ID."""
        link_data = cls._link_store.get(link_id)
        if link_data and cls.is_expired(link_data):
            if link_data.status != "expired":
                link_data.status = "expired"
                logger.debug(f"Updated link {link_id} status to expired during retrieval")
        return link_data

    @classmethod
    def update_link(cls, link_id: str, update_data: LinkDataUpdate) -> LinkData | None:
        """Update link data and return the updated link data."""

        link_data = cls._link_store.get(link_id)
        if not link_data:
            return None

        if cls.is_expired(link_data):
            link_data.status = "expired"
            logger.warning(f"Attempted to update expired link {link_id}")
            return None

        update_dict = update_data.model_dump(exclude_none=True)
        if update_dict:
            updated_link = link_data.model_copy(update=update_dict)
            cls._link_store[link_id] = updated_link
            logger.info(f"Updated hosted link {link_id} with data: {update_data}")
            return updated_link
        return link_data

    @classmethod
    def is_expired(cls, link_data: LinkData) -> bool:
        """Check if the given link data represents an expired link."""
        expires_at_str = str(link_data.expires_at).replace("Z", "+00:00")
        expires_at = datetime.fromisoformat(expires_at_str)
        return datetime.now(timezone.utc) > expires_at
