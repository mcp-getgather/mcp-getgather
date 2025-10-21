import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

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
            LoggingIntegration(level=logging.getLevelNamesMapping()[settings.LOG_LEVEL]),
            StarletteIntegration(
                transaction_style="endpoint",
                failed_request_status_codes={403, *range(500, 599)},
            ),
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes={403, *range(500, 599)},
            ),
        ],  # capture logs in sentry above INFO level
        send_default_pii=True,
    )
