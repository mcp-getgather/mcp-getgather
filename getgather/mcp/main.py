from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult

from getgather.api.types import RequestInfo
from getgather.browser.profile import BrowserProfile
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.auto_import import auto_import
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import auth_hosted_link, poll_status_hosted_link
from getgather.mcp.store import BrandConnectionStore, ProfileStore

auto_import("getgather.mcp.brand")


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


@mcp.tool
async def set_proxy_location(
    brand_id: str,
    city: str | None = None,
    state: str | None = None, 
    country: str | None = None,
    postal_code: str | None = None
) -> dict[str, Any]:
    """Set proxy location for the browser profile associated with a brand.
    
    This sets the location for the entire browser profile, which:
    - Affects all brands that share this browser profile
    - Persists across browser sessions (profile is reused)
    - Remains until explicitly changed or cleared
    
    The location is used for proxy routing if a proxy service is configured.
    
    Args:
        brand_id: Brand identifier to get the associated browser profile (e.g., "goodreads", "ebird")
        city: City name (e.g., "Los Angeles")
        state: State/Province name (e.g., "California") 
        country: Country code (e.g., "US", "DE", "GB")
        postal_code: Postal/ZIP code
        
    Returns:
        Success message with location details
    """
    brand_enum = BrandIdEnum(brand_id)
    profile_id = BrandConnectionStore.get_browser_profile_id(brand_enum)
    
    if not profile_id:
        # If no profile exists yet, create one
        browser_profile = BrowserProfile()
        BrandConnectionStore.init_brand_state(brand_enum, browser_profile.id)
        profile_id = browser_profile.id
    
    # Create location object
    location = RequestInfo(
        city=city,
        state=state, 
        country=country,
        postal_code=postal_code
    )
    
    # Store location for this profile
    ProfileStore.set_profile_location(profile_id, location)
    
    location_parts: list[str] = []
    if city:
        location_parts.append(f"City: {city}")
    if state:
        location_parts.append(f"State: {state}")
    if country:
        location_parts.append(f"Country: {country}")
    if postal_code:
        location_parts.append(f"Postal: {postal_code}")
    
    location_str = ", ".join(location_parts) if location_parts else "No location specified"
    
    return {
        "status": "success",
        "message": f"Proxy location set for browser profile {profile_id} (accessed via brand '{brand_id}')",
        "location": location_str,
        "profile_id": profile_id,
        "note": "This location affects all brands using this browser profile"
    }


@mcp.tool 
async def clear_proxy_location(brand_id: str) -> dict[str, Any]:
    """Clear proxy location for the browser profile associated with a brand.
    
    Args:
        brand_id: Brand identifier to get the associated browser profile (e.g., "goodreads", "ebird")
        
    Returns:
        Success message
    """
    brand_enum = BrandIdEnum(brand_id)
    profile_id = BrandConnectionStore.get_browser_profile_id(brand_enum)
    
    if not profile_id:
        return {
            "status": "error", 
            "message": f"No browser profile found for brand '{brand_id}'"
        }
    
    ProfileStore.clear_profile_location(profile_id)
    
    return {
        "status": "success",
        "message": f"Proxy location cleared for browser profile {profile_id} (accessed via brand '{brand_id}')",
        "profile_id": profile_id,
        "note": "This affects all brands using this browser profile"
    }


for prefix, brand_mcp in BrandMCPBase.registry.items():
    logger.info(f"Mounting {prefix} with {brand_mcp}")
    mcp.mount(server=brand_mcp, prefix=prefix)

mcp_app = mcp.http_app(path="/")
