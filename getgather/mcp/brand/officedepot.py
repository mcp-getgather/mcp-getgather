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
    orders = await run_distillation_loop(
        "https://www.officedepot.com/orderhistory/orderHistoryList.do",
        patterns,
        browser_profile=browser_profile,
    )
    return {"orders": orders}
