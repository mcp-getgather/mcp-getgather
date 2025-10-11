import os
from typing import Any

from getgather.browser.session import BrowserSession
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_session, with_brand_browser_session

officedepot_mcp = BrandMCPBase(brand_id="officedepot", name="Office Depot MCP")


@officedepot_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_order_history(*, browser_session: BrowserSession | None = None) -> dict[str, Any]:
    """Get order history of officedepot."""
    browser_session = browser_session or get_mcp_browser_session()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    purchase_history = await run_distillation_loop(
        # `https://www.officedepot.com/orderhistory/orderHistoryListSet.do` only shows the last 3 months of orders
        "https://www.officedepot.com/orderhistory/orderHistoryListSet.do?ordersInMonths=0&orderType=ALL&orderStatus=A",
        patterns,
        browser_session=browser_session,
    )

    return {"purchase_history": purchase_history}


@officedepot_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_order_history_details(
    order_number: str,
    *,
    browser_session: BrowserSession | None = None,
) -> dict[str, Any]:
    """Get detailed order history for a specific Office Depot order."""
    browser_session = browser_session or get_mcp_browser_session()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    purchase_history_details = await run_distillation_loop(
        f"https://www.officedepot.com/orderhistory/orderHistoryDetail.do?id={order_number}",
        patterns,
        browser_session=browser_session,
    )

    if purchase_history_details and isinstance(purchase_history_details, list):
        for item in purchase_history_details:
            item["order_number"] = order_number

    return {"purchase_history_details": purchase_history_details}
