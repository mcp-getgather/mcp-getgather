from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

ubereats_mcp = BrandMCPBase(brand_id="ubereats", name="UberEats MCP")


@ubereats_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from UberEats.com."""
    return await extract()
