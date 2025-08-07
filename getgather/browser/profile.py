from __future__ import annotations

import shutil
from pathlib import Path

import sentry_sdk
from nanoid import generate
from patchright.async_api import BrowserType, ViewportSize
from pydantic import ConfigDict, Field, model_validator

from getgather.browser.freezable_model import FreezableModel
from getgather.config import settings
from getgather.logs import logger

# avoid similar looking characters: number 0 and letter O, number 1 and letter L
FRIENDLY_CHARS: str = "23456789abcdefghijkmnpqrstuvwxyz"


class BrowserProfile(FreezableModel):
    screen_width: int = 1920
    screen_height: int = 1080

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: generate(FRIENDLY_CHARS, 6))

    @model_validator(mode="after")
    def setup_sentry(self):
        sentry_sdk.set_tag("profile_id", self.id)
        return self

    def profile_dir(self, profile_id: str) -> Path:
        return settings.profiles_dir / profile_id

    def get_viewport_config(self) -> ViewportSize:
        """Create viewport configuration from screen dimensions."""
        return ViewportSize(width=self.screen_width, height=self.screen_height)

    async def launch(self, profile_id: str, browser_type: BrowserType):
        logger.info(
            f"Launching local browser {browser_type.name} with user_data_dir:"
            f" file://{self.profile_dir(profile_id)}",
            extra={"profile_id": profile_id},
        )
        proxy = None
        # Get viewport configuration from parent class
        viewport_config = self.get_viewport_config()

        return await browser_type.launch_persistent_context(
            user_data_dir=str(self.profile_dir(profile_id)),
            headless=False,
            viewport=viewport_config,
            proxy=proxy,
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
