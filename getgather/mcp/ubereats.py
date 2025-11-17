import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import GatherMCP
from getgather.mcp.shared import get_mcp_browser_profile

ubereats_mcp = GatherMCP(brand_id="ubereats", name="UberEats MCP")


async def get_orders() -> dict[str, Any]:
    """Get orders from UberEats.com."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    _terminated, distilled, converted = await run_distillation_loop(
        "https://www.ubereats.com/orders",
        patterns,
        browser_profile=browser_profile,
    )
    orders = converted if converted else distilled
    return {"orders": orders}
