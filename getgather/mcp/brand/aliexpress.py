import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

aliexpress_mcp = BrandMCPBase(brand_id="aliexpress", name="AliExpress MCP")


@aliexpress_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from AliExpress."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    _terminated, distilled, converted = await run_distillation_loop(
        "https://www.aliexpress.com/p/order/index.html", patterns, browser_profile=browser_profile
    )
    orders = converted if converted else distilled
    return {"orders": orders}
