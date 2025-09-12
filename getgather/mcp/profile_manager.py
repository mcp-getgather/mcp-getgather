"""Global browser profile manager for single-user setup."""

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.logs import logger
from fastmcp.server.dependencies import get_context, get_http_headers


class GlobalProfileManager:
    """Manages a single browser profile for all brands."""

    _instance: "GlobalProfileManager | None" = None
    _profile: BrowserProfile | None = None

    def __new__(cls) -> "GlobalProfileManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_profile(self) -> BrowserProfile:
        """Get or create the global browser profile."""
        headers = get_http_headers(include_all=True)
        if headers.get("x-getgather-custom-app"):
            mcp_session_id = get_context().session_id
            return BrowserProfile(id=mcp_session_id)

        if self._profile is None:
            # Use a fixed profile ID for single-user setup
            self._profile = BrowserProfile(id="global")
            logger.info(f"Created global browser profile: {self._profile.id}")
        return self._profile

    def get_session(self) -> BrowserSession:
        """Get browser session for the global profile."""
        profile = self.get_profile()
        return BrowserSession.get(profile)


# Global instance
global_profile_manager = GlobalProfileManager()
