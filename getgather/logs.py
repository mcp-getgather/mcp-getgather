import logging

from rich.logging import RichHandler

LOGGER_NAME = "getgather"


def setup_logging(level: str = "INFO"):
    rich_handler = RichHandler(rich_tracebacks=True, markup=True)

    # reconfigure uvicorn.error, uvicorn.access and fastapi
    for name in ["uvicorn.error", "uvicorn.access", "fastapi"]:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.addHandler(rich_handler)
        logger.propagate = False

    # Configure the root logger to INFO level, and app logger to the level specified in the .env
    logging.basicConfig(level="INFO", format="%(message)s", datefmt="[%X]", handlers=[rich_handler])
    logging.getLogger(LOGGER_NAME).setLevel(level)


logger = logging.getLogger(LOGGER_NAME)
