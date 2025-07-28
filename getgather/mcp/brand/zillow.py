
from fastmcp import FastMCP, Context
from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum

from getgather.config import settings

from fastmcp.utilities.logging import get_logger

from getgather.mcp.shared import auth, extract

logger = get_logger(__name__)


zillow_mcp = FastMCP[Any](name="Zillow MCP")


@zillow_mcp.tool
async def login(
    ctx: Context,
    inputs: dict[str, str] = {},
    current_page_spec_name: str | None = None,
) -> dict[str, Any]:
    """Login to zillow if needed."""

    request = ctx.get_http_request()
    headers = request.headers

    inputs["email"] = inputs.get("email",  headers.get(
        'ZILLOW_EMAIL', settings.ZILLOW_EMAIL))
    inputs["password"] = inputs.get("password", headers.get(
        'ZILLOW_PASSWORD', settings.ZILLOW_PASSWORD))
    inputs["continue"] = "true"
    inputs["submit"] = "true"

    return await auth(session_id=ctx.session_id, brand_id=BrandIdEnum("zillow"), inputs=inputs, current_page_spec_name=current_page_spec_name)


@zillow_mcp.tool(tags={"private"})
async def get_favorites(
    ctx: Context,
) -> dict[str, Any]:
    """Get favorites of zillow."""
    return await extract(session_id=ctx.session_id, brand_id=BrandIdEnum("zillow"))
