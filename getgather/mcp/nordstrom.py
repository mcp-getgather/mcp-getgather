import asyncio
from typing import Any

from fastmcp import Context
from patchright.async_api import Page, Response

from getgather.mcp.dpage import dpage_mcp_tool, dpage_with_action
from getgather.mcp.registry import GatherMCP

nordstrom_mcp = GatherMCP(brand_id="nordstrom", name="Nordstrom MCP")


@nordstrom_mcp.tool
async def get_orders(ctx: Context) -> dict[str, Any]:
    """Get the list of orders from Nordstrom"""

    return await dpage_mcp_tool(
        "https://www.nordstrom.com/my-account?count=100&page=1&range=all", "nordstrom_orders"
    )


# Currently, no way for us to get the order detail based on the order id since
# the order id needs to be paired with lookupKey which is not available in the dom / ui
# so we need to listen specifically to the order details api call
@nordstrom_mcp.tool
async def get_order_history(ctx: Context) -> dict[str, Any]:
    """Get the details of an order from Nordstrom"""

    async def get_order_details_action(page: Page) -> dict[str, Any]:
        """Get the details of an order from Nordstrom"""

        print("Getting order details...")

        result_future: asyncio.Future[dict[str, Any]] = asyncio.Future()

        async def handle_response(response: Response) -> None:
            if (
                response.status == 200
                and "/api/shoppers/" in response.url
                and "/orders" in response.url
            ):
                if not result_future.done():
                    try:
                        data = await response.json()
                        result_future.set_result(data)
                    except Exception as err:
                        result_future.set_exception(err)

        page.on("response", handle_response)

        print("Waiting for response...")

        # Wait for the response
        try:
            orders = await asyncio.wait_for(result_future, timeout=30.0)
            return orders
        finally:
            page.remove_listener("response", handle_response)

    return await dpage_with_action(
        "https://www.nordstrom.com/my-account",
        get_order_details_action,
    )
