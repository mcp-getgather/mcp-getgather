from typing import Any

from patchright.async_api import Page

from getgather.actions import handle_network_extraction
from getgather.mcp.dpage import dpage_with_action
from getgather.mcp.registry import GatherMCP

alfagift_mcp = GatherMCP(brand_id="alfagift", name="Alfagift MCP")

@alfagift_mcp.tool
async def get_cart() -> dict[str, Any]:
    """Get cart alfagift."""

    async def action(page: Page, _) -> dict[str, Any]:
        await page.goto(f"https://alfagift.id/cart")
        data = await handle_network_extraction(page, "active-cart-by-memberId")
        return {"alfagift_cart": data["data"]["listCartDetail"]}

    return await dpage_with_action(
        "https://alfagift.id",
        action,
    )

@alfagift_mcp.tool
async def get_order_done() -> dict[str, Any]:
    """Get order done alfagift."""

    async def action(page: Page, _) -> dict[str, Any]:
        await page.goto(f"https://alfagift.id/order-done")
        data = await handle_network_extraction(page, "order-ereceipt-service/list/complete")
        return {"alfagift_order_done": data["data"]}    
        logger.info("Extracted cart data from network response. with data: {data}")
        return {"alfagift_cart": data["data"]["listCartDetail"]}

    return await dpage_with_action(
        "https://alfagift.id",
        action,
    )