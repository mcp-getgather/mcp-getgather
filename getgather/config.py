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

    DATA_DIR: str = ""

    # Logging
    SENTRY_DSN: str = ""

    # Browser Package Settings
    HEADLESS: bool = False
    SHOULD_BLOCK_UNWANTED_RESOURCES: bool = False

    # Browser-use settings
    BROWSER_USE_MODEL: str = "o4-mini"
    OPENAI_API_KEY: str = ""

    BROWSER_TIMEOUT: int = 30_000

    # Proxy Settings
    BROWSER_PROXY: str = ""

    # RRWeb Recording Settings
    ENABLE_RRWEB_RECORDING: bool = False
    RRWEB_SCRIPT_URL: str = (
        "https://cdn.jsdelivr.net/npm/rrweb@2.0.0-alpha.14/dist/record/rrweb-record.min.js"
    )
    RRWEB_MASK_ALL_INPUTS: bool = True

    HOSTNAME: str = ""

    @property
    def brand_spec_dir(self) -> Path:
        return PROJECT_DIR / "getgather" / "connectors" / "brand_specs"

    @property
    def test_brand_spec_dir(self) -> Path:
        return PROJECT_DIR / "tests" / "connectors" / "brand_specs"

    @property
    def data_dir(self) -> Path:
        path = Path(self.DATA_DIR).resolve() if self.DATA_DIR else PROJECT_DIR / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def bundles_dir(self) -> Path:
        path = self.data_dir / "bundles"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def screenshots_dir(self) -> Path:
        path = self.data_dir / "screenshots"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def profiles_dir(self) -> Path:
        path = self.data_dir / "profiles"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def persistent_store_dir(self) -> Path:
        path = self.data_dir / "store"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def recordings_dir(self) -> Path:
        """Path to recordings directory for per-activity files."""
        path = self.data_dir / "recordings"
        path.mkdir(parents=True, exist_ok=True)
        return path

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
