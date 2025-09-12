import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.profile_manager import global_profile_manager
from getgather.mcp.registry import BrandMCPBase

bbc_mcp = BrandMCPBase(brand_id="bbc", name="BBC MCP")


@bbc_mcp.tool(tags={"private"})
async def get_bookmarks() -> dict[str, Any]:
    """Get bookmarks of bbc."""

    browser_profile = global_profile_manager.get_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    extract_result = await run_distillation_loop(
        "https://www.bbc.com/saved", patterns, browser_profile=browser_profile
    )
    return {"extract_result": extract_result}
