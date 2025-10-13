import asyncio
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import aiohttp
from patchright.async_api import BrowserContext, Route

from getgather.config import settings
from getgather.logs import logger


def _get_blocklist_file_path(url: str) -> Path:
    """Get the file path for a specific blocklist URL."""
    # Use last part of URL path as filename (e.g., "ads.txt", "tracking.txt")
    filename = url.rstrip("/").split("/")[-1]
    file_path = settings.data_dir / "blocklists" / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def _parse_blocklist_content(content: str) -> set[str]:
    """Parse blocklist content and extract domains.

    Expected format: "0.0.0.0 domain.com" or just "domain.com"
    """
    domains: set[str] = set()
    for line in content.splitlines():
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#") or line.startswith("!"):
            continue

        parts = line.split()
        if not parts:
            continue

        # Handle "0.0.0.0 domain.com" format or plain "domain.com"
        domain = parts[1] if line.startswith("0.0.0.0") and len(parts) > 1 else parts[0]
        domains.add(domain.lower())

    return domains


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


async def _download_blocklist(url: str) -> str:
    """Download a blocklist from the remote URL."""
    logger.info(f"Downloading blocklist from {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                response.raise_for_status()
                content = await response.text()
                logger.info(f"Successfully downloaded blocklist ({len(content)} bytes)")
                return content
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        logger.error(f"Failed to download blocklist from {url}: {exc}")
        raise


async def _load_blocklist(url: str) -> set[str]:
    """Load a single blocklist from local file or download if not exists."""
    file_path = _get_blocklist_file_path(url)

    # Try loading from local file
    if file_path.exists():
        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
            logger.debug(f"Loaded blocklist from file: {file_path.name}")
        except (OSError, IOError) as exc:
            logger.warning(f"Failed to load blocklist file: {exc}")
            content = None
    else:
        content = None

    # Download if file doesn't exist or failed to read
    if content is None:
        content = await _download_blocklist(url)
        try:
            async with aiofiles.open(file_path, "w") as f:
                await f.write(content)
            logger.debug(f"Saved blocklist to file: {file_path.name}")
        except (OSError, IOError) as exc:
            logger.warning(f"Failed to save blocklist: {exc}")

    # Parse and return domains
    return _parse_blocklist_content(content)


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
    _BLOCKLIST_URLS = [
        "https://raw.githubusercontent.com/blocklistproject/Lists/master/ads.txt",
        "https://raw.githubusercontent.com/blocklistproject/Lists/master/tracking.txt",
    ]

    def __init__(self):
        self._domains: frozenset[str] | None = None

    async def load(self) -> None:
        """Load all configured blocklists into memory."""
        logger.info("Loading blocklists...")

        # Load all blocklists sequentially
        all_domains: set[str] = set()
        for url in self._BLOCKLIST_URLS:
            domains = await _load_blocklist(url)
            all_domains.update(domains)
            logger.info(f"Loaded {len(domains)} domains from {url.split('/')[-1]}")

        self._domains = frozenset(all_domains)

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
    if not settings.ENABLE_BLOCKER:
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
