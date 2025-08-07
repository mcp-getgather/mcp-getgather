from typing import Any

from fastmcp import Context
from fastmcp.utilities.logging import get_logger

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

logger = get_logger(__name__)


hardcover_mcp = BrandMCPBase(prefix="hardcover", name="Hardcover MCP")


@hardcover_mcp.tool(tags={"private"})
async def get_book_list(
    ctx: Context,
) -> dict[str, Any]:
    """Get book list from Hardcover.app."""
    return await extract(brand_id=BrandIdEnum("hardcover"))
