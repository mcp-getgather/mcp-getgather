import importlib
from typing import Any

from fastmcp import Context, FastMCP

from getgather.logs import logger
from getgather.mcp.auto_import import auto_import
from getgather.mcp.middleware import AuthMiddleware, FilterDisabledBrandsMiddleware
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import poll_status_hosted_link


def create_mcp_app():
    """Create and return the MCP ASGI app.

    This performs plugin discovery/registration and mounts brand MCPs.
    """
    # Discover and import all brand MCP modules (registers into BrandMCPBase.registry)
    auto_import("getgather.mcp.brand")

    # Ensure calendar MCP is registered by importing its module
    try:
        importlib.import_module("getgather.mcp.calendar_utils")
    except Exception as e:
        logger.warning(f"Failed to register calendar MCP: {e}")

    mcp = FastMCP[Context](name="Getgather MCP")
    mcp.add_middleware(AuthMiddleware())
    mcp.add_middleware(FilterDisabledBrandsMiddleware())

    @mcp.tool(tags={"general_tool"})
    async def poll_auth(ctx: Context, link_id: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """Poll auth for a session. Only call this tool if you get the auth link/url."""
        return await poll_status_hosted_link(context=ctx, hosted_link_id=link_id)

    for prefix, brand_mcp in BrandMCPBase.registry.items():
        logger.info(f"Mounting {prefix} with {brand_mcp}")
        mcp.mount(server=brand_mcp, prefix=prefix)

    return mcp.http_app(path="/")
