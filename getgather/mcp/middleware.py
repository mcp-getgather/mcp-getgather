from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, AsyncGenerator

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import Tool, ToolResult

from getgather.browser.profile import BrowserProfile
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.database.repositories.activity_repository import Activity
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.logs import logger
from getgather.mcp.shared import auth_hosted_link


@asynccontextmanager
async def activity(name: str, brand_id: str = "") -> AsyncGenerator[None, None]:
    """Context manager for tracking activity."""
    activity_id = Activity.add(
        Activity(
            brand_id=brand_id,
            name=name,
            start_time=datetime.now(UTC),
        )
    )
    try:
        yield
    finally:
        Activity.update_end_time(
            id=activity_id,
            end_time=datetime.now(UTC),
        )


class FilterDisabledBrandsMiddleware(Middleware):
    async def on_list_tools(
        self, context: MiddlewareContext[Any], call_next: CallNext[Any, list[Tool]]
    ) -> list[Tool]:
        result = await call_next(context)
        disabled_brands = [brand.brand_id for brand in BrandState.get_all() if not brand.enabled]

        filtered_tools: list[Tool] = []
        for tool in result:
            key_parts = tool.key.split("_")
            if key_parts[0] not in disabled_brands:
                filtered_tools.append(tool)

        return filtered_tools


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
            BrandState.update_browser_profile_id(
                brand_id=BrandIdEnum(brand_id),
                browser_profile_id=browser_profile.id,
            )

        logger.info(
            f"[AuthMiddleware] processing auth for brand {brand_id} with browser profile {browser_profile_id}"
        )

        async with activity(
            brand_id=brand_id,
            name="auth",
        ):
            result = await auth_hosted_link(brand_id=BrandIdEnum(brand_id))
            return ToolResult(structured_content=result)
