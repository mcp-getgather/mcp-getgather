from dataclasses import dataclass
from functools import cache, cached_property
from typing import Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.server.http import StarletteWithLifespan
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel

from getgather.browser.profile import BrowserProfile
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.activity import activity
from getgather.mcp.auto_import import auto_import
from getgather.mcp.brand_state import BrandState, brand_state_manager
from getgather.mcp.calendar_utils import calendar_mcp
from getgather.mcp.dpage import dpage_check
from getgather.mcp.registry import BrandMCPBase, GatherMCP
from getgather.mcp.shared import poll_status_hosted_link, signin_hosted_link

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

        brand_state = brand_state_manager.get(brand_id)
        if "private" not in tool.tags or (brand_state and brand_state.is_connected):
            async with activity(
                brand_id=brand_id,
                name=context.message.name,
            ):
                return await call_next(context)

        browser_profile_id = brand_state.browser_profile_id if brand_state else None
        if not browser_profile_id:
            # Create and persist a new profile for the auth flow
            browser_profile = BrowserProfile()
            brand_state_manager.add(
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
            result = await signin_hosted_link(brand_id=BrandIdEnum(brand_id))
            return ToolResult(structured_content=result)


CATEGORY_BUNDLES: dict[str, list[str]] = {
    "food": ["doordash", "ubereats"],
    "books": ["audible", "goodreads", "kindle", "hardcover"],
    "shopping": ["amazon", "shopee", "tokopedia"],
    "media": [],
}

# For MCP tools based on distillation
MCP_BUNDLES: dict[str, list[str]] = {
    "media": ["bbc", "espn", "npr", "nytimes"],
}


@dataclass
class MCPApp:
    name: str
    type: Literal["brand", "category", "all"]
    route: str
    brand_ids: list[BrandIdEnum | str]

    @cached_property
    def app(self) -> StarletteWithLifespan:
        return _create_mcp_app(self.name, self.brand_ids)


@cache
def create_mcp_apps() -> list[MCPApp]:
    # Discover and import all brand MCP modules (registers into BrandMCPBase.registry)
    auto_import("getgather.mcp.brand")

    auto_import("getgather.mcp")  # Import distillation-based MCPs

    apps: list[MCPApp] = []
    apps.append(
        MCPApp(
            name="all",
            type="all",
            route="/mcp",
            brand_ids=list(BrandMCPBase.registry.keys())
            + [
                brand_id
                for brand_id in GatherMCP.registry.keys()
                if brand_id not in [b.value for b in BrandMCPBase.registry.keys()]
            ],
        )
    )
    # Add individual brand MCPs from BrandMCPBase registry
    apps.extend([
        MCPApp(
            name=brand_id.value,
            type="brand",
            route=f"/mcp-{brand_id.value}",
            brand_ids=[brand_id],
        )
        for brand_id in BrandMCPBase.registry.keys()
    ])
    # Add individual brand MCPs from GatherMCP registry
    apps.extend([
        MCPApp(
            name=brand_id,
            type="brand",
            route=f"/mcp-{brand_id}",
            brand_ids=[brand_id],
        )
        for brand_id in GatherMCP.registry.keys()
        if brand_id not in [b.value for b in BrandMCPBase.registry.keys()]
    ])
    apps.extend([
        MCPApp(
            name=category,
            type="category",
            route=f"/mcp-{category}",
            brand_ids=[BrandIdEnum(brand_id) for brand_id in brand_ids]
            + MCP_BUNDLES.get(category, []),
        )
        for category, brand_ids in CATEGORY_BUNDLES.items()
    ])

    return apps


def _create_mcp_app(bundle_name: str, brand_ids: list[BrandIdEnum | str]):
    """Create and return the MCP ASGI app.

    This performs plugin discovery/registration and mounts brand MCPs.
    """
    mcp = FastMCP[Context](name=f"Getgather {bundle_name} MCP")
    mcp.add_middleware(AuthMiddleware())

    @mcp.tool(tags={"general_tool"})
    async def poll_signin(ctx: Context, link_id: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """Poll sign in for a session. Only call this tool if you get the sign in link/url."""
        return await poll_status_hosted_link(context=ctx, hosted_link_id=link_id)

    @mcp.tool(tags={"general_tool"})
    async def check_signin(ctx: Context, signin_id: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        result = await dpage_check(id=signin_id)
        if result is None:
            return {
                "status": "ERROR",
                "message": "Sign in not completed within the time limit. Please try again.",
            }
        return {
            "status": "SUCCESS",
            "message": "Sign in completed successfully.",
            "result": result,
        }

    for brand_id in brand_ids:
        brand_id_str = brand_id.value if isinstance(brand_id, BrandIdEnum) else brand_id
        brand_id_enum = brand_id if isinstance(brand_id, BrandIdEnum) else None

        # Try BrandMCPBase registry first (if it's a BrandIdEnum)
        if brand_id_enum and brand_id_enum in BrandMCPBase.registry:
            brand_mcp = BrandMCPBase.registry[brand_id_enum]
            logger.info(f"Mounting {brand_mcp.name} to MCP bundle {bundle_name}")
            mcp.mount(server=brand_mcp, prefix=brand_mcp.brand_id)
        # Try GatherMCP registry (for string brand IDs)
        elif brand_id_str in GatherMCP.registry:
            gather_mcp = GatherMCP.registry[brand_id_str]
            logger.info(
                f"Mounting {gather_mcp.name} (distillation-based) to MCP bundle {bundle_name}"
            )
            mcp.mount(server=gather_mcp, prefix=gather_mcp.brand_id)

    mcp.mount(server=calendar_mcp, prefix="calendar")

    return mcp.http_app(path="/")


class MCPToolDoc(BaseModel):
    name: str
    description: str


class MCPDoc(BaseModel):
    name: str
    type: Literal["brand", "category", "all"]
    route: str
    tools: list[MCPToolDoc]


async def mcp_app_docs(mcp_app: MCPApp) -> MCPDoc:
    return MCPDoc(
        name=mcp_app.name,
        type=mcp_app.type,
        route=mcp_app.route,
        tools=[
            MCPToolDoc(
                name=tool.name,
                description=tool.description or "No description provided",
            )
            for tool in (await mcp_app.app.state.fastmcp_server.get_tools()).values()
        ],
    )
