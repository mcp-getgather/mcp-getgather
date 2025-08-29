from typing import ClassVar

from fastmcp import Context, FastMCP

from getgather.logs import logger


class BrandMCPBase(FastMCP[Context]):
    registry: ClassVar[dict[str, "BrandMCPBase"]] = {}

    def __init__(self, *, brand_id: str, name: str) -> None:
        super().__init__(name=name)
        self.brand_id: str = brand_id
        BrandMCPBase.registry[self.brand_id] = self
        logger.debug(f"Registered MCP with brand_id '{brand_id}' and name '{name}'")
