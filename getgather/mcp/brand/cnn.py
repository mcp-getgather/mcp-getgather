from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

cnn_mcp = BrandMCPBase(prefix="cnn", name="CNN MCP")


@cnn_mcp.tool(tags={"private"})
async def get_newsletter() -> dict[str, Any]:
    """Get bookmarks of cnn."""
    return await extract(brand_id=BrandIdEnum("cnn"))
