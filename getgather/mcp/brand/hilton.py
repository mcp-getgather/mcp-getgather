import os
from typing import Any

from getgather.browser.session import BrowserSession
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_session, with_brand_browser_session

hilton_mcp = BrandMCPBase(brand_id="hilton", name="Hilton MCP")


@hilton_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_activities(*, browser_session: BrowserSession | None = None) -> dict[str, Any]:
    """Get activities from Hilton."""
    browser_session = browser_session or get_mcp_browser_session()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    activities = await run_distillation_loop(
        "https://www.hilton.com/en/hilton-honors/guest/activity/",
        patterns,
        browser_session=browser_session,
    )
    return {"activities": activities}
