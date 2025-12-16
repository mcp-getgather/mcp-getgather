"""GetGather package initialization."""

# Initialize logging as early as possible
try:
    from getgather.config import settings
    from getgather.logs import setup_logging

    setup_logging(level=settings.LOG_LEVEL)
except Exception:
    # If settings aren't available yet, setup_logging will be called from startup
    pass
