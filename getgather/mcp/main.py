from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult

from getgather.browser.profile import BrowserProfile
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.auto_import import auto_import
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import auth_hosted_link, poll_status_hosted_link
from getgather.mcp.store import BrandConnectionStore

auto_import("getgather.mcp.brand")


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
        if "private" not in tool.tags:
            return await call_next(context)

        brand_id = BrandIdEnum(context.message.name.split("_")[0])
        if BrandConnectionStore.is_brand_connected(brand_id):
            return await call_next(context)

        browser_profile_id = BrandConnectionStore.get_browser_profile_id(brand_id)
        if not browser_profile_id:
            browser_profile = BrowserProfile()
            BrandConnectionStore.init_brand_state(brand_id, browser_profile.id)

        logger.info(
            f"[AuthMiddleware] processing auth for brand {brand_id} with browser profile {browser_profile_id}"
        )

        result = await auth_hosted_link(brand_id)
        return ToolResult(structured_content=result)


mcp = FastMCP[Context](name="Getgather MCP")

mcp.add_middleware(AuthMiddleware())


@mcp.tool
async def poll_auth(ctx: Context, link_id: str) -> dict[str, Any]:
    """Poll auth for a session. Only call this tool if you get the auth link/url."""
    return await poll_status_hosted_link(context=ctx, hosted_link_id=link_id)


for prefix, brand_mcp in BrandMCPBase.registry.items():
    logger.info(f"Mounting {prefix} with {brand_mcp}")
    mcp.mount(server=brand_mcp, prefix=prefix)

mcp_app = mcp.http_app(path="/")
