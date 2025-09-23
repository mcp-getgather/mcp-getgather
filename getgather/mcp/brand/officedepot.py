import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

officedepot_mcp = BrandMCPBase(brand_id="officedepot", name="Office Depot MCP")


@officedepot_mcp.tool(tags={"private"})
async def get_order_history() -> dict[str, Any]:
    """Get order history of officedepot."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    purchase_history = await run_distillation_loop(
        # `https://www.officedepot.com/orderhistory/orderHistoryListSet.do` only shows the last 3 months of orders
        "https://www.officedepot.com/orderhistory/orderHistoryListSet.do?ordersInMonths=0&orderType=ALL&orderStatus=A",
        patterns,
        browser_profile=browser_profile,
    )

    return {"purchase_history": purchase_history}


@officedepot_mcp.tool(tags={"private"})
async def get_order_history_details(order_number: str) -> dict[str, Any]:
    """Get detailed order history for a specific Office Depot order."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    purchase_history_details = await run_distillation_loop(
        f"https://www.officedepot.com/orderhistory/orderHistoryDetail.do?id={order_number}",
        patterns,
        browser_profile=browser_profile,
    )

    return {"purchase_history_details": purchase_history_details}
