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


@wayfair_mcp.tool
async def get_cart() -> dict[str, Any]:
    """Get order history details of wayfair."""
    return await dpage_mcp_tool(
        "https://www.wayfair.com/v/checkout/basket/show", "wayfair_cart", timeout=10
    )


@wayfair_mcp.tool
async def get_whishlists() -> dict[str, Any]:
    """Get whishlists of wayfair."""
    return await dpage_mcp_tool("https://www.wayfair.com/lists", "wayfair_whishlists", timeout=10)


@wayfair_mcp.tool
async def get_whishlist_details(url: str) -> dict[str, Any]:
    """Get whishlist details of wayfair."""
    return await dpage_mcp_tool(
        f"https://www.wayfair.com{url}", "wayfair_whishlist_details", timeout=10
    )
