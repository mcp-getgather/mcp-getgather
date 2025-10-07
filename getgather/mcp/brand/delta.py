import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

delta_mcp = BrandMCPBase(brand_id="delta", name="Delta MCP")


@delta_mcp.tool(tags={"private"})
async def get_trips() -> dict[str, Any]:
    """Get trips of delta."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    profile = await run_distillation_loop(
        "https://www.delta.com/my-trips/upcoming-trips",
        patterns,
        browser_profile=browser_profile,
    )
    return {"profile": profile}
