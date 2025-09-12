"""Simplified MCP main using global profile manager."""

from dataclasses import dataclass
from functools import cache, cached_property
from typing import Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.server.http import StarletteWithLifespan
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.activity import activity
from getgather.mcp.auth import get_auth_user
from getgather.mcp.auto_import import auto_import
from getgather.mcp.calendar_utils import calendar_mcp
from getgather.mcp.connection_manager import connection_manager
from getgather.mcp.espn import espn_mcp
from getgather.mcp.nytimes import nytimes_mcp
from getgather.mcp.profile_manager import global_profile_manager
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import poll_status_hosted_link, signin_hosted_link

# Ensure calendar MCP is registered by importing its module
try:
    from getgather.mcp import calendar_utils  # type: ignore
except Exception as e:
    logger.warning(f"Failed to register calendar MCP: {e}")


class AuthMiddleware(Middleware):
    """Simplified auth middleware using global profile."""

    async def on_call_tool(self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]):  # type: ignore
        if not context.fastmcp_context:
            return await call_next(context)

        logger.info(f"[AuthMiddleware Context]: {context.message}")

        auth_user = get_auth_user()
        logger.info("[AuthMiddleware] auth_user", extra=auth_user.model_dump())

        tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)  # type: ignore

        if "general_tool" in tool.tags:
            async with activity(name=context.message.name):
                return await call_next(context)

        brand_id = BrandIdEnum(context.message.name.split("_")[0])
        context.fastmcp_context.set_state("brand_id", brand_id)

        # Check if private tool and brand is connected
        is_private = "private" in tool.tags
        is_connected = connection_manager.is_connected(brand_id)
        logger.info(
            f"[AuthMiddleware] Tool check: {context.message.name}, private={is_private}, connected={is_connected}, tags={tool.tags}"
        )

        if not is_private or is_connected:
            async with activity(brand_id=str(brand_id), name=context.message.name):
                return await call_next(context)

        # Need authentication - use global profile
        profile = global_profile_manager.get_profile()
        logger.info(
            f"[AuthMiddleware] processing auth for brand {brand_id} with global profile {profile.id}"
        )

        async with activity(name="auth", brand_id=str(brand_id)):
            result = await signin_hosted_link(brand_id=brand_id)
            return ToolResult(structured_content=result)


CATEGORY_BUNDLES: dict[str, list[str]] = {
    "food": ["doordash", "ubereats"],
    "books": ["audible", "goodreads", "kindle", "hardcover"],
    "shopping": ["amazon", "shopee", "tokopedia"],
}


@dataclass
class MCPApp:
    name: str
    type: Literal["brand", "category", "all"]
    route: str
    brand_ids: list[BrandIdEnum]

    @cached_property
    def mcp(self) -> FastMCP:
        """Build MCP server with global profile manager."""
        mcp = FastMCP(self.name, middleware=[AuthMiddleware()])

        # Mount global tools
        mcp.mount(server=calendar_mcp, prefix="calendar")
        mcp.mount(server=espn_mcp, prefix="espn")
        mcp.mount(server=nytimes_mcp, prefix="nytimes")

        # Auto-import all brand MCPs first (populates BrandMCPBase.registry)
        auto_import("getgather.mcp.brand")

        # Mount brand tools
        for brand_id in self.brand_ids:
            if brand_id in BrandMCPBase.registry:
                brand_mcp = BrandMCPBase.registry[brand_id]
                mcp.mount(server=brand_mcp, prefix=str(brand_id))

        # Add general polling tool
        @mcp.tool(tags={"general_tool"})
        async def poll_signin(context: Context, hosted_link_id: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
            """Poll the status of a hosted link."""
            return await poll_status_hosted_link(context, hosted_link_id)

        return mcp

    @cached_property
    def app(self) -> StarletteWithLifespan:
        """Get ASGI app."""
        return self.mcp.http_app(path="/")


@cache
def get_apps() -> list[MCPApp]:
    """Get all MCP apps with global profile setup."""
    all_brands = list(BrandIdEnum)

    apps = [
        MCPApp("all", "all", "/mcp", all_brands),
    ]

    # Add category apps
    for category, brand_names in CATEGORY_BUNDLES.items():
        brand_enums = [
            BrandIdEnum(name) for name in brand_names if name in [b.value for b in all_brands]
        ]
        if brand_enums:
            apps.append(MCPApp(category, "category", f"/mcp-{category}", brand_enums))

    # Add individual brand apps
    for brand in all_brands:
        apps.append(MCPApp(str(brand), "brand", f"/mcp-{brand}", [brand]))

    return apps


# Additional classes and functions needed by API
class MCPToolDoc(BaseModel):
    name: str
    description: str


class MCPDoc(BaseModel):
    name: str
    type: Literal["brand", "category", "all"]
    route: str
    tools: list[MCPToolDoc]


def create_mcp_apps() -> list[MCPApp]:
    """Create MCP apps - wrapper for get_apps for backward compatibility."""
    return get_apps()


async def mcp_app_docs(mcp_app: MCPApp) -> MCPDoc:
    """Generate documentation for an MCP app."""
    return MCPDoc(
        name=mcp_app.name,
        type=mcp_app.type,
        route=mcp_app.route,
        tools=[
            MCPToolDoc(
                name=tool.name,
                description=tool.description or "",
            )
            for tool in (await mcp_app.mcp.get_tools()).values()
        ],
    )
