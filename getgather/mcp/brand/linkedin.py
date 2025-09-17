import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

linkedin_mcp = BrandMCPBase(brand_id="linkedin", name="Linkedin MCP")


@linkedin_mcp.tool(tags={"private"})
async def get_feed() -> dict[str, Any]:
    """Get feed of Linkedin."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "linkedin/*.html")
    patterns = load_distillation_patterns(path)
    feed = await run_distillation_loop(
        "https://www.linkedin.com/feed/",
        patterns,
        browser_profile=browser_profile,
    )
    return {"feed": feed}
