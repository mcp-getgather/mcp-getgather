import importlib
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.server.http import StarletteWithLifespan
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
        context.fastmcp_context.set_state("brand_id", brand_id)

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


CATEGORY_BUNDLES: dict[str, list[str]] = {
    "food": ["doordash", "ubereats"],
    "books": ["audible", "goodreads", "kindle", "hardcover"],
    "shopping": ["amazon", "shopee", "tokopedia"],
}


def create_mcp_apps() -> dict[str, StarletteWithLifespan]:
    # Discover and import all brand MCP modules (registers into BrandMCPBase.registry)
    auto_import("getgather.mcp.brand")

    # Ensure calendar MCP is registered by importing its module
    try:
        importlib.import_module("getgather.mcp.calendar_utils")
    except Exception as e:
        logger.warning(f"Failed to register calendar MCP: {e}")

    # "all" MCP has all brands and tools
    bundles: dict[str, list[BrandIdEnum]] = {"all": list(BrandMCPBase.registry.keys())}
    # [brand] MCP has tools for a single brand
    bundles.update({brand_id.value: [brand_id] for brand_id in BrandMCPBase.registry.keys()})
    # [category] MCP has tools for a category of brands
    bundles.update({
        bundle_name: [BrandIdEnum(brand_id) for brand_id in brand_ids]
        for bundle_name, brand_ids in CATEGORY_BUNDLES.items()
    })
    apps = {
        bundle_name: _create_mcp_app(bundle_name, brand_ids)
        for bundle_name, brand_ids in bundles.items()
    }
    return apps


def _create_mcp_app(bundle_name: str, brand_ids: list[BrandIdEnum]):
    """Create and return the MCP ASGI app.

    This performs plugin discovery/registration and mounts brand MCPs.
    """
    mcp = FastMCP[Context](name=f"Getgather {bundle_name} MCP")
    mcp.add_middleware(AuthMiddleware())

    @mcp.tool(tags={"general_tool"})
    async def poll_auth(ctx: Context, link_id: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """Poll auth for a session. Only call this tool if you get the auth link/url."""
        return await poll_status_hosted_link(context=ctx, hosted_link_id=link_id)

    for brand_id in brand_ids:
        brand_mcp = BrandMCPBase.registry[brand_id]
        logger.info(f"Mounting {brand_mcp.name} to MCP bundle {bundle_name}")
        mcp.mount(server=brand_mcp, prefix=brand_mcp.brand_id)

    from getgather.mcp.calendar_utils import calendar_mcp

    mcp.mount(server=calendar_mcp, prefix="calendar")

    return mcp.http_app(path="/")
