from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

cnn_mcp = BrandMCPBase(brand_id="cnn", name="CNN MCP")


@cnn_mcp.tool(tags={"private"})
async def get_newsletter() -> dict[str, Any]:
    """Get bookmarks of cnn."""
    return await extract()
