from __future__ import annotations

import shutil
from pathlib import Path

import sentry_sdk
from nanoid import generate
from pydantic import ConfigDict, Field, model_validator
from stagehand import Stagehand

from getgather.browser.freezable_model import FreezableModel
from getgather.config import settings
from getgather.logs import logger

# Note: These imports are commented out as they're not used in the Stagehand implementation
# from getgather.api.types import request_info
# from getgather.browser.proxy import setup_proxy

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

    def get_viewport_config(self) -> dict[str, int]:
        """Create viewport configuration from screen dimensions."""
        return {"width": self.screen_width, "height": self.screen_height}

    async def launch(self, profile_id: str) -> Stagehand:
        logger.info(
            f"Launching local browser with Stagehand using user_data_dir:"
            f" file://{self.profile_dir(profile_id)}",
            extra={"profile_id": profile_id},
        )

        # Note: Stagehand handles proxy and viewport configuration differently than patchright
        # These might need to be configured through Stagehand's browser page after initialization
        # proxy = await setup_proxy(profile_id, request_info.get())
        # viewport_config = self.get_viewport_config()

        # Add macOS-specific launch arguments to prevent crashes
        args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-field-trial-config",
            "--disable-ipc-flooding-protection",
        ]

        # Prepare Stagehand launch options
        launch_options = {
            "user_data_dir": str(self.profile_dir(profile_id)),
            "headless": settings.HEADLESS,
            "args": args,
        }

        # Initialize Stagehand with the configured options
        stagehand = Stagehand(
            env="LOCAL",
            headless=settings.HEADLESS,
            local_browser_launch_options=launch_options,
        )

        await stagehand.init()
        return stagehand

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
