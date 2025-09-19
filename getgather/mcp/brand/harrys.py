import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

harrys_mcp = BrandMCPBase(brand_id="harrys", name="Harrys MCP")


@harrys_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from Harrys."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    orders = await run_distillation_loop(
        "https://www.harrys.com/en/profile/orders", patterns, browser_profile=browser_profile
    )
    return {"orders": orders}
