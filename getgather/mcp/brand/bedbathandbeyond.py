import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

bedbathandbeyond_mcp = BrandMCPBase(brand_id="bedbathandbeyond", name="Bed Bath and Beyond MCP")


@bedbathandbeyond_mcp.tool(tags={"private"})
async def get_favorites() -> dict[str, Any]:
    """Get favorites of bedbathandbeyond."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    favorites = await run_distillation_loop(
        "https://www.bedbathandbeyond.com/profile/me/lists",
        patterns,
        browser_profile=browser_profile,
    )
    return {"favorites": favorites}
