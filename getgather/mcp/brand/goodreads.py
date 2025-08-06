from typing import Any

from fastmcp import Context
from fastmcp.utilities.logging import get_logger

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

logger = get_logger(__name__)

goodreads_mcp = BrandMCPBase(prefix="goodreads", name="Goodreads MCP")


@goodreads_mcp.tool(tags={"private"})
async def get_book_list(
    ctx: Context,
) -> dict[str, Any]:
    """Get book list of a goodreads."""
    return await extract(session_id=ctx.session_id, brand_id=BrandIdEnum("goodreads"))
