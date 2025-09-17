import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

thriftbooks_mcp = BrandMCPBase(brand_id="thriftbooks", name="Thriftbooks MCP")


@thriftbooks_mcp.tool(tags={"private"})
async def get_feed() -> dict[str, Any]:
    """Get order history of thriftbooks."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    order_summary = await run_distillation_loop(
        "https://www.thriftbooks.com/account/ordersummary/",
        patterns,
        browser_profile=browser_profile,
    )
    return {"order_summary": order_summary}
