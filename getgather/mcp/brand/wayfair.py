import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

wayfair_mcp = BrandMCPBase(brand_id="wayfair", name="Wayfair MCP")


@wayfair_mcp.tool(tags={"private"})
async def get_order_history() -> dict[str, Any]:
    """Get order history of wayfair."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    purchase_history = await run_distillation_loop(
        "https://www.wayfair.com/session/secure/account/order_search.php",
        patterns,
        browser_profile=browser_profile,
    )
    return {"purchase_history": purchase_history}
