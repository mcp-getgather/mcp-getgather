"""Proxy configuration builder with template-based dynamic parameter replacement.

This module provides a flexible system for building proxy configurations from
environment variable templates, supporting multiple proxy providers with different
URL formats and parameter naming conventions.
"""

import re
from typing import Any
from urllib.parse import urlparse

from getgather.api.types import RequestInfo
from getgather.logs import logger


class ProxyConfig:
    """Represents a configured proxy from environment variables."""

    def __init__(
        self,
        url: str | None = None,
        params_template: str | None = None,
    ):
        """Initialize proxy configuration.

        Args:
            url: Proxy URL with credentials (e.g., 'http://user:pass@proxy.example.com:8888')
            params_template: Dynamic parameters with placeholders (e.g., 'country-{country}-sessionid-{session_id}')
        """
        self.params_template = params_template

        # Parse URL to extract username, password, and server
        self.base_username: str | None = None
        self.password: str | None = None
        self.server: str | None = None
        self.masked_url: str | None = None  # URL with credentials masked for logging

        if url:
            self._parse_url(url)

    def _parse_url(self, url: str) -> None:
        """Parse URL to extract base username, password, and server.

        Args:
            url: Full URL with credentials (e.g., 'user:pass@host:port' or 'http://user:pass@host:port')
        """
        # Add scheme if not present to help urlparse
        url_to_parse = url
        if "://" not in url:
            url_to_parse = f"http://{url}"

        # Create masked version for logging (mask credentials once)
        self.masked_url = re.sub(r"://[^@]+@", "://***@", url_to_parse)

        parsed = urlparse(url_to_parse)

        # Extract username and password from URL
        if parsed.username:
            self.base_username = parsed.username
        if parsed.password:
            self.password = parsed.password

        # Reconstruct server URL without credentials
        if parsed.hostname:
            scheme = parsed.scheme or "http"
            port = f":{parsed.port}" if parsed.port else ""
            self.server = f"{scheme}://{parsed.hostname}{port}"
        else:
            logger.warning(f"Could not parse hostname from URL: {self.masked_url}")
            self.server = url

    def build(
        self, profile_id: str, request_info: RequestInfo | None = None
    ) -> dict[str, str] | None:
        """Build proxy configuration dict with dynamic parameter replacement.

        Args:
            profile_id: Profile ID to use as session identifier
            request_info: Optional request information with location data

        Returns:
            dict: Proxy configuration with server, username, password
            None: If no server configured
        """
        if not self.server:
            logger.info("No proxy server configured, skipping proxy")
            return None

        # Build username from base + params
        username = None
        if self.base_username:
            username = self.base_username

            # Add dynamic parameters if template is provided
            if self.params_template:
                values = self._extract_values(profile_id, request_info)
                params = self._build_params(self.params_template, values)
                if params:
                    username = f"{username}-{params}"

            logger.info(f"Built proxy username: {username}")

        result = {
            "server": self.server,
        }
        if username:
            result["username"] = username
        if self.password:
            result["password"] = self.password

        logger.info(
            f"Built proxy config - server: {self.server}, username: {username}, "
            f"has_password: {bool(self.password)}"
        )
        return result

    def _extract_values(self, profile_id: str, request_info: RequestInfo | None) -> dict[str, Any]:
        """Extract replacement values from request info.

        Args:
            profile_id: Profile ID to use as session identifier
            request_info: Optional request information

        Returns:
            dict: Mapping of placeholder names to values
        """
        values = {
            "session_id": profile_id,  # Use profile_id as session identifier
        }

        if not request_info:
            return values

        if request_info.country:
            values["country"] = request_info.country.lower()
        if request_info.state:
            values["state"] = request_info.state.lower().replace(" ", "_")
        if request_info.city:
            values["city"] = request_info.city.lower().replace(" ", "_")
        if request_info.postal_code:
            values["postal_code"] = request_info.postal_code

        return values

    def _build_params(self, template: str, values: dict[str, Any]) -> str:
        """Build params string by only including segments with actual values.

        Splits template by placeholders and only joins segments that have values.

        Examples:
        - Template: 'cc-{country}-city-{city}', values: {'country': 'us'} -> 'cc-us'
        - Template: 'cc-{country}-city-{city}', values: {} -> ''
        - Template: 'state-us_{state}', values: {'state': 'ca'} -> 'state-us_ca'
        - Template: 'state-us_{state}', values: {} -> ''

        Args:
            template: Template string with {placeholders}
            values: Mapping of placeholder names to values

        Returns:
            str: Params with only segments that have values, or empty string
        """
        # Split by placeholders to get segments
        # We'll rebuild by only including segments where we have values
        parts: list[str] = []
        current = template

        # Find all placeholders in order
        placeholders: list[str] = re.findall(r"\{([^}]+)\}", template)

        for placeholder in placeholders:
            # Split on this placeholder
            before, _, after = current.partition(f"{{{placeholder}}}")

            # If we have a value for this placeholder, include the segment
            if placeholder in values:
                parts.append(before + str(values[placeholder]))

            current = after

        # Add any remaining text
        if current:
            parts.append(current)

        result = "".join(parts)

        # Clean up separators at start/end
        result = result.strip("-_")

        return result


def load_proxy_configs_from_env(env_dict: dict[str, str]) -> dict[str, ProxyConfig]:
    """Load all proxy configurations from environment variables.

    Expected format:
        PROXY_0_URL=http://user:pass@proxy.example.com:8888
        PROXY_0_PARAMS_TEMPLATE=country-{country}-sessionid-{session_id}

        PROXY_1_URL=http://user2:pass2@proxy2.example.com:8000
        PROXY_1_PARAMS_TEMPLATE=session-{session_id}-state-{state}

    Args:
        env_dict: Environment variables dictionary

    Returns:
        dict: Mapping of proxy identifiers (e.g., 'proxy-0') to ProxyConfig objects
    """
    configs: dict[str, ProxyConfig] = {}

    # Find all proxy indices by looking for PROXY_X_URL
    indices: set[int] = set()
    for key in env_dict.keys():
        if key.startswith("PROXY_") and "_URL" in key:
            # Extract index from PROXY_{INDEX}_URL
            parts = key.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                indices.add(int(parts[1]))

    # Load configuration for each index
    for idx in sorted(indices):
        url = env_dict.get(f"PROXY_{idx}_URL")
        if not url:
            continue

        params_template = env_dict.get(f"PROXY_{idx}_PARAMS_TEMPLATE")

        config = ProxyConfig(
            url=url,
            params_template=params_template,
        )

        proxy_key = f"proxy-{idx}"
        configs[proxy_key] = config
        logger.info(f"Loaded proxy configuration for {proxy_key}: url={config.masked_url}")

    return configs
