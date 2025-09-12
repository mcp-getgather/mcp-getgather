import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.profile_manager import global_profile_manager

zillow_mcp = BrandMCPBase(brand_id="zillow", name="Zillow MCP")


@zillow_mcp.tool(tags={"private"})
async def get_favorites() -> dict[str, Any]:
    """Get favorites of zillow."""
    browser_profile = global_profile_manager.get_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    favorites = await run_distillation_loop(
        "https://www.zillow.com/myzillow/favorites", patterns, browser_profile=browser_profile
    )
    return {"favorites": favorites}
