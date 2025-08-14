from typing import Any

from fastmcp import Context

from getgather.browser.agent import run_agent
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, start_browser_session

doordash_mcp = BrandMCPBase(prefix="doordash", name="Doordash MCP")


@doordash_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from Doordash.com."""
    return await extract(BrandIdEnum("doordash"))


@doordash_mcp.tool(tags={"private"})
async def reorder_last_order(ctx: Context) -> dict[str, Any]:
    """Reorder the last order on Doordash.com."""
    browser_session = None
    try:
        browser_session = await start_browser_session(BrandIdEnum("doordash"))
        task = (
            f"Following the instructions below to reorder the last order on Doordash:"
            " 1. go to Orders page at https://www.doordash.com/orders."
            " 2. find the top order on the page and click the 'Reorder' button,"
            "   then you will be redirected to the page of the restaurant."
            " 3. click the red cart button on the top right corner of the page to open the cart."
            " 4. Continue the process and place the order at the end."
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
