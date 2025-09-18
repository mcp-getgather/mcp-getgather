import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

agoda_mcp = BrandMCPBase(brand_id="agoda", name="Agoda MCP")


@agoda_mcp.tool(tags={"private"})
async def get_complete_bookings() -> dict[str, Any]:
    """Get complete bookings of agoda."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    complete_bookings = await run_distillation_loop(
        "https://www.agoda.com/account/bookings.html?sort=BookingStartDate&state=Completed&page=1",
        patterns,
        browser_profile=browser_profile,
    )
    return {"complete_bookings": complete_bookings}
