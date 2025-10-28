import json
import logging
from typing import Any, Literal

from rich.logging import RichHandler

LOGGER_NAME = "getgather"


def extract_extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    """Extract custom extra fields from a LogRecord, excluding standard attributes."""
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

    return {
        k: v
        for k, v in record.__dict__.items()
        if k not in standard_attrs and not k.startswith("_")
    }


def setup_logging_level(level: str = "INFO"):
    # app logger to the level
    logging.getLogger(LOGGER_NAME).setLevel(level)


def setup_logging_format(format: Literal["rich", "json"] = "rich"):
    if format == "rich":
        handler = _setup_rich()
    else:
        handler = _setup_json()

    # reconfigure uvicorn.error, uvicorn.access and fastapi
    for name in ["uvicorn.error", "uvicorn.access", "fastapi"]:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False

    # Configure the root logger to INFO level
    logging.basicConfig(level="INFO", format="%(message)s", datefmt="[%X]", handlers=[handler])


def _setup_rich():
    rich_handler = RichHandler(
        rich_tracebacks=True, markup=True, show_time=True, show_level=True, show_path=False
    )
    rich_handler.setFormatter(StructuredFormatter())
    return rich_handler


def _setup_json():
    """Setup JSON logging format."""
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(JsonFormatter())

    return json_handler


logger = logging.getLogger(LOGGER_NAME)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that handles extra fields in log records."""

    def format(self, record: logging.LogRecord) -> str:
        # Get the base formatted message
        base_msg = super().format(record)

        extras = extract_extra_fields(record)

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


class JsonFormatter(logging.Formatter):
    """JSON formatter that outputs structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        # Create the base log entry
        log_entry = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        log_entry.update(extract_extra_fields(record))

        return json.dumps(log_entry, default=str)


# The StructuredFormatter handles extra fields automatically when using logger.info(msg, extra={...})
