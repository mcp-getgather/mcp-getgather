"""Proxy configuration builder with template-based dynamic parameter replacement.

This module provides a flexible system for building proxy configurations from
environment variable templates, supporting multiple proxy providers with different
URL formats and parameter naming conventions.
"""

from typing import Any

from getgather.api.types import RequestInfo
from getgather.logs import logger


class ProxyConfig:
    """Represents a configured proxy from environment variables."""

    def __init__(
        self,
        proxy_type: str,
        url: str | None = None,
        base_username: str | None = None,
        params_template: str | None = None,
        password: str | None = None,
    ):
        """Initialize proxy configuration.

        Args:
            proxy_type: Type identifier (e.g., 'none', 'proxy-1', 'proxy-2')
            url: Proxy server URL (e.g., 'http://proxy.io:7777')
            base_username: Static base username (e.g., 'user-mcp')
            params_template: Dynamic parameters with placeholders (e.g., 'cc-{country}-sessid-{session_id}')
            password: Proxy password
        """
        self.proxy_type = proxy_type
        self.url = url
        self.base_username = base_username
        self.params_template = params_template
        self.password = password

    def is_none(self) -> bool:
        """Check if this is a 'no proxy' configuration."""
        return self.proxy_type == "none"

    def build(
        self, profile_id: str, request_info: RequestInfo | None = None
    ) -> dict[str, str] | None:
        """Build proxy configuration dict with dynamic parameter replacement.

        Args:
            profile_id: Profile ID to use as session identifier
            request_info: Optional request information with location data

        Returns:
            dict: Proxy configuration with server, username, password
            None: If proxy type is 'none' or configuration is invalid
        """
        if self.is_none():
            logger.info("Proxy type is 'none', skipping proxy configuration")
            return None

        if not self.url:
            logger.warning("Proxy configuration incomplete: no URL provided")
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
            "server": self.url,
        }
        if username:
            result["username"] = username
        if self.password:
            result["password"] = self.password

        logger.info(
            f"Built proxy config - server: {self.url}, username: {username}, "
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
        import re

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

    Args:
        env_dict: Environment variables dictionary

    Returns:
        dict: Mapping of proxy identifiers (e.g., 'proxy-0') to ProxyConfig objects
    """
    configs: dict[str, ProxyConfig] = {}

    # Find all proxy indices
    indices: set[int] = set()
    for key in env_dict.keys():
        if key.startswith("PROXY_") and "_TYPE" in key:
            # Extract index from PROXY_{INDEX}_TYPE
            parts = key.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                indices.add(int(parts[1]))

    # Load configuration for each index
    for idx in sorted(indices):
        proxy_type = env_dict.get(f"PROXY_{idx}_TYPE")
        if not proxy_type:
            continue

        url = env_dict.get(f"PROXY_{idx}_URL")
        base_username = env_dict.get(f"PROXY_{idx}_BASE_USERNAME")
        params_template = env_dict.get(f"PROXY_{idx}_PARAMS_TEMPLATE")
        password = env_dict.get(f"PROXY_{idx}_PASSWORD")

        config = ProxyConfig(
            proxy_type=proxy_type,
            url=url,
            base_username=base_username,
            params_template=params_template,
            password=password,
        )

        proxy_key = f"proxy-{idx}"
        configs[proxy_key] = config
        logger.info(f"Loaded proxy configuration for {proxy_key}: type={proxy_type}")

    return configs
