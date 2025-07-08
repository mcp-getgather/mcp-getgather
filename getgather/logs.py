import logging
import shutil

from rich.console import Console
from rich.logging import RichHandler

# suppress noisy logs
for lib in ["urllib3"]:
    logging.getLogger(lib).setLevel(logging.WARNING)

rich_handler = RichHandler(
    rich_tracebacks=True,
    markup=True,
    console=Console(width=shutil.get_terminal_size().columns - 1),  # avoid line wrapping
)

# reconfigure uvicorn.error, uvicorn.access and fastapi
for name in ["uvicorn.error", "uvicorn.access", "fastapi"]:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.addHandler(rich_handler)
    logger.propagate = False


logging.basicConfig(level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[rich_handler])


logger = logging.getLogger()
