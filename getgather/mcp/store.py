from getgather.connectors.spec_loader import BrandIdEnum
from getgather.database.repositories import brand_state_repository


class BrandConnectionStore:
    """
    Store brands connection statuses.
    This will soon be replaced by a database.
    """

    @classmethod
    def is_brand_connected(cls, brand_id: BrandIdEnum) -> bool:
        """Retrieve auth status for the given brand ID."""
        state = brand_state_repository.get_by_id(str(brand_id))
        return state["is_connected"] if state else False

    @classmethod
    def init_brand_state(cls, brand_id: BrandIdEnum, browser_profile_id: str):
        """Create a new brand state."""
        brand_state_repository.create(str(brand_id), browser_profile_id, False)

    @classmethod
    def update_brand_state(cls, brand_id: BrandIdEnum, *, is_connected: bool):
        """Store browser profile ID for the given brand ID."""
        brand_state_repository.update_is_connected(str(brand_id), is_connected)

    @classmethod
    def get_browser_profile_id(cls, brand_id: BrandIdEnum) -> str | None:
        """Retrieve browser profile ID for the given brand ID."""
        state = brand_state_repository.get_by_id(str(brand_id))
        return state["browser_profile_id"] if state else None
