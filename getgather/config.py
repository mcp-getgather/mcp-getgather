import functools
from pathlib import Path
from typing import Awaitable, Callable, ParamSpec, TypeVar

from fastapi import HTTPException
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from getgather.logs import logger, setup_logging

PROJECT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env", env_ignore_empty=True, extra="ignore"
    )
    ENVIRONMENT: str = "local"
    APP_NAME: str = "getgather-local"
    LOG_LEVEL: str = "INFO"
    GIT_REV: str = ""

    # Logging
    SENTRY_DSN: str = ""

    # Browser Package Settings
    PROFILES_DIR: str = ""
    BUNDLES_DIR: str = ""
    SCREENSHOTS_DIR: str = ""
    HEADLESS: bool = False
    SHOULD_BLOCK_UNWANTED_RESOURCES: bool = False

    # Browser-use settings
    BROWSER_USE_MODEL: str = "o4-mini"
    OPENAI_API_KEY: str = ""

    # Proxy Settings
    BROWSER_HTTP_PROXY: str = ""
    BROWSER_HTTP_PROXY_PASSWORD: str = ""

    # Websites with Content Security Policy
    CSP_WEBSITES: list[str] = ["*.bbc.com"]

    # RRWeb Recording Settings
    ENABLE_RRWEB_RECORDING: bool = True
    RRWEB_SCRIPT_URL: str = (
        "https://cdn.jsdelivr.net/npm/rrweb@2.0.0-alpha.14/dist/record/rrweb-record.min.js"
    )
    RRWEB_MASK_ALL_INPUTS: bool = True

    MULTI_USER_ENABLED: bool = False

    SERVER_ORIGIN: str = "http://localhost:23456"

    OAUTH_GITHUB_CLIENT_ID: str = ""
    OAUTH_GITHUB_CLIENT_SECRET: str = ""
    OAUTH_GITHUB_REDIRECT_PATH: str = "/auth/github/callback"

    @property
    def brand_spec_dir(self) -> Path:
        return PROJECT_DIR / "getgather" / "connectors" / "brand_specs"

    @property
    def test_brand_spec_dir(self) -> Path:
        return PROJECT_DIR / "tests" / "connectors" / "brand_specs"

    @property
    def bundles_dir(self) -> Path:
        return Path(self.BUNDLES_DIR) if self.BUNDLES_DIR else PROJECT_DIR / "data" / "bundles"

    @property
    def screenshots_dir(self) -> Path:
        dir = (
            Path(self.SCREENSHOTS_DIR)
            if self.SCREENSHOTS_DIR
            else PROJECT_DIR / "data" / "screenshots"
        )
        if not dir.exists():
            dir.mkdir(parents=True)
        return dir

    @property
    def profiles_dir(self) -> Path:
        path = (
            Path(self.PROFILES_DIR).resolve()
            if self.PROFILES_DIR
            else PROJECT_DIR / "data/profiles"
        )
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def persistent_store_dir(self) -> Path:
        path = PROJECT_DIR / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def db_json_path(self) -> Path:
        """Path to general database JSON file in the main data directory."""
        data_dir = PROJECT_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "db.json"

    @property
    def recordings_dir(self) -> Path:
        """Path to recordings directory for per-activity files."""
        recordings_dir = PROJECT_DIR / "data" / "recordings"
        recordings_dir.mkdir(parents=True, exist_ok=True)
        return recordings_dir

    @field_validator("LOG_LEVEL", mode="after")
    @classmethod
    def set_log_level(cls, v: str) -> str:
        setup_logging(v)
        return v

    @field_validator("SENTRY_DSN", mode="after")
    @classmethod
    def validate_sentry_dsn(cls, v: str) -> str:
        if not v:
            logger.warning("SENTRY_DSN is not set, logging will not be captured in Sentry.")
        return v

    @model_validator(mode="after")
    def validate_multi_user_enabled(self) -> "Settings":
        if self.MULTI_USER_ENABLED:
            auth_enabled = all([
                self.SERVER_ORIGIN,
                self.OAUTH_GITHUB_CLIENT_ID,
                self.OAUTH_GITHUB_CLIENT_SECRET,
                self.OAUTH_GITHUB_REDIRECT_PATH,
            ])
            if not auth_enabled:
                raise ValueError("MCP auth must be enabled in MULTI_USER mode.")
        logger.info(
            f"Multi-user mode and MCP auth are {'enabled' if self.MULTI_USER_ENABLED else 'disabled'}."
        )
        return self

    @property
    def mcp_auth_provider(self) -> str:
        """Only supports GitHub for now."""
        return "github"


settings = Settings()


P = ParamSpec("P")
T = TypeVar("T")


def disabled_if_multi_user(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """Disable the route if multi-user is enabled."""

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if settings.MULTI_USER_ENABLED:
            raise HTTPException(
                status_code=404, detail=f"Route {func.__name__} is disabled in multi-user mode."
            )
        return await func(*args, **kwargs)

    return wrapper
