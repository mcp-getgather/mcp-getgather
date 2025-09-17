import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

alltrails_mcp = BrandMCPBase(brand_id="alltrails", name="Alltrails MCP")


@alltrails_mcp.tool(tags={"private"})
async def get_feed() -> dict[str, Any]:
    """Get feed of alltrails."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "alltrails/*.html")
    patterns = load_distillation_patterns(path)
    feed = await run_distillation_loop(
        "https://www.alltrails.com/my/profile/",
        patterns,
        browser_profile=browser_profile,
    )
    return {"feed": feed}
