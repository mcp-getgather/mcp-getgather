from pathlib import Path
from types import MethodType
from urllib.parse import urlparse

import aiofiles
from patchright.async_api import BrowserContext, Page, Route

from getgather.config import PROJECT_DIR, settings
from getgather.logs import logger

_BLOCKED_RESOURCE_TYPES = {"media", "font"}
_blocked_domains: frozenset[str] | None = None
_allowed_domains: frozenset[str] = frozenset(["amazon.ca", "wayfair.com"])


def _get_domain_variants(domain: str) -> list[str]:
    """Get domain and all parent domains for subdomain matching.

    This is necessary because blocklists typically contain base domains (e.g., "doubleclick.net"),
    but actual requests come from subdomains (e.g., "ad.doubleclick.net", "stats.doubleclick.net").
    Without checking parent domains, most blocked requests would be missed.

    Args:
        domain: Domain to get variants for (e.g., "www.ads.google.com")

    Returns:
        List of domain variants from most specific to least, requiring at least 2 parts
        and stopping before potential TLDs (e.g., ["www.ads.google.com", "ads.google.com", "google.com"])
    """
    parts = domain.split(".")
    variants: list[str] = []

    # Generate variants from most specific to base domain, stopping at 2 parts minimum
    # This prevents treating TLDs like 'co.uk' or 'com' as blockable domains
    for i in range(len(parts) - 1):
        if len(parts) - i >= 2:
            variants.append(".".join(parts[i:]))

    return variants


async def _load_blocklist_from_file(path: Path) -> frozenset[str]:
    """Load blocklist domains from a file.

    Args:
        path: Path to the blocklist file

    Returns:
        Frozenset of domain strings
    """
    logger.debug(f"Loading blocked domains from {path}...")
    async with aiofiles.open(path, "r") as f:
        lines = await f.readlines()
        domains = frozenset(line.strip() for line in lines if line.strip())
        logger.debug(f"Loaded {len(domains)} domains from {path}")
        return domains


def _extract_domain(url: str) -> str:
    """Extract the domain from a URL.

    Args:
        url: Full URL string

    Returns:
        The domain portion (e.g., "example.com")
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


async def _load_blocklists() -> None:
    global _blocked_domains
    logger.info("Loading blocklists...")
    all_domains: set[str] = set()

    blocklist_files = list(PROJECT_DIR.glob("blocklists-*.txt"))
    if blocklist_files:
        for blocklist_file in blocklist_files:
            logger.debug(f"Loading blocklist file: {blocklist_file.name}")
            domains = await _load_blocklist_from_file(blocklist_file)
            all_domains.update(domains)

        filtered_domains = all_domains - _allowed_domains
        _blocked_domains = frozenset(filtered_domains)

    else:
        logger.warning("No blocklist files found matching pattern 'blocklists-*.txt'")
        _blocked_domains = frozenset()

    logger.info(f"Blocklists loaded: {len(_blocked_domains)} total domains")


async def configure_context(context: BrowserContext) -> None:
    """Install resource blocking for all existing and future pages in the context."""
    if not settings.SHOULD_BLOCK_UNWANTED_RESOURCES:
        return

    if getattr(context, "_gather_resource_blocking_configured", False):
        return

    if _blocked_domains is None:
        await _load_blocklists()

    original_new_page = context.new_page

    async def new_page_with_blocking(self: BrowserContext) -> Page:
        page = await original_new_page()
        await _maybe_block_unwanted_resources(page)
        return page

    context.new_page = MethodType(new_page_with_blocking, context)

    setattr(context, "_gather_resource_blocking_configured", True)


async def _maybe_block_unwanted_resources(page: Page) -> None:
    await page.route("**/*", _handle_route)


async def _should_be_blocked(url: str) -> bool:
    domain = _extract_domain(url)
    if not domain:
        return False

    if _blocked_domains is None:
        return False

    for variant in _get_domain_variants(domain):
        if variant in _blocked_domains:
            return True

    return False


async def _handle_route(route: Route) -> None:
    request = route.request
    resource_type = request.resource_type
    url = request.url

    try:
        if resource_type in _BLOCKED_RESOURCE_TYPES:
            await route.abort()
            return

        if await _should_be_blocked(url):
            logger.debug(f"DENY {url}")
            await route.abort()
            return

        await route.continue_()
    except Exception as exc:
        logger.debug(
            "Route handling ignored for closed page or context.",
            extra={"url": url, "error": str(exc)},
        )
