from getgather.database.models import DBModel


class BrandState(DBModel):
    """Brand state record model."""

    browser_profile_id: str
    is_connected: bool

    table_name = "brand_states"
