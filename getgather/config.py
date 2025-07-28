from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from getgather.logs import logger

PROJECT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env", env_ignore_empty=True, extra="ignore"
    )
    ENVIRONMENT: str = "local"
    APP_NAME: str = "getgather-local"
    LOG_LEVEL: str = "INFO"

    # Logging
    SENTRY_DSN: str = ""

    # Browser Package Settings
    PROFILES_DIR: str = ""
    BUNDLES_DIR: str = ""
    SCREENSHOTS_DIR: str = ""
    HEADLESS: bool = False
    
    # Credentials
    GOODREADS_EMAIL: str = ""
    GOODREADS_PASSWORD: str = ""
    EBIRD_USERNAME: str = ""
    EBIRD_PASSWORD: str = ""
    BBC_EMAIL: str = ""
    BBC_PASSWORD: str = ""
    ZILLOW_EMAIL: str = ""
    ZILLOW_PASSWORD: str = ""

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

    @field_validator("LOG_LEVEL", mode="after")
    @classmethod
    def set_log_level(cls, v: str) -> str:
        logger.setLevel(v)
        return v

    def validate_sentry_dsn(self) -> Self:
        if not self.SENTRY_DSN:
            from getgather.logs import logger

            logger.warning("SENTRY_DSN is not set, logging will not be captured in Sentry.")
        return self


settings = Settings()
settings.validate_sentry_dsn()  # normal Pydantic validator would cause circular import due to logger
