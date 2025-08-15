import importlib
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult

from getgather.activity import activity
from getgather.browser.profile import BrowserProfile
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.logs import logger
from getgather.mcp.auto_import import auto_import
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import auth_hosted_link, poll_status_hosted_link

# Ensure calendar MCP is registered by importing its module
try:
    from getgather.mcp import calendar_utils  # type: ignore
except Exception as e:
    logger.warning(f"Failed to register calendar MCP: {e}")


class AuthMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]):  # type: ignore
        if not context.fastmcp_context:
            return await call_next(context)

        logger.info(f"[AuthMiddleware Context]: {context.message}")

        tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)  # type: ignore

        if "general_tool" in tool.tags:
            async with activity(
                name=context.message.name,
            ):
                return await call_next(context)

        brand_id = context.message.name.split("_")[0]
        if "private" not in tool.tags or BrandState.is_brand_connected(brand_id):
            async with activity(
                brand_id=brand_id,
                name=context.message.name,
            ):
                return await call_next(context)

        browser_profile_id = BrandState.get_browser_profile_id(brand_id)
        if not browser_profile_id:
            # Create and persist a new profile for the auth flow
            browser_profile = BrowserProfile()
            BrandState.add(
                BrandState(
                    brand_id=BrandIdEnum(brand_id),
                    browser_profile_id=browser_profile.id,
                    is_connected=False,
                )
            )

        logger.info(
            f"[AuthMiddleware] processing auth for brand {brand_id} with browser profile {browser_profile_id}"
        )

        async with activity(
            name="auth",
            brand_id=brand_id,
        ):
            result = await auth_hosted_link(brand_id=BrandIdEnum(brand_id))
            return ToolResult(structured_content=result)


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

    @mcp.tool(tags={"general_tool"})
    async def poll_auth(ctx: Context, link_id: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """Poll auth for a session. Only call this tool if you get the auth link/url."""
        return await poll_status_hosted_link(context=ctx, hosted_link_id=link_id)

    for prefix, brand_mcp in BrandMCPBase.registry.items():
        logger.info(f"Mounting {prefix} with {brand_mcp}")
        mcp.mount(server=brand_mcp, prefix=prefix)

    return mcp.http_app(path="/")
