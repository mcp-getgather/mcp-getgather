import os
from typing import Any

from getgather.browser.session import BrowserSession
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_session, with_brand_browser_session

booking_mcp = BrandMCPBase(brand_id="booking", name="Booking MCP")


@booking_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_past_trips(*, browser_session: BrowserSession | None = None) -> dict[str, Any]:
    """Get past trip of booking.com."""
    browser_session = browser_session or get_mcp_browser_session()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    past_trips = await run_distillation_loop(
        "https://secure.booking.com/mytrips.html",
        patterns,
        browser_session=browser_session,
    )
    return {"past_trips": past_trips}
