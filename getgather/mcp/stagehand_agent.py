"""
Stagehand agent implementation for AI-powered browser automation.

This module provides a functional interface for creating and using Stagehand agents
with the existing getgather browser profile system for session persistence.
"""

from typing import Any, Protocol

# BrowserContext import removed - Stagehand creates its own browser instance
from stagehand import Stagehand, default_config

from getgather.config import settings
from getgather.logs import logger
from getgather.mcp.shared import get_mcp_browser_session, with_brand_browser_session


class StagehandPage(Protocol):
    """Protocol for StagehandPage interface matching real Stagehand."""

    async def goto(self, url: str) -> None:
        """Navigate to a URL."""
        ...

    async def act(self, action_or_result: str, **kwargs: Any) -> Any:
        """Perform an action based on natural language instruction."""
        ...

    async def extract(self, options_or_instruction: str | None = None, **kwargs: Any) -> Any:
        """Extract data based on natural language instruction."""
        ...


def _get_user_data_dir() -> str | None:
    """Get userDataDir from browser session profile for session persistence."""
    try:
        browser_session = get_mcp_browser_session()
        if browser_session and browser_session.profile:
            profile_path = browser_session.profile.profile_dir(browser_session.profile.id)
            user_data_dir = str(profile_path)
            logger.info(f"Using userDataDir from browser profile: {user_data_dir}")
            return user_data_dir
    except Exception as e:
        logger.warning(f"Could not get userDataDir from browser session: {e}")
    return None


def _create_stagehand_config() -> Any:
    """Create Stagehand configuration with browser profile integration."""
    user_data_dir = _get_user_data_dir()

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
        launch_options["userDataDir"] = user_data_dir

    return default_config.model_copy(
        update={
            "env": "LOCAL",
            "model_api_key": settings.OPENAI_API_KEY,
            "use_api": False,
            "local_browser_launch_options": launch_options,
        }
    )


# Core Stagehand Agent Functions


@with_brand_browser_session
async def run_stagehand_agent() -> StagehandPage:
    """Create and return a StagehandPage with AI capabilities.

    This is the main functional interface: () -> StagehandPage

    Returns:
        StagehandPage: A configured StagehandPage instance with AI capabilities

    Raises:
        ValueError: If OPENAI_API_KEY is not set
        RuntimeError: If StagehandPage creation fails
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")

    # Create and initialize Stagehand with integrated configuration
    config = _create_stagehand_config()
    stagehand = Stagehand(config=config)
    await stagehand.init()

    # Validate StagehandPage creation
    stagehand_page = stagehand.page
    if stagehand_page is None:
        raise RuntimeError("Failed to create StagehandPage - stagehand.page is None")

    logger.info("StagehandPage created successfully")
    return stagehand_page
