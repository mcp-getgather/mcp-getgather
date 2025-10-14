import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from getgather.browser.resource_blocker import resource_blocker
from getgather.config import settings
from getgather.logs import logger


async def startup():
    logger.info("Setting up Sentry with LOG_LEVEL=%s", settings.LOG_LEVEL)
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        _experiments={
            "enable_logs": True,
        },
        environment=settings.ENVIRONMENT,
        integrations=[
            LoggingIntegration(level=logging.getLevelNamesMapping()[settings.LOG_LEVEL])
        ],  # capture logs in sentry above INFO level
        send_default_pii=True,
    )

    # Preload blocklists on startup
    if settings.SHOULD_BLOCK_UNWANTED_RESOURCES:
        logger.info("Preloading blocklists on startup...")
        try:
            await resource_blocker.load()
            logger.info("Blocklists preloaded successfully")
        except Exception as exc:
            logger.error(f"Failed to preload blocklists: {exc}")
