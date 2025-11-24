from typing import Any

from patchright.async_api import Page

from getgather.actions import handle_network_extraction
from getgather.logs import logger
from getgather.mcp.dpage import dpage_mcp_tool, dpage_with_action
from getgather.mcp.registry import GatherMCP

garmin_mcp = GatherMCP(brand_id="garmin", name="Garmin MCP")


@garmin_mcp.tool
async def get_activities() -> dict[str, Any]:
    """Get the activity history from a user's account."""

    async def add_activity_ids_action(page: Page, _) -> dict[str, Any]:
        result = await dpage_mcp_tool(
            "https://connect.garmin.com/modern/activities",
            "garmin_activity_history",
        )

        activities = result.get("garmin_activity_history", [])
        logger.info(f"Activities: {activities}")

        for activity in activities:
            activity_url = activity.get("activity_url", "")
            if activity_url:
                parts = activity_url.split("/")
                if len(parts) > 0:
                    activity_id = parts[-1]
                    activity["activity_id"] = activity_id
                    activity["activity_url"] = f"https://connect.garmin.com{activity_url}"
                    logger.info(f"Activity: {activity}")

        return {"garmin_activity_history": activities}

    return await dpage_with_action(
        "https://connect.garmin.com/modern/activities",
        action=add_activity_ids_action,
    )


@garmin_mcp.tool
async def get_activity_stats(activity_id: str) -> dict[str, Any]:
    """Get the stats for a specific activity."""

    async def action(page: Page, _) -> dict[str, Any]:
        data = await handle_network_extraction(page, f"activity-service/activity/{activity_id}")
        return {"garmin_activity_stats": data}

    return await dpage_with_action(
        f"https://connect.garmin.com/modern/activity/{activity_id}",
        action,
    )


@garmin_mcp.tool
async def calculate_calories_burned(avg_power: float, seconds: int) -> dict[str, Any]:
    """Get the fueling strategy for a specific activity."""
    mechanical_work = avg_power * seconds
    calories_burned = mechanical_work / (0.25 * 4.184)
    return {
        "calories_burned": calories_burned,
    }


@garmin_mcp.tool
async def calculate_tss(
    seconds: int, norm_power: float, intensity_factor: float, ftp: float
) -> dict[str, Any]:
    """Calculate the TSS for a specific activity. Ask FTP first from user first."""
    tss = (seconds * norm_power * intensity_factor) / (ftp * 3600) * 100
    return {
        "tss": tss,
    }
