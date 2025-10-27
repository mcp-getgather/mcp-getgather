from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

lululemon_mcp = GatherMCP(brand_id="lululemon", name="Lululemon MCP")


@lululemon_mcp.tool
async def get_orders() -> dict[str, Any]:
    """Get orders from Lululemon."""
    return await dpage_mcp_tool(
        "https://shop.lululemon.com/account/purchase-history", "lululemon_orders"
    )
