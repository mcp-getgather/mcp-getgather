import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

sephora_mcp = BrandMCPBase(brand_id="sephora", name="Sephora MCP")


@sephora_mcp.tool(tags={"private"})
async def get_order_history() -> dict[str, Any]:
    """Get order history of sephora."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    order_history = await run_distillation_loop(
        "https://www.sephora.com/purchase-history", patterns, browser_profile=browser_profile
    )
    return {"order_history": order_history}
