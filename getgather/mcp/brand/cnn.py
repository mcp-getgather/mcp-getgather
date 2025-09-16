import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, get_mcp_browser_profile

cnn_mcp = BrandMCPBase(brand_id="cnn", name="CNN MCP")


@cnn_mcp.tool(tags={"private"})
async def get_newsletter() -> dict[str, Any]:
    """Get newsletter of cnn."""

    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    newsletter = await run_distillation_loop(
        "https://www.cnn.com/newsletters", patterns, browser_profile=browser_profile
    )
    return {"newsletter": newsletter}
