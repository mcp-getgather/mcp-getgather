from fastmcp import Context, FastMCP
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)


class BrandMCPBase(FastMCP[Context]):
    registry: dict[str, FastMCP[Context]] = {}

    def __init__(self, *, prefix: str, name: str) -> None:
        super().__init__(name=name)
        self._prefix = prefix
        BrandMCPBase.registry[prefix] = self
        logger.debug(f"Registered MCP with prefix '{prefix}' and name '{name}'")
