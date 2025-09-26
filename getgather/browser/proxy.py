"""Proxy configuration for browser sessions.

This module provides proxy configuration for external proxy service integration
with hierarchical location support (city, state, country).
"""

import re
from urllib.parse import urlsplit

from patchright.async_api import ProxySettings

from getgather.api.types import RequestInfo
from getgather.config import settings
from getgather.logs import logger


async def setup_proxy(
    profile_id: str, request_info: RequestInfo | None = None
) -> ProxySettings | None:
    """Setup proxy configuration using external proxy service.

    The proxy service supports hierarchical location targeting by encoding
    location information in the username format:
    - Basic: profile_id
    - With location: profile_id-city_X_postal_code_Y_state_Z_country_W

    Args:
        profile_id: Profile ID to use as base proxy username
        request_info: Optional request information containing location data

    Returns:
        dict: Proxy configuration with server, username and password
        None: If no proxy is configured
    """
    # Check if proxy service is configured
    if not settings.BROWSER_PROXY:
        return None

    proxy = urlsplit(settings.BROWSER_PROXY)
    if not proxy.password:
        raise ValueError("BROWSER_PROXY must contain a password")
    if not proxy.scheme:
        raise ValueError("BROWSER_PROXY must contain a scheme")

    proxy_url = re.sub("://.*@", "://", settings.BROWSER_PROXY)
    logger.info(f"Setting up proxy service {proxy_url}")

    username = proxy.username or get_proxy_username(profile_id, request_info)
    return ProxySettings(server=proxy_url, username=username, password=proxy.password)


def get_proxy_username(profile_id: str, request_info: RequestInfo | None = None) -> str:
    # Use profile ID as base username
    username = profile_id

    if request_info and (
        request_info.country or request_info.state or request_info.city or request_info.postal_code
    ):
        # Log the incoming request_info for debugging
        logger.info(
            f"RequestInfo received - city: {request_info.city}, "
            f"postal_code: {request_info.postal_code}, "
            f"state: {request_info.state}, country: {request_info.country}"
        )
        # Build hierarchical location string for proxy service
        location_parts: list[str] = []

        # Add city if available
        if request_info.city:
            location_parts.extend(["city", request_info.city.lower().replace(" ", "_")])

        # Add postal code if available
        if request_info.postal_code:
            location_parts.extend(["postalcode", request_info.postal_code])

        # Add state if available (mainly for US)
        if request_info.state:
            location_parts.extend(["state", request_info.state.lower().replace(" ", "_")])

        # Add country if available
        if request_info.country:
            location_parts.extend(["country", request_info.country.lower()])

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
