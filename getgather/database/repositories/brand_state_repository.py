from typing import TypedDict, cast

from getgather.database.connection import execute_insert, execute_query, fetch_all, fetch_one


class BrandState(TypedDict):
    """Type definition for a brand state record."""

    brand_id: str
    browser_profile_id: str
    is_connected: bool
    created_at: str  # SQLite timestamp as string


def create(brand_id: str, browser_profile_id: str, is_connected: bool) -> int:
    """Create a new brand state."""
    query = """
        INSERT INTO brand_states (brand_id, browser_profile_id, is_connected)
        VALUES (?, ?, ?)
    """
    return execute_insert(query, (brand_id, browser_profile_id, is_connected))


def get_by_id(brand_id: str) -> BrandState | None:
    """Get a session by its ID."""
    query = "SELECT * FROM brand_states WHERE brand_id = ?"
    brand_state = fetch_one(query, (brand_id,))
    if brand_state:
        return cast(BrandState, brand_state)
    return None


def get_all() -> list[BrandState]:
    """Get all brand states."""
    query = "SELECT * FROM brand_states"
    brand_states = fetch_all(query)

    return [cast(BrandState, brand_state) for brand_state in brand_states]


def update_is_connected(brand_id: str, is_connected: bool) -> None:
    """Update the is_connected for a brand."""
    query = """
        UPDATE brand_states 
        SET is_connected = ?
        WHERE brand_id = ?
    """
    execute_query(query, (is_connected, brand_id))


def delete(brand_id: str) -> None:
    """Delete a brand state."""
    query = "DELETE FROM brand_states WHERE brand_id = ?"
    execute_query(query, (brand_id,))
