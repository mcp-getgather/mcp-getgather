from getgather.connectors.spec_loader import BrandIdEnum
from getgather.database.models import DBModel


class BrandState(DBModel):
    """Brand state record model."""

    browser_profile_id: str
    is_connected: bool

    table_name = "brand_states"

    @classmethod
    def update_is_connected(cls, id: BrandIdEnum, is_connected: bool) -> None:
        cls.update(
            id=id,
            data={"is_connected": is_connected},
        )
