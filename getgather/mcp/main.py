from getgather.browser.profile import BrowserProfile
from fastmcp import FastMCP, Context

from getgather.browser.profile import BrowserProfile


from typing import Any

from getgather.browser.profile import BrowserProfile


from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from getgather.mcp.session_manager import SessionManager
from getgather.browser.session import BrowserSession


from fastmcp.utilities.logging import get_logger

from getgather.mcp.brand.goodreads import goodreads_mcp
from getgather.mcp.brand.ebird import ebird_mcp
from getgather.mcp.brand.bbc import bbc_mcp
from getgather.mcp.brand.zillow import zillow_mcp
from getgather.mcp.shared import auth
from getgather.auth_orchestrator import AuthStatus
from fastmcp.tools.tool import ToolResult
from getgather.connectors.spec_loader import BrandIdEnum


logger = get_logger(__name__)


class AuthMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]):  # type: ignore
        if context.fastmcp_context:
            tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)  # type: ignore
            session_id = context.fastmcp_context.session_id
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
                    auth_response = await auth(
                        session_id=session_id, brand_id=BrandIdEnum(brand_id)
                    )
                    if auth_response["status"] != AuthStatus.FINISHED:
                        return ToolResult(structured_content=auth_response)

        return await call_next(context)


mcp = FastMCP[Context](name="Getgather MCP")

mcp.add_middleware(AuthMiddleware())

mcp.mount(server=goodreads_mcp, prefix="goodreads")
mcp.mount(server=ebird_mcp, prefix="ebird")
mcp.mount(server=bbc_mcp, prefix="bbc")
mcp.mount(server=zillow_mcp, prefix="zillow")

mcp_app = mcp.http_app(path="/")
