from typing import Any

from patchright.async_api import Page

from getgather.actions import handle_network_extraction
from getgather.logs import logger
from getgather.mcp.dpage import dpage_with_action
from getgather.mcp.registry import GatherMCP

nordstrom_mcp = GatherMCP(brand_id="nordstrom", name="Nordstrom MCP")


async def get_order_details_with_retry(
    page: Page, page_number: int = 1, max_retries: int = 3
) -> dict[str, Any]:
    """Get the details of an order from Nordstrom with retry logic"""
    for attempt in range(1, max_retries + 1):
        try:
            await page.goto("https://www.nordstrom.com/my-account", wait_until="commit")
            await page.wait_for_selector("div > label > select")
            await page.select_option("div > label > select", value="all")
            orders = await handle_network_extraction(page, "/orders")

            if page_number > 1:
                locator = page.locator(f"ul li a[href='?page={page_number}']")
                count = await locator.count()
                if count == 0:
                    return {"orders": []}
                await page.click(f"ul li a[href='?page={page_number}']")
                orders = await handle_network_extraction(page, "/orders")

            return orders

        except Exception:
            if attempt == max_retries:
                logger.error(
                    f"Max retries reached for getting order details for page {page_number}"
                )
                raise Exception(
                    f"Max retries reached for getting order details for page {page_number}"
                )

    raise Exception(f"Max retries reached for getting order details for page {page_number}")


# Currently, no way for us to get the order detail based on the order id since
# the order id needs to be paired with lookupKey which is not available in the dom / ui
# so we need to listen specifically to the order details api call


@nordstrom_mcp.tool
async def get_order_history(page_number: int = 1) -> dict[str, Any]:
    """Get the details of an order from Nordstrom"""

    async def get_order_details_action(page: Page, _) -> dict[str, Any]:
        """Get the details of an order from Nordstrom"""
        return await get_order_details_with_retry(page, page_number)

    return await dpage_with_action(
        "https://www.nordstrom.com/my-account",
        get_order_details_action,
    )
