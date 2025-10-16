from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

alltrails_mcp = GatherMCP(brand_id="alltrails", name="Alltrails MCP")


@alltrails_mcp.tool
async def get_feed() -> dict[str, Any]:
    """Get feed of alltrails."""
    return await dpage_mcp_tool("https://www.alltrails.com/my/profile/", "alltrails_feed")
