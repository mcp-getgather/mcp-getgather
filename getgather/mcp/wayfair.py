from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

wayfair_mcp = GatherMCP(brand_id="wayfair", name="Wayfair MCP")


# TODO: delete this tool by changing the client to use get_order_history tool
@wayfair_mcp.tool
async def dpage_get_order_history(page_number: int = 1) -> dict[str, Any]:
    """Get order history of wayfair."""
    return await dpage_mcp_tool(
        f"https://www.wayfair.com/session/secure/account/order_search.php?page={page_number}",
        "wayfair_order_history",
    )


@wayfair_mcp.tool
async def get_order_history(page_number: int = 1) -> dict[str, Any]:
    """Get order history of wayfair."""
    return await dpage_mcp_tool(
        f"https://www.wayfair.com/session/secure/account/order_search.php?page={page_number}",
        "wayfair_order_history",
    )


@wayfair_mcp.tool
async def get_order_history_details(order_id: str) -> dict[str, Any]:
    """Get order history details of wayfair."""
    return await dpage_mcp_tool(
        f"https://www.wayfair.com/v/account/order/details?order_id={order_id}",
        "wayfair_order_history_details",
    )
