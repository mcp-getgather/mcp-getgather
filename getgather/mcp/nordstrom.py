from typing import Any

from patchright.async_api import Page

from getgather.actions import handle_network_extraction
from getgather.mcp.dpage import dpage_with_action
from getgather.mcp.registry import GatherMCP

nordstrom_mcp = GatherMCP(brand_id="nordstrom", name="Nordstrom MCP")

# Currently, no way for us to get the order detail based on the order id since
# the order id needs to be paired with lookupKey which is not available in the dom / ui
# so we need to listen specifically to the order details api call


@nordstrom_mcp.tool
async def get_order_history() -> dict[str, Any]:
    """Get the details of an order from Nordstrom"""

    async def get_order_details_action(page: Page) -> dict[str, Any]:
        """Get the details of an order from Nordstrom"""
        await page.wait_for_selector("div > label > select")
        await page.select_option("div > label > select", value="all")
        orders = await handle_network_extraction(page, "/orders")
        return orders

    return await dpage_with_action(
        "https://www.nordstrom.com/my-account",
        get_order_details_action,
    )
