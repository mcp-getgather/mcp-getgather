import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

jetblue_mcp = BrandMCPBase(brand_id="jetblue", name="JetBlue MCP")


@jetblue_mcp.tool(tags={"private"})
async def get_profile() -> dict[str, Any]:
    """Get profile of jetblue."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    profile = await run_distillation_loop(
        "https://www.jetblue.com/",
        patterns,
        browser_profile=browser_profile,
    )
    return {"profile": profile}
