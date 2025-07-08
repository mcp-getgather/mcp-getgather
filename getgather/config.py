from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from getgather.logs import logger

PROJECT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env", env_ignore_empty=True, extra="ignore"
    )
    ENVIRONMENT: str = "local"
    APP_NAME: str = "getgather-local"
    LOG_LEVEL: str = "INFO"

    @field_validator("LOG_LEVEL", mode="after")
    @classmethod
    def set_log_level(cls, v: str) -> str:
        logger.setLevel(v)
        return v


settings = Settings()