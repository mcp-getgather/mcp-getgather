import logging

import logfire
import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from getgather.config import settings
from getgather.logs import logger


async def startup(app: FastAPI | None = None):
    logger.info("Setting up Logfire and Sentry with LOG_LEVEL=%s", settings.LOG_LEVEL)

    # Configure Logfire
    logfire.configure(
        service_name="mcp-getgather",
        send_to_logfire="if-token-present",
        token=settings.LOGFIRE_TOKEN or None,
        environment=settings.ENVIRONMENT,
        distributed_tracing=True,
        code_source=logfire.CodeSource(
            repository="https://github.com/mcp-getgather/mcp-getgather", revision="main"
        ),
        scrubbing=False,
        console=False,
    )

    # Add LogfireLoggingHandler to all existing loggers
    logfire_handler = logfire.LogfireLoggingHandler()
    root_logger = logging.getLogger()
    root_logger.addHandler(logfire_handler)

    # Instrument FastAPI if app is provided
    if app:
        logfire.instrument_fastapi(app, capture_headers=True)
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
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
