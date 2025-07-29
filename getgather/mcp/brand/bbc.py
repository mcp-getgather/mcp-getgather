from fastmcp import FastMCP, Context
from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum

from fastmcp.utilities.logging import get_logger

from getgather.mcp.shared import extract

logger = get_logger(__name__)


bbc_mcp = FastMCP[Any](name="BBC MCP")


@bbc_mcp.tool(tags={"private"})
async def get_bookmarks(
    ctx: Context,
) -> dict[str, Any]:
    """Get bookmarks of bbc."""
    return await extract(session_id=ctx.session_id, brand_id=BrandIdEnum("bbc"))
