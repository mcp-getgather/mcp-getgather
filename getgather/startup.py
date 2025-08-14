import base64
import logging
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from getgather.config import settings
from getgather.logs import logger


async def startup():
    logger.info("Setting up Sentry with LOG_LEVEL=%s", settings.LOG_LEVEL)

    # Configure Sentry with proxy if needed
    sentry_config: dict[str, Any] = {
        "dsn": settings.SENTRY_DSN,
        "_experiments": {
            "enable_logs": True,
        },
        "environment": settings.ENVIRONMENT,
        "integrations": [
            LoggingIntegration(level=logging.getLevelNamesMapping()[settings.LOG_LEVEL])
        ],  # capture logs in sentry above INFO level
        "send_default_pii": True,
    }

    # Add proxy configuration if proxy settings are provided
    if settings.HTTP_PROXY:
        # Set the proxy server URL (without credentials)
        sentry_config["http_proxy"] = settings.HTTP_PROXY
        sentry_config["https_proxy"] = settings.HTTP_PROXY

        # Add authentication headers if password is provided
        if settings.HTTP_PROXY_PASSWORD:
            # Create Basic Auth header for proxy authentication
            auth_string = f"sentry:{settings.HTTP_PROXY_PASSWORD}"
            auth_bytes = auth_string.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

            sentry_config["proxy_headers"] = {"Proxy-Authorization": f"Basic {auth_b64}"}
            logger.info("Configuring Sentry with authenticated proxy: %s", settings.HTTP_PROXY)
        else:
            logger.info("Configuring Sentry with unauthenticated proxy: %s", settings.HTTP_PROXY)

    sentry_sdk.init(**sentry_config)
