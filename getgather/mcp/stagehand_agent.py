"""Stagehand agent implementation with browser profile persistence. By default, it uses Playwright to start a browser."""

from typing import Any, Protocol

from pydantic import BaseModel
from stagehand import Stagehand, default_config
from stagehand.schemas import (
    ActResult,
    ExtractOptions,
    ExtractResult,
    ObserveOptions,
    ObserveResult,
)

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.config import settings
from getgather.logs import logger
from getgather.mcp.brand_state import brand_state_manager
from getgather.mcp.shared import get_mcp_brand_id


class StagehandPage(Protocol):
    """Protocol for page operations."""

    async def goto(
        self,
        url: str,
        *,
        referer: str | None = None,
        timeout: int | None = None,
        wait_until: str | None = None,
    ) -> None:
        """Navigate to URL with optional referer, timeout, and wait condition."""
        ...

    async def act(
        self,
        action_or_result: str | ObserveResult | dict[str, Any],
        **kwargs: Any,
    ) -> ActResult:
        """Execute an natural language action or apply a pre-observed action."""
        ...

    async def observe(
        self,
        options_or_instruction: str | ObserveOptions | None = None,
        **kwargs: Any,
    ) -> list[ObserveResult]:
        """Make an natural language observation of page elements."""
        ...

    async def extract(
        self,
        options_or_instruction: str | ExtractOptions | None = None,
        *,
        schema: type[BaseModel] | None = None,
        **kwargs: Any,
    ) -> ExtractResult:
        """Extract data from page using natural language."""
        ...


# Currently, we only need the page property and close method
class StagehandAgent(Protocol):
    """Minimal interface for Stagehand agent."""

    @property
    def page(self) -> StagehandPage:
        """Get current page."""
        ...

    async def close(self) -> None:
        """Close agent and cleanup."""
        ...


# This wrapper is used to provide a minimal interface for the Stagehand agent
class StagehandAgentWrapper:
    """Minimal wrapper around Stagehand."""

    def __init__(self, stagehand: Stagehand):
        self._stagehand = stagehand

    @property
    def page(self) -> StagehandPage:
        """Get current page or raise if not set."""
        if not self._stagehand.page:
            raise ValueError("Page is not set")
        return self._stagehand.page

    async def close(self) -> None:
        """Close and cleanup."""
        await self._stagehand.close()


async def _get_user_data_dir() -> str | None:
    """Get browser profile directory for session persistence."""
    try:
        # the implementation is similar to with_brand_browser_session in shared.py
        # howerver, it doesn't use the browser session directly, but rather uses stagehand's browser session
        brand_id = get_mcp_brand_id()
        if not brand_id:
            raise ValueError("Brand ID is not set")

        brand_state = brand_state_manager.get(brand_id)
        profile_id = (
            brand_state.browser_profile_id if brand_state and brand_state.is_connected else None
        )
        if not profile_id:
            raise ValueError("Profile ID is not set")

        browser_profile = BrowserProfile(id=profile_id)
        browser_session = BrowserSession.get(browser_profile)

        if browser_session and browser_session.profile:
            profile_path = browser_session.profile.profile_dir(browser_session.profile.id)
            user_data_dir = str(profile_path)
            logger.info(f"Using userDataDir from browser profile: {user_data_dir}")
            return user_data_dir
    except Exception as e:
        logger.warning(f"Could not get userDataDir from browser session: {e}")
    return None


async def _create_stagehand_config() -> Any:
    """Create Stagehand config with profile integration."""
    user_data_dir = await _get_user_data_dir()

    # Configure browser launch options
    launch_options: dict[str, Any] = {
        "headless": False,
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
        ],
    }

    # Add userDataDir for session persistence if available
    if user_data_dir:
        launch_options["user_data_dir"] = user_data_dir

    return default_config.model_copy(
        update={
            "env": "LOCAL",
            "model_api_key": settings.OPENAI_API_KEY,
            "use_api": False,
            "local_browser_launch_options": launch_options,
        }
    )


# Core Stagehand Agent Functions
async def run_stagehand_agent() -> StagehandAgent:
    """Create and return a minimal StagehandAgent.

    Returns:
        StagehandAgent: Minimal Stagehand interface
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")

    # Create and initialize Stagehand with integrated configuration
    config = await _create_stagehand_config()
    stagehand = Stagehand(config=config)
    await stagehand.init()
    logger.info("StagehandPage created successfully")
    return StagehandAgentWrapper(stagehand)
