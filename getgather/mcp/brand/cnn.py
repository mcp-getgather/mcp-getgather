from fastmcp import Context
from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum

from fastmcp.utilities.logging import get_logger

from getgather.mcp.shared import extract
from getgather.mcp.registry import BrandMCPBase

logger = get_logger(__name__)


cnn_mcp = BrandMCPBase(prefix="cnn", name="CNN MCP")


@cnn_mcp.tool(tags={"private"})
async def get_newsletter(
    ctx: Context,
) -> dict[str, Any]:
    """Get bookmarks of cnn."""
    return await extract(session_id=ctx.session_id, brand_id=BrandIdEnum("cnn"))
