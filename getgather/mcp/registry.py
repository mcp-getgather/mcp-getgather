from typing import ClassVar

from fastmcp import Context, FastMCP

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger


class BrandMCPBase(FastMCP[Context]):
    registry: ClassVar[dict[BrandIdEnum, "BrandMCPBase"]] = {}

    def __init__(self, *, brand_id: str, name: str) -> None:
        super().__init__(name=name)
        self.brand_id = BrandIdEnum(brand_id)
        BrandMCPBase.registry[self.brand_id] = self
        logger.debug(f"Registered MCP with brand_id '{brand_id}' and name '{name}'")


class GatherMCP(FastMCP[Context]):
    registry: ClassVar[dict[str, "GatherMCP"]] = {}

    def __init__(self, *, brand_id: str, name: str) -> None:
        super().__init__(name=name)
        self.brand_id = brand_id
        GatherMCP.registry[self.brand_id] = self
        logger.debug(f"Registered GatherMCP with brand_id '{brand_id}' and name '{name}'")
