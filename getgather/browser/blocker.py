from __future__ import annotations

from patchright.async_api import BrowserContext, Route

from getgather.browser.blocklist import blocklist_manager
from getgather.config import settings
from getgather.logs import logger

_BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
_BLOCKED_URL_KEYWORDS = ("quantummetric.com", "nr-data.net", "googletagmanager.com")


async def configure_context(context: BrowserContext) -> None:
    """Install resource blocking for all existing and future pages in the context."""
    if not settings.SHOULD_BLOCK_UNWANTED_RESOURCES:
        return

    await context.route("**/*", _handle_route)


async def _handle_route(route: Route) -> None:
    request = route.request
    resource_type = request.resource_type
    url = request.url

    try:
        if resource_type in _BLOCKED_RESOURCE_TYPES:
            await route.abort()
            return

        if any(keyword in url for keyword in _BLOCKED_URL_KEYWORDS):
            await route.abort()
            return

        if await blocklist_manager.is_blocked(url):
            await route.abort()
            return

        await route.continue_()
    except Exception as exc:
        logger.debug(
            "Route handling ignored for closed page or context.",
            extra={"url": url, "error": str(exc)},
        )
