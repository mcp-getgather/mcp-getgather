"""Proxy configuration for browser sessions.

This module provides proxy configuration for external proxy service integration
with hierarchical location support (city, state, country).
"""

import re
from urllib.parse import urlsplit

from patchright.async_api import ProxySettings

from getgather.api.types import ProxyInfo
from getgather.config import settings
from getgather.logs import logger


async def setup_proxy(profile_id: str, proxy_info: ProxyInfo | None = None) -> ProxySettings | None:
    """Setup proxy configuration using external proxy service.

    The proxy service supports hierarchical location targeting by encoding
    location information in the username format:
    - Basic: profile_id
    - With location: profile_id-city_X_postal_code_Y_state_Z_country_W

    Args:
        profile_id: Profile ID to use as base proxy username
        proxy_info: Optional proxy information containing location data and proxy URL

    Returns:
        dict: Proxy configuration with server, username and password
        None: If no proxy is configured
    """

    if proxy_info and proxy_info.browser_proxy == "":
        logger.info(f"No proxy provided from proxy_info, skipping proxy setup")
        return None

    browser_proxy = (
        proxy_info.browser_proxy
        if proxy_info and proxy_info.browser_proxy
        else settings.BROWSER_PROXY
    )

    # Check if proxy service is configured
    if not browser_proxy:
        return None

    proxy = urlsplit(browser_proxy)
    if not proxy.password:
        raise ValueError("BROWSER_PROXY must contain a password")
    if not proxy.scheme:
        raise ValueError("BROWSER_PROXY must contain a scheme")

    proxy_url = re.sub("://.*@", "://", browser_proxy)
    logger.info(f"Setting up proxy service {proxy_url}")

    username = proxy.username or get_proxy_username(profile_id, proxy_info)
    return ProxySettings(server=proxy_url, username=username, password=proxy.password)


def get_proxy_username(profile_id: str, proxy_info: ProxyInfo | None = None) -> str:
    # Use profile ID as base username
    username = profile_id

    if proxy_info and (
        proxy_info.country or proxy_info.state or proxy_info.city or proxy_info.postal_code
    ):
        # Log the incoming proxy_info for debugging
        logger.info(
            f"ProxyInfo received - city: {proxy_info.city}, "
            f"postal_code: {proxy_info.postal_code}, "
            f"state: {proxy_info.state}, country: {proxy_info.country}"
        )
        # Build hierarchical location string for proxy service
        location_parts: list[str] = []

        # Add city if available
        if proxy_info.city:
            location_parts.extend(["city", proxy_info.city.lower().replace(" ", "_")])

        # Add postal code if available
        if proxy_info.postal_code:
            location_parts.extend(["postalcode", proxy_info.postal_code])

        # Add state if available (mainly for US)
        if proxy_info.state:
            location_parts.extend(["state", proxy_info.state.lower().replace(" ", "_")])

        # Add country if available
        if proxy_info.country:
            location_parts.extend(["country", proxy_info.country.lower()])

        if location_parts:
            # Format: profile_id-city_losangeles_postalcode_90001_state_california_country_us
            location = "_".join(location_parts)
            username = f"{profile_id}-{location}"
            logger.info(
                f"Using proxy service with profile '{profile_id}' and hierarchical location: {location}"
            )
        else:
            logger.info(
                f"Using proxy service with profile '{profile_id}' without specific location"
            )
    else:
        logger.info(f"Using proxy service with profile '{profile_id}' and default settings")

    return username
