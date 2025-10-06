from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import BrandMCPBase

containerstore_mcp = BrandMCPBase(
    brand_id="containerstore", name="Container Store MCP")


@containerstore_mcp.tool
async def get_cart() -> dict[str, Any]:
    """Get cart of containerstore."""
    return await dpage_mcp_tool("https://www.containerstore.com/cart/list.htm", "containerstore_cart")
