from typing import Any

from patchright.async_api import Page

from getgather.logs import logger
from getgather.mcp.dpage import dpage_with_action
from getgather.mcp.registry import GatherMCP

americanairlines_mcp = GatherMCP(brand_id="americanairlines", name="American Airlines MCP")


@americanairlines_mcp.tool
async def get_upcoming_flights() -> dict[str, Any]:
    """Get upcoming flights of americanairlines."""

    async def action(page: Page) -> dict[str, Any]:
        try:
            async with page.expect_response(
                lambda resp: "loyalty/api/upcoming-trips" in resp.url,
                timeout=15000,
            ) as response_info:
                await page.goto(
                    "https://www.aa.com/aadvantage-program/profile/account-summary",
                    wait_until="commit",
                )

            response = await response_info.value
            data = await response.json()
            return {"americanairlines_upcoming_flights": data}
        except Exception as e:
            logger.error(f"Failed to get upcoming flights: {e}")
            return {"americanairlines_upcoming_flights": []}

    return await dpage_with_action(
        "https://www.aa.com/aadvantage-program/profile/account-summary",
        action,
    )


@americanairlines_mcp.tool
async def get_recent_activity() -> dict[str, Any]:
    """Get recent activity (purchase history) of americanairlines."""

    async def action(page: Page) -> dict[str, Any]:
        try:
            async with page.expect_response(
                lambda resp: "api/loyalty/miles/transaction/orchestrator/memberActivity"
                in resp.url,
                timeout=15000,
            ) as response_info:
                await page.goto(
                    "https://www.aa.com/aadvantage-program/profile/account-summary",
                    wait_until="commit",
                )

            response = await response_info.value
            data = await response.json()
            return {"americanairlines_recent_activity": data}
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return {"americanairlines_recent_activity": []}

    return await dpage_with_action(
        "https://www.aa.com/aadvantage-program/profile/account-summary",
        action,
    )
