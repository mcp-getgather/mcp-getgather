import contextvars
import logging
from typing import Any

from rich.logging import RichHandler

LOGGER_NAME = "getgather"

# Context variable to store logging context (session IDs, etc.)
logging_context: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "logging_context", default={}
)


def setup_logging(level: str = "INFO"):
    rich_handler = RichHandler(
        rich_tracebacks=True, markup=True, show_time=True, show_level=True, show_path=False
    )
    rich_handler.setFormatter(StructuredFormatter())

    # reconfigure uvicorn.error, uvicorn.access and fastapi
    for name in ["uvicorn.error", "uvicorn.access", "fastapi"]:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.addHandler(rich_handler)
        logger.propagate = False

    # Configure the root logger to INFO level, and app logger to the level
    # specified in the .env
    logging.basicConfig(level="INFO", format="%(message)s", datefmt="[%X]", handlers=[rich_handler])
    logging.getLogger(LOGGER_NAME).setLevel(level)


class ContextLogger(logging.Logger):
    """Logger that automatically includes context variables in all log messages."""

    def append_context(self, key: str, value: Any):
        """Add key-value pair to the current context."""
        current = logging_context.get()
        logging_context.set({**current, key: value})

    def set_context(self, **kwargs):
        """Set multiple context values at once."""
        current = logging_context.get()
        logging_context.set({**current, **kwargs})

    def clear_context(self):
        """Clear the logging context."""
        logging_context.set({})

    def _wrap_extra(self, extra):
        """Merge context vars with provided extra dict."""
        context = logging_context.get()
        safe_extra = extra or {}
        return {**context, **safe_extra}

    def debug(self, msg, *args, extra=None, **kwargs):
        super().debug(msg, *args, extra=self._wrap_extra(extra), **kwargs)

    def info(self, msg, *args, extra=None, **kwargs):
        super().info(msg, *args, extra=self._wrap_extra(extra), **kwargs)

    def warning(self, msg, *args, extra=None, **kwargs):
        super().warning(msg, *args, extra=self._wrap_extra(extra), **kwargs)

    def error(self, msg, *args, extra=None, **kwargs):
        super().error(msg, *args, extra=self._wrap_extra(extra), **kwargs)

    def critical(self, msg, *args, extra=None, **kwargs):
        super().critical(msg, *args, extra=self._wrap_extra(extra), **kwargs)


# Set custom logger class and create logger instance
logging.setLoggerClass(ContextLogger)
logger: ContextLogger = logging.getLogger(LOGGER_NAME)  # type: ignore


class StructuredFormatter(logging.Formatter):
    """Custom formatter that handles extra fields in log records."""

    def format(self, record: logging.LogRecord) -> str:
        # Get the base formatted message
        base_msg = super().format(record)

        # Extract extra fields (anything not in the standard LogRecord attributes)
        # Include all possible LogRecord attributes to avoid conflicts
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "exc_info",
            "exc_text",
            "stack_info",
            "message",
            "asctime",
            "taskName",
        }

        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith("_")
        }

        if extras:
            # Color code the extras section based on log level
            level_colors = {
                "DEBUG": "dim blue",
                "INFO": "cyan",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold red",
            }
            color = level_colors.get(record.levelname, "white")

            # Always use multi-line format for better readability
            extras_lines: list[str] = []
            for key, value in extras.items():
                value_any: Any = value  # Type annotation for unknown LogRecord fields

                # Handle complex values like dicts
                if isinstance(value_any, dict):
                    if len(value_any) <= 3:  # Small dicts inline  # type: ignore[arg-type]
                        value_str = str(value_any)  # type: ignore[arg-type]
                    else:  # Large dicts formatted
                        dict_items = [f"{k}={v}" for k, v in value_any.items()]  # type: ignore[misc]
                        value_str = "{\n      " + ",\n      ".join(dict_items) + "\n    }"
                elif isinstance(value_any, (list, tuple)) and len(value_any) > 3:  # type: ignore[arg-type]
                    # Format long lists/tuples nicely
                    items = [str(item) for item in value_any]  # type: ignore[misc]
                    value_str = "[\n      " + ",\n      ".join(items) + "\n    }"
                else:
                    value_str = str(value_any)  # type: ignore[arg-type]

                extras_lines.append(f"[{color}]    {key}:[/{color}] {value_str}")

            extras_str = "\n" + "\n".join(extras_lines) + "\n"
            return f"{base_msg}\n{extras_str}"

        return base_msg


# The StructuredFormatter handles extra fields automatically when using logger.info(msg, extra={...})
