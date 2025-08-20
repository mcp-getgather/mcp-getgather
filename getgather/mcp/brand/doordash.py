from typing import Any

from fastmcp import Context

from getgather.mcp.agent import run_agent_for_brand
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

doordash_mcp = BrandMCPBase(brand_id="doordash", name="Doordash MCP")


@doordash_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from Doordash.com."""
    return await extract()


@doordash_mcp.tool(tags={"private"})
async def reorder_previous_order(ctx: Context, restaurant_name: str) -> dict[str, Any]:
    """Reorder the previous order on Doordash.com from the given restaurant."""
    task = (
        "Following the instructions below to reorder the last order on Doordash:"
        " 1. Go to Orders page at https://www.doordash.com/orders."
        f" 2. Find the most recent order from {restaurant_name} on the page,"
        "   and click the 'Reorder' button, "
        "   then you will be redirected to the page of the restaurant."
        " 3. Click the red cart button on the top right corner of the page to open the cart."
        " 4. Continue the process to place the order. "
        "   Make sure choose delivery option and not pickup,"
        "   and the delivery address is the same as the last order."
        " 5. At the end, confirm the order is placed successfully."
    )
    return await run_agent_for_brand(task)


@doordash_mcp.tool(tags={"private"})
async def check_order_status(ctx: Context) -> dict[str, Any]:
    """Check the status of the in progress order on Doordash.com."""
    task = (
        "Following the instructions below to"
        " check the status of the in progress order on Doordash:"
        " 1. Go to Orders page at https://www.doordash.com/orders."
        " 2. Find the most recent in progress order on the top of the page,"
        " 3. Extract the order status including the estinated delivery time if available, and return the result."
        " 4. If there is no in progress order, return 'no in progress order found'."
    )
    return await run_agent_for_brand(task)
