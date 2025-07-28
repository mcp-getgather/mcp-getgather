
from fastmcp import FastMCP, Context
from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum

from getgather.config import settings

from fastmcp.utilities.logging import get_logger

from getgather.mcp.shared import auth, extract

logger = get_logger(__name__)


goodreads_mcp = FastMCP[Any](name="Goodreads MCP")


@goodreads_mcp.tool
async def login(
    ctx: Context,
    inputs: dict[str, str] = {},
    current_page_spec_name: str | None = None,
) -> dict[str, Any]:
    """Login to goodreads if needed."""

    request = ctx.get_http_request()
    headers = request.headers

    inputs["email"] = inputs.get("email",  headers.get(
        'GOODREADS_EMAIL', settings.GOODREADS_EMAIL))
    inputs["password"] = inputs.get("password", headers.get(
        'GOODREADS_PASSWORD', settings.GOODREADS_PASSWORD))

    return await auth(session_id=ctx.session_id, brand_id=BrandIdEnum("goodreads"), inputs=inputs, current_page_spec_name=current_page_spec_name)


@goodreads_mcp.tool(tags={"private"})
async def get_book_list(
    ctx: Context,
) -> dict[str, Any]:
    """Get book list of a goodreads."""
    return await extract(session_id=ctx.session_id, brand_id=BrandIdEnum("goodreads"))
