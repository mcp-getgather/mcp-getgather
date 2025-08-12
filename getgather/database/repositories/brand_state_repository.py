from typing import Self

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.database.connection import execute_query, fetch_one
from getgather.database.models import DBModel


class BrandState(DBModel):
    """Brand state record model."""

    brand_id: str
    name: str
    browser_profile_id: str | None
    is_connected: bool = False
    enabled: bool = True
    table_name = "brand_states"

    @classmethod
    def get_by_brand_id(cls, brand_id: BrandIdEnum) -> Self | None:
        """Get a brand state by its brand ID."""
        query = "SELECT * FROM brand_states WHERE brand_id = ?"
        if row := fetch_one(query, (brand_id,)):
            return cls.model_validate(row)
        return None

    @classmethod
    def update_is_connected(cls, brand_id: BrandIdEnum, is_connected: bool) -> None:
        """Update the is_connected status for a brand."""
        query = """
            UPDATE brand_states 
            SET is_connected = ?
            WHERE brand_id = ?
        """
        execute_query(query, (is_connected, BrandIdEnum(brand_id)))

    @classmethod
    def is_brand_connected(cls, brand_id: BrandIdEnum) -> bool:
        """Check if a brand is connected."""
        state = cls.get_by_brand_id(BrandIdEnum(brand_id))
        return state.is_connected if state else False

    @classmethod
    def get_browser_profile_id(cls, brand_id: BrandIdEnum) -> str | None:
        """Get the browser profile ID for a brand."""
        state = cls.get_by_brand_id(BrandIdEnum(brand_id))
        return state.browser_profile_id if state else None

    @classmethod
    def update_enabled(cls, brand_id: BrandIdEnum, enabled: bool) -> None:
        """Update the status for a brand."""
        query = """
            UPDATE brand_states 
            SET enabled = ?
            WHERE brand_id = ?
        """
        execute_query(query, (enabled, BrandIdEnum(brand_id)))

    @classmethod
    def update_browser_profile_id(cls, brand_id: BrandIdEnum, browser_profile_id: str) -> None:
        """Update the browser profile ID for a brand."""
        query = """
            UPDATE brand_states 
            SET browser_profile_id = ?
            WHERE brand_id = ?
        """
        execute_query(query, (browser_profile_id, BrandIdEnum(brand_id)))
