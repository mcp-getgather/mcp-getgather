from typing import ClassVar

from pydantic import BaseModel

from getgather.connectors.spec_loader import BrandIdEnum


class BrandState(BaseModel):
    browser_profile_id: str
    is_connected: bool = False


class BrandConnectionStore:
    """
    Store brands connection statuses.
    This will soon be replaced by a database.
    """

    _brand_states: ClassVar[dict[BrandIdEnum, BrandState]] = {}

    @classmethod
    def is_brand_connected(cls, brand_id: BrandIdEnum) -> bool:
        """Retrieve auth status for the given brand ID."""
        state = cls._brand_states.get(brand_id)
        return state.is_connected if state else False

    @classmethod
    def init_brand_state(cls, brand_id: BrandIdEnum, browser_profile_id: str):
        """Create a new brand state."""
        cls._brand_states[brand_id] = BrandState(
            browser_profile_id=browser_profile_id, is_connected=False
        )

    @classmethod
    def update_brand_state(cls, brand_id: BrandIdEnum, *, is_connected: bool):
        """Store browser profile ID for the given brand ID."""
        if brand_id not in cls._brand_states:
            raise ValueError(f"Brand {brand_id} not found in store")
        cls._brand_states[brand_id].is_connected = is_connected

    @classmethod
    def get_browser_profile_id(cls, brand_id: BrandIdEnum) -> str | None:
        """Retrieve browser profile ID for the given brand ID."""
        state = cls._brand_states.get(brand_id)
        return state.browser_profile_id if state else None
