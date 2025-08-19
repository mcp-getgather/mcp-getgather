from pathlib import Path

from pydantic import field_validator
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
    def database_path(self) -> Path:
        """Path to SQLite database file in the main data directory."""
        data_dir = PROJECT_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "getgather.db"

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


settings = Settings()
