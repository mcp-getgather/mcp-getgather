from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

nordstrom_mcp = GatherMCP(brand_id="nordstrom", name="Nordstrom MCP")


@nordstrom_mcp.tool
async def get_orders(ctx: Context) -> dict[str, Any]:
    """Get the list of orders from Nordstrom"""

    return await dpage_mcp_tool(
        "https://www.nordstrom.com/my-account?count=100&page=1&range=all", "nordstrom_orders"
    )
