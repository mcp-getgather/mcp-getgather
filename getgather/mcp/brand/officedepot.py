from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

officedepot_mcp = BrandMCPBase(brand_id="officedepot", name="Office Depot MCP")


@officedepot_mcp.tool(tags={"private"})
async def get_order_history() -> dict[str, Any]:
    """Get order history of officedepot."""
    return await extract()
