from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Any, Literal, Self, get_args

import sentry_sdk
from nanoid import generate
from patchright.async_api import BrowserType, ViewportSize
from pydantic import AfterValidator, BaseModel, ConfigDict, PrivateAttr, model_validator

from getgather.browser.freezable_model import FreezableModel
from getgather.config import settings
from getgather.logs import logger

# avoid similar looking characters: number 0 and letter O, number 1 and letter L
FRIENDLY_CHARS: str = "23456789abcdefghijkmnpqrstuvwxyz"

BROWSER_APP = Literal["chromium", "firefox", "webkit"]
BROWSER_CHANNEL = Literal["chrome", "msedge"]


class BrowserProfile(FreezableModel):
    model_config = ConfigDict(extra="forbid")

    _id: str = PrivateAttr(default="")  # _id will be lazily initialized when session starts
    config: BrowserConfig

    async def init(self):
        """Lazy initialization of profile ID when session starts."""
        if self._id:  # Profile already initialized
            return

        self._id = generate(FRIENDLY_CHARS, 6)
        sentry_sdk.set_tag("profile_id", self._id)
        self.freeze()

    @property
    def profile_id(self) -> str:
        if not self._id:
            raise ValueError("Browser session not initialized")
        return self._id

    @classmethod
    def get(cls, profile_id: str) -> BrowserProfile:
        """Load an existing browser profile from a profile ID."""
        config = BrowserConfig.from_profile_id(profile_id)
        profile = cls(config=config)
        profile._id = profile_id
        return profile

    @classmethod
    def create(cls, config_data: dict[str, Any]) -> BrowserProfile:
        """Create a new browser profile."""
        config = BrowserConfig(**config_data)
        return cls(config=config)

    def profile_dir(self) -> Path:
        return self.config.profile_dir(self._id)


def browser_validator_factory(choices: tuple[str]) -> AfterValidator:
    def browser_validator(v: str) -> str:
        if v not in choices:
            raise ValueError(f"Invalid browser type: {v}")
        return v

    return AfterValidator(browser_validator)


class BrowserConfig(BaseModel):
    browser: Annotated[str, browser_validator_factory(get_args(BROWSER_APP))]
    channel: BROWSER_CHANNEL | None = None

    screen_width: int = 1920
    screen_height: int = 1080

    model_config = ConfigDict(frozen=True)

    def get_viewport_config(self) -> ViewportSize:
        """Create viewport configuration from screen dimensions."""
        return ViewportSize(width=self.screen_width, height=self.screen_height)

    @model_validator(mode="after")
    def validate_config(self):
        if self.channel and self.browser != "chromium":
            raise ValueError("Channel is only supported for chromium")

        return self

    @classmethod
    def from_profile_id(cls, profile_id: str) -> Self:
        dirs = list(settings.profiles_dir.glob(f"*_{profile_id}"))
        if len(dirs) == 0:
            raise ValueError(f"Profile {profile_id} not found")
        if len(dirs) > 1:
            raise ValueError(f"Invalid profile ID: {profile_id}")
        profile_dir = dirs[0]
        browser_type = profile_dir.name.split("_")[0]
        return cls(browser=browser_type)

    def profile_dir(self, profile_id: str) -> Path:
        return settings.profiles_dir / f"{self.browser}_{profile_id}"

    async def launch(self, profile_id: str, browser_type: BrowserType):
        channel_message = f" in channel: {self.channel}" if self.channel else ""
        logger.info(
            f"Launching local browser {browser_type.name} with user_data_dir:",
            extra={"profile_id": profile_id},
        )
        logger.info(
            f"file://{self.profile_dir(profile_id)}{channel_message}",
            extra={"profile_id": profile_id},
        )
        proxy = None
        # Get viewport configuration from parent class
        viewport_config = self.get_viewport_config()

        if self.browser == "firefox":
            firefox_user_prefs: dict[str, str | float | bool] = {
                "dom.webdriver.enabled": False,
                "privacy.resistFingerprinting": True,
            }
            return await browser_type.launch_persistent_context(
                user_data_dir=str(self.profile_dir(profile_id)),
                headless=settings.HEADLESS,
                firefox_user_prefs=firefox_user_prefs,
                viewport=viewport_config,
                proxy=proxy,  # type: ignore
            )
        elif self.browser == "chromium":
            return await browser_type.launch_persistent_context(
                user_data_dir=str(self.profile_dir(profile_id)),
                headless=settings.HEADLESS,
                channel=self.channel,
                viewport=viewport_config,
                proxy=proxy,  # type: ignore
            )
        else:
            return await browser_type.launch_persistent_context(
                user_data_dir=str(self.profile_dir(profile_id)),
                headless=settings.HEADLESS,
                viewport=viewport_config,
                proxy=proxy,  # type: ignore
            )

    def cleanup(self, profile_id: str):
        user_data_dir = self.profile_dir(profile_id)
        logger.info(
            f"Removing extra stuff in file://{user_data_dir}...",
            extra={
                "profile_id": profile_id,
            },
        )
        for directory in [
            "Default/DawnGraphiteCache",
            "Default/DawnWebGPUCache",
            "Default/GPUCache",
            "Default/Code Cache",
            "Default/Cache",
            "GraphiteDawnCache",
            "GrShaderCache",
            "ShaderCache",
            "Subresource Filter",
            "segmentation_platform",
        ]:
            path = user_data_dir / directory

            if path.exists():
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    logger.warning(f"Failed to remove {directory}: {e}")
