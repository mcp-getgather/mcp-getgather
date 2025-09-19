import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

ashley_mcp = BrandMCPBase(brand_id="ashley", name="Ashley MCP")


@ashley_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from Ashley."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    orders = await run_distillation_loop(
        "https://www.ashleyfurniture.com/orders", patterns, browser_profile=browser_profile
    )
    return {"orders": orders}
