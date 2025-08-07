from typing import Any

from fastmcp import Context
from fastmcp.utilities.logging import get_logger

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

logger = get_logger(__name__)


cnn_mcp = BrandMCPBase(prefix="cnn", name="CNN MCP")


@cnn_mcp.tool(tags={"private"})
async def get_newsletter(
    ctx: Context,
) -> dict[str, Any]:
    """Get bookmarks of cnn."""
    return await extract(brand_id=BrandIdEnum("cnn"))
