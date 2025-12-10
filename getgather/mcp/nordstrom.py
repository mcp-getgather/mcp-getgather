import json
from typing import Any, cast

import zendriver as zd

from getgather.logs import logger
from getgather.mcp.dpage import zen_dpage_with_action
from getgather.mcp.registry import GatherMCP
from getgather.zen_distill import page_query_selector

nordstrom_mcp = GatherMCP(brand_id="nordstrom", name="Nordstrom MCP")


async def _parse_response_body(body: str) -> dict[str, Any]:
    """Parse response body as JSON, handling base64 encoding if needed."""
    try:
        logger.info("Parsing JSON from response body...")
        parsed: Any = json.loads(body)
        logger.info(f"Successfully parsed JSON. Type: {type(parsed).__name__}")

        if isinstance(parsed, dict):
            orders_dict = cast(dict[str, Any], parsed)
            keys: list[str] = list(orders_dict.keys())
            logger.info(f"Response keys: {keys}")
            if "orders" not in orders_dict:
                logger.warning(f"'orders' key not found in response. Available keys: {keys}")
            else:
                orders_list: Any = orders_dict.get("orders", [])
                orders_count: int | str
                if isinstance(orders_list, list):
                    orders_count = len(cast(list[Any], orders_list))
                else:
                    orders_count = "N/A"
                logger.info(f"Found 'orders' key with {orders_count} items")
            return orders_dict
        else:
            logger.info(f"Response is not a dict, it's a {type(parsed).__name__}")
            return {"orders": []}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.info(f"Response body preview (first 500 chars): {body[:500] if body else 'None'}")
        return {"orders": []}


async def get_order_details_with_retry(
    tab: zd.Tab, page_number: int = 1, max_retries: int = 3
) -> dict[str, Any]:
    """Get the details of an order from Nordstrom with retry logic"""
    logger.info(
        f"Starting get_order_details_with_retry (page_number={page_number}, max_retries={max_retries})"
    )

    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt}/{max_retries}")
        try:
            await tab.get("https://www.nordstrom.com/my-account")
            select_element = await page_query_selector(tab, "div > label > select", 30_000)

            orders = None
            if select_element:
                async with tab.expect_response(".*/orders.*") as resp:
                    logger.info("Response listener active. Triggering select_option('all')...")
                    await select_element.select_option(value="all")
                    logger.info("select_option triggered. Waiting for API response...")

                    response_event = await resp.value
                    logger.info(
                        f"Received response: {response_event.response.status} {response_event.response.url}"
                    )

                    body, _ = await resp.response_body
                    orders = await _parse_response_body(body)
            else:
                logger.warning("Select element not found. Skipping dropdown selection.")

            if page_number > 1:
                logger.info(f"Looking for pagination link: ul li a[href='?page={page_number}']")
                pagination_link = await tab.select(
                    f"ul li a[href='?page={page_number}']", timeout=5
                )
                if not pagination_link:
                    logger.warning(
                        f"Pagination link for page {page_number} not found. Returning empty orders."
                    )
                    return {"orders": []}

                logger.info(
                    "Setting up response listener for pagination API response containing '/orders'..."
                )
                async with tab.expect_response(".*/orders.*") as resp:
                    await pagination_link.click()
                    logger.info("Pagination link clicked. Waiting for API response...")

                    response_event = await resp.value
                    logger.info(f"Received pagination response: {response_event.response.status}")
                    logger.info(f"Response URL: {response_event.response.url}")

                    body, _ = await resp.response_body
                    logger.info(f"Pagination response body fetched")
                    orders = await _parse_response_body(body)
            else:
                logger.info("Page 1 - no pagination needed")

            result = orders or {"orders": []}
            orders_count = (
                len(result.get("orders", [])) if isinstance(result.get("orders"), list) else 0
            )
            logger.info(f"Successfully retrieved orders. Returning {orders_count} orders.")
            return result

        except Exception as e:
            logger.error(f"Attempt {attempt}/{max_retries} failed: {e}")

            if attempt == max_retries:
                logger.error(
                    f" Max retries ({max_retries}) reached for getting order details for page {page_number}"
                )
                raise Exception(
                    f"Max retries reached for getting order details for page {page_number}"
                )
            else:
                logger.info(f"Waiting before retry {attempt + 1}...")

    raise Exception(f"Max retries reached for getting order details for page {page_number}")


# Currently, no way for us to get the order detail based on the order id since
# the order id needs to be paired with lookupKey which is not available in the dom / ui
# so we need to listen specifically to the order details api call


@nordstrom_mcp.tool
async def get_order_history(page_number: int = 1) -> dict[str, Any]:
    """Get the details of an order from Nordstrom"""

    async def get_order_details_action(tab: zd.Tab, _) -> dict[str, Any]:
        """Get the details of an order from Nordstrom"""
        logger.info("🔧 Executing get_order_details_action...")
        result: dict[str, Any] = await get_order_details_with_retry(tab, page_number)
        result_keys: list[str] = list(result.keys())
        logger.info(f"✅ get_order_details_action completed. Result keys: {result_keys}")
        return result

    return await zen_dpage_with_action(
        "https://www.nordstrom.com/my-account",
        get_order_details_action,
    )
