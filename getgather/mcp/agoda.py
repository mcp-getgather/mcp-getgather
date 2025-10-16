from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

agoda_mcp = GatherMCP(brand_id="agoda", name="Agoda MCP")


@agoda_mcp.tool
async def get_complete_bookings() -> dict[str, Any]:
    """Get complete bookings of agoda."""
    return await dpage_mcp_tool(
        "https://www.agoda.com/account/bookings.html?sort=BookingStartDate&state=Completed&page=1",
        "agoda_complete_bookings",
    )
