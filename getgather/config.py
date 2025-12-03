from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from getgather.browser.proxy_loader import load_proxy_configs
from getgather.browser.proxy_types import ProxyConfig
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
    LOGFIRE_TOKEN: str = ""

    DATA_DIR: str = ""

    # Logging
    SENTRY_DSN: str = ""

    # Browser Package Settings
    HEADLESS: bool = False
    SHOULD_BLOCK_UNWANTED_RESOURCES: bool = True

    BROWSER_TIMEOUT: int = 30_000

    # Default Proxy Type (optional - e.g., "proxy-0", "proxy-1")
    # If not set, no proxy will be used unless specified via x-proxy-type header
    DEFAULT_PROXY_TYPE: str = ""

    # RRWeb Recording Settings
    ENABLE_RRWEB_RECORDING: bool = False
    RRWEB_SCRIPT_URL: str = (
        "https://cdn.jsdelivr.net/npm/rrweb@2.0.0-alpha.14/dist/record/rrweb-record.min.js"
    )
    RRWEB_MASK_ALL_INPUTS: bool = True

    HOSTNAME: str = ""

    # Max session age, in minutes
    BROWSER_SESSION_AGE: int = 60

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

    @property
    def proxy_configs(self) -> dict[str, ProxyConfig]:
        """Load proxy configurations from YAML file or environment variable (cached).

        Returns:
            dict: Mapping of proxy identifiers (e.g., 'proxy-0') to ProxyConfig objects
        """
        return load_proxy_configs()


settings = Settings()
