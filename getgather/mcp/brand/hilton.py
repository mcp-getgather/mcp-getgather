import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

hilton_mcp = BrandMCPBase(brand_id="hilton", name="Hilton MCP")


@hilton_mcp.tool(tags={"private"})
async def get_activities() -> dict[str, Any]:
    """Get activities from Hilton."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    activities, _ = await run_distillation_loop(
        "https://www.hilton.com/en/hilton-honors/guest/activity/",
        patterns,
        browser_profile=browser_profile,
    )
    return {"activities": activities}
