from typing import ClassVar

from fastmcp import Context, FastMCP

from getgather.logs import logger


class GatherMCP(FastMCP[Context]):
    registry: ClassVar[dict[str, "GatherMCP"]] = {}

    def __init__(self, *, brand_id: str, name: str) -> None:
        super().__init__(name=name)
        self.brand_id = brand_id
        GatherMCP.registry[self.brand_id] = self
        logger.debug(f"Registered GatherMCP with brand_id '{brand_id}' and name '{name}'")
