from __future__ import annotations

from types import MethodType
from typing import Iterable

from patchright.async_api import BrowserContext, Page, Route

from getgather.config import settings
from getgather.logs import logger

_BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
_BLOCKED_URL_KEYWORDS = ("quantummetric.com", "nr-data.net", "googletagmanager.com")


async def configure_context(context: BrowserContext) -> None:
    """Install resource blocking for all existing and future pages in the context."""
    if not settings.SHOULD_BLOCK_UNWANTED_RESOURCES:
        return

    if getattr(context, "_gather_resource_blocking_configured", False):
        return

    original_new_page = context.new_page

    async def new_page_with_blocking(self: BrowserContext) -> Page:
        page = await original_new_page()
        await _maybe_block_unwanted_resources(page)
        return page

    context.new_page = MethodType(new_page_with_blocking, context)

    await _configure_existing_pages(context.pages)

    setattr(context, "_gather_resource_blocking_configured", True)


async def _configure_existing_pages(pages: Iterable[Page]) -> None:
    for page in pages:
        await _maybe_block_unwanted_resources(page)


async def _maybe_block_unwanted_resources(page: Page) -> None:
    if getattr(page, "_gather_resource_blocking_enabled", False):
        return

    await page.route("**/*", _handle_route)
    setattr(page, "_gather_resource_blocking_enabled", True)


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

        await route.continue_()
    except Exception as exc:
        logger.debug(
            "Route handling ignored for closed page or context.",
            extra={"url": url, "error": str(exc)},
        )
