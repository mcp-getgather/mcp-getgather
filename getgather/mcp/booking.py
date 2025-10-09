from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

booking_mcp = GatherMCP(brand_id="booking", name="Booking MCP")


@booking_mcp.tool
async def get_past_trips() -> dict[str, Any]:
    """Get past trip of booking.com."""
    return await dpage_mcp_tool("https://secure.booking.com/mytrips.html", "booking_past_trips")
