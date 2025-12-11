import logging

import logfire
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from getgather.config import settings
from getgather.logs import logger


async def startup():
    logger.info("Setting up Sentry with LOG_LEVEL=%s", settings.LOG_LEVEL)
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
    )
    logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()], level=logging.INFO)
