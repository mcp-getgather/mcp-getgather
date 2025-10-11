import os
from typing import Any

from getgather.browser.session import BrowserSession
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_session, with_brand_browser_session

agoda_mcp = BrandMCPBase(brand_id="agoda", name="Agoda MCP")


@agoda_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_complete_bookings(*, browser_session: BrowserSession | None = None) -> dict[str, Any]:
    """Get complete bookings of agoda."""
    browser_session = browser_session or get_mcp_browser_session()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    complete_bookings = await run_distillation_loop(
        "https://www.agoda.com/account/bookings.html?sort=BookingStartDate&state=Completed&page=1",
        patterns,
        browser_session=browser_session,
    )
    return {"complete_bookings": complete_bookings}
