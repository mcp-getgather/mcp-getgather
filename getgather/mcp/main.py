from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.auto_import import auto_import
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.session_manager import SessionManager
from getgather.mcp.shared import auth_hosted_link, poll_status_hosted_link

auto_import("getgather.mcp.brand")


class AuthMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]):  # type: ignore
        if context.fastmcp_context:
            logger.info("[AuthMiddleware Context]: %s", context.message)

            tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)  # type: ignore
            session_id = context.fastmcp_context.session_id
            logger.info("[AuthMiddleware Session ID]: %s", session_id)
            try:
                SessionManager.get_browser_profile_id(session_id=session_id)
            except ValueError:
                browser_profile = BrowserProfile.create()
                browser_session = await BrowserSession.get(browser_profile)
                await browser_session.start()
                SessionManager.create_session(
                    browser_profile_id=browser_profile.profile_id, session_id=session_id
                )
                await browser_session.stop()

            if "private" in tool.tags:
                brand_id = context.message.name.split("_")[0]
                if not SessionManager.is_brand_connected(brand_id=brand_id, session_id=session_id):
                    result = await auth_hosted_link(
                        session_id=session_id, brand_id=BrandIdEnum(brand_id)
                    )
                    return ToolResult(structured_content=result)

        return await call_next(context)


mcp = FastMCP[Context](name="Getgather MCP")

mcp.add_middleware(AuthMiddleware())


@mcp.tool
async def poll_auth(
    ctx: Context,
    session_id: str,
) -> dict[str, Any]:
    """Poll auth for a session. Only call this tool if you get the auth link/url."""
    return await poll_status_hosted_link(
        context=ctx, hosted_link_session_id=session_id, session_id=ctx.session_id
    )


for prefix, brand_mcp in BrandMCPBase.registry.items():
    logger.info(f"Mounting {prefix} with {brand_mcp}")
    mcp.mount(server=brand_mcp, prefix=prefix)

mcp_app = mcp.http_app(path="/")
