import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

americanairlines_mcp = BrandMCPBase(brand_id="americanairlines", name="American Airlines MCP")


@americanairlines_mcp.tool(tags={"private"})
async def get_upcoming_flights() -> dict[str, Any]:
    """Get upcoming flights of americanairlines."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    upcoming_flights = await run_distillation_loop(
        "https://www.aa.com/aadvantage-program/profile/account-summary",
        patterns,
        browser_profile=browser_profile,
    )
    return {"upcoming_flights": upcoming_flights}


@americanairlines_mcp.tool(tags={"private"})
async def get_past_flights() -> dict[str, Any]:
    """Get past flights of americanairlines."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    past_flights = await run_distillation_loop(
        "https://www.aa.com/aadvantage-program/profile/trip-history",
        patterns,
        browser_profile=browser_profile,
    )
    return {"past_flights": past_flights}
