from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

costco_mcp = GatherMCP(brand_id="costco", name="Costco MCP")


@costco_mcp.tool
async def get_online_orders(ctx: Context) -> dict[str, Any]:
    """Get online orders from Costco.com."""
    return await dpage_mcp_tool(
        initial_url="https://www.costco.com/myaccount/", result_key="orders"
    )
