"""Proxy configuration for browser sessions.

This module provides proxy configuration for external proxy service integration
with hierarchical location support (city, state, country).
"""

from getgather.api.types import RequestInfo
from getgather.config import settings
from getgather.logs import logger


async def setup_proxy(
    profile_id: str, request_info: RequestInfo | None = None
) -> dict[str, str] | None:
    """Setup proxy configuration using external proxy service.

    The proxy service supports hierarchical location targeting by encoding
    location information in the username format:
    - Basic: profile_id (or custom proxy username if provided)
    - With location: <username>-city_X_postal_code_Y_state_Z_country_W

    Args:
        profile_id: Profile ID to use as base proxy username
        request_info: Optional request information containing location data

    Returns:
        dict: Proxy configuration with server, username and password
        None: If no proxy is configured
    """
    # Check if proxy service is configured
    if not settings.BROWSER_HTTP_PROXY or not settings.BROWSER_HTTP_PROXY_PASSWORD:
        logger.info(
            "No proxy configured (BROWSER_HTTP_PROXY and BROWSER_HTTP_PROXY_PASSWORD not set)"
        )
        return None

    # Determine base username (custom header overrides profile ID when provided)
    username_base = profile_id
    if request_info and request_info.custom_proxy_username:
        username_base = request_info.custom_proxy_username

    username = username_base

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
            # Format: username-city_losangeles_postalcode_90001_state_california_country_us
            location = "_".join(location_parts)
            username = f"{username_base}-{location}"
            logger.info(
                f"Using proxy service with username '{username}' and hierarchical location: {location}"
            )
        else:
            logger.info(
                f"Using proxy service with username '{username_base}' without specific location"
            )
    else:
        logger.info(f"Using proxy service with username '{username_base}' and default settings")

    # Return proxy configuration for the service
    return {
        "server": settings.BROWSER_HTTP_PROXY,
        "username": username,
        "password": settings.BROWSER_HTTP_PROXY_PASSWORD,
    }
