from typing import Any

from fastmcp import Context

from getgather.browser.agent import run_agent
from getgather.logs import logger
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, start_browser_session

doordash_mcp = BrandMCPBase(brand_id="doordash", name="Doordash MCP")


@doordash_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from Doordash.com."""
    return await extract(brand_id=doordash_mcp.brand_id)


@doordash_mcp.tool(tags={"private"})
async def reorder_previous_order(ctx: Context, restaurant_name: str) -> dict[str, Any]:
    """Reorder the previous order on Doordash.com from the given restaurant."""
    browser_session = None
    try:
        browser_session = await start_browser_session(doordash_mcp.brand_id)
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
        logger.info(f"Running agent with task: {task}")
        await run_agent(ctx, browser_session.context, task)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if browser_session:
            await browser_session.stop()


@doordash_mcp.tool(tags={"private"})
async def checkout_order_status(ctx: Context) -> dict[str, Any]:
    """Checkout the status of the in progress order on Doordash.com."""
    browser_session = None
    try:
        browser_session = await start_browser_session(doordash_mcp.brand_id)
        task = (
            "Following the instructions below to"
            " checkout the status of the in progress order on Doordash:"
            " 1. Go to Orders page at https://www.doordash.com/orders."
            " 2. Find the most recent in progress order on the top of the page,"
            "   and click the 'View Order' button, "
            "   then you will be redirected to the page of the order."
            " 3. Analyze the order status and return the status in a short sentence."
        )
        logger.info(f"Running agent with task: {task}")
        await run_agent(ctx, browser_session.context, task)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if browser_session:
            await browser_session.stop()
