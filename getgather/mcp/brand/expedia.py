import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

expedia_mcp = BrandMCPBase(brand_id="expedia", name="Expedia MCP")


@expedia_mcp.tool(tags={"private"})
async def get_past_trips() -> dict[str, Any]:
    """Get past trips from Expedia."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    past_trips = await run_distillation_loop(
        "https://www.expedia.com/trips/list/3 ", patterns, browser_profile=browser_profile
    )
    return {"past_trips": past_trips}
