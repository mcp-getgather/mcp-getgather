import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

nike_mcp = BrandMCPBase(brand_id="nike", name="Nike MCP")


@nike_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get online orders of nike."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    online_orders = await run_distillation_loop(
        "https://www.nike.com/orders",
        patterns,
        browser_profile=browser_profile,
    )
    return {"online_orders": online_orders}
