from typing import Any

from fastmcp import Context

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

bbc_mcp = BrandMCPBase(prefix="bbc", name="BBC MCP")


@bbc_mcp.tool(tags={"private"})
async def get_bookmarks(
    ctx: Context,
) -> dict[str, Any]:
    """Get bookmarks of bbc."""
    return await extract(session_id=ctx.session_id, brand_id=BrandIdEnum("bbc"))
