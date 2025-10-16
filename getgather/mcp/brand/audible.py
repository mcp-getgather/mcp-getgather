import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

audible_mcp = BrandMCPBase(brand_id="audible", name="Audible MCP")


@audible_mcp.tool(tags={"private"})
async def get_book_list() -> dict[str, Any]:
    """Get book list from Audible.com."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    book_list = await run_distillation_loop(
        "https://www.audible.com/library/titles",
        patterns,
        browser_profile=browser_profile,
    )
    return {"book_list": book_list}
