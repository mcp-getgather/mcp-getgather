from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import aiohttp
from patchright.async_api import BrowserContext, Route

from getgather.config import settings
from getgather.logs import logger


def _get_domain_variants(domain: str) -> list[str]:
    """Get domain and all parent domains for subdomain matching.

    This is necessary because blocklists typically contain base domains (e.g., "doubleclick.net"),
    but actual requests come from subdomains (e.g., "ad.doubleclick.net", "stats.doubleclick.net").
    Without checking parent domains, most blocked requests would be missed.

    Args:
        domain: Domain to get variants for (e.g., "www.ads.google.com")

    Returns:
        List of domain variants from most specific to least, excluding bare TLDs
        (e.g., ["www.ads.google.com", "ads.google.com", "google.com"])
    """
    parts = domain.split(".")
    variants: list[str] = []

    # Generate variants from most specific to base domain (excluding bare TLD)
    for i in range(len(parts) - 1):
        variants.append(".".join(parts[i:]))

    return variants


async def _load_blocklist_from_urls(urls: list[str]) -> frozenset[str]:
    """Download and parse blocklists from multiple remote URLs.

    Args:
        urls: List of URLs to download blocklists from

    Returns:
        Set of all domain strings from all blocklists
    """
    all_domains: set[str] = set()

    for url in urls:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                response.raise_for_status()
                content = await response.text()
                logger.info(f"Successfully downloaded blocklist ({len(content)} bytes)")

                # Parse domains from content (one per line)
                domains = {line.strip() for line in content.splitlines() if line.strip()}
                all_domains.update(domains)
                logger.info(f"Loaded {len(domains)} domains from {url.split('/')[-1]}")

    return frozenset(all_domains)


async def _load_blocklist_from_file(path: Path) -> frozenset[str]:
    """Load blocklist domains from a file.

    Args:
        path: Path to the blocklist file

    Returns:
        Frozenset of domain strings
    """
    async with aiofiles.open(path, "r") as f:
        lines = await f.readlines()
        return frozenset(line.strip() for line in lines)


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


class ResourceBlocker:
    """Manages resource type blocking and domain blocklist checking."""

    _BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
    _BLOCKLIST_PATH = settings.data_dir / "blocklists.txt"
    _BLOCKLIST_URLS = [
        "https://raw.githubusercontent.com/hectorm/hmirror/refs/heads/master/data/molinero.dev/list.txt",
        "https://raw.githubusercontent.com/hectorm/hmirror/refs/heads/master/data/adguard-cname-trackers/list.txt",
        "https://raw.githubusercontent.com/hectorm/hmirror/refs/heads/master/data/easyprivacy/list.txt",
    ]

    def __init__(self):
        self._domains: frozenset[str] | None = None

    async def load(self) -> None:
        """Load all configured blocklists into memory."""
        logger.info("Loading blocklists...")

        if self._BLOCKLIST_PATH.exists():
            self._domains = await _load_blocklist_from_file(self._BLOCKLIST_PATH)
        else:
            self._domains = await _load_blocklist_from_urls(self._BLOCKLIST_URLS)

            # Save blocklist to file
            self._BLOCKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self._BLOCKLIST_PATH, "w") as f:
                await f.write("\n".join(sorted(self._domains)))
            logger.info(f"Saved blocklist to: {self._BLOCKLIST_PATH.name}")

        logger.info(f"Blocklists loaded: {len(self._domains)} total domains")

    async def is_blocked(self, url: str) -> bool:
        """Check if a URL should be blocked based on loaded blocklists.

        Checks the domain and all parent domains for matches.

        Args:
            url: The URL to check

        Returns:
            True if the domain or any parent domain is in the blocklist
        """
        if self._domains is None:
            return False

        domain = _extract_domain(url)
        if not domain:
            return False

        for variant in _get_domain_variants(domain):
            if variant in self._domains:
                return True

        return False

    def is_resource_type_blocked(self, resource_type: str) -> bool:
        """Check if a resource type should be blocked.

        Args:
            resource_type: The resource type to check (e.g., "image", "media", "font")

        Returns:
            True if the resource type should be blocked
        """
        return resource_type in self._BLOCKED_RESOURCE_TYPES


resource_blocker = ResourceBlocker()


async def configure_context(context: BrowserContext) -> None:
    if not settings.SHOULD_BLOCK_UNWANTED_RESOURCES:
        return

    await context.route("**/*", _handle_route)


async def _handle_route(route: Route) -> None:
    request = route.request
    resource_type = request.resource_type
    url = request.url

    try:
        if resource_blocker.is_resource_type_blocked(resource_type):
            await route.abort()
            return

        if await resource_blocker.is_blocked(url):
            await route.abort()
            return

        await route.continue_()
    except Exception as exc:
        logger.debug(
            "Route handling ignored for closed page or context.",
            extra={"url": url, "error": str(exc)},
        )
