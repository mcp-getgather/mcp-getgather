from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import zen_dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

harrys_mcp = GatherMCP(brand_id="harrys", name="Harrys MCP")


@harrys_mcp.tool
async def get_orders(ctx: Context) -> dict[str, Any]:
    """Get the list of orders from Harrys"""

    return await zen_dpage_mcp_tool("https://www.harrys.com/en/profile/orders", "harrys_orders")
