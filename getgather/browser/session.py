from __future__ import annotations

from contextlib import asynccontextmanager
from typing import ClassVar

from fastapi import HTTPException
from stagehand import Stagehand

from getgather.browser.profile import BrowserProfile
from getgather.logs import logger


class BrowserStartupError(HTTPException):
    """Raised when browser fails to start."""

    def __init__(self, message: str):
        super().__init__(status_code=503, detail=message, headers={"X-No-Retry": "true"})


class BrowserSession:
    _sessions: ClassVar[dict[str, BrowserSession]] = {}  # tracking profile_id -> session

    def __init__(self, profile_id: str):
        self.profile: BrowserProfile = BrowserProfile(id=profile_id)
        self._stagehand: Stagehand | None = None

        self.total_event = 0

    @classmethod
    def get(cls, profile: BrowserProfile) -> BrowserSession:
        if profile.id in cls._sessions:  # retrieve active session
            return cls._sessions[profile.id]
        else:  # create new session
            return BrowserSession(profile.id)

    @property
    def stagehand(self) -> Stagehand:
        assert self._stagehand is not None, "Browser session not started"
        return self._stagehand

    @property
    def context(self):
        """Get the browser context from Stagehand for compatibility with browser-use."""
        assert self._stagehand is not None, "Browser session not started"
        page = self._stagehand.page
        if page is None:
            raise RuntimeError("Stagehand page not available")
        return page.context

    async def page(self):
        # Stagehand manages pages differently - get the current page
        assert self._stagehand is not None, "Browser session not started"
        return self._stagehand.page

    async def start(self):
        try:
            if self.profile.id in BrowserSession._sessions:
                # Session already started
                return

            BrowserSession._sessions[self.profile.id] = self

            logger.info(
                f"Starting new session with profile {self.profile.id}",
                extra={"profile_id": self.profile.id},
            )

            self._stagehand = await self.profile.launch(profile_id=self.profile.id)

            # TODO: RRWeb injection needs to be adapted for Stagehand
            # The current rrweb_injector expects patchright Page type, not Stagehand's page type
            # page = await self.page()
            # if rrweb_injector.should_inject_for_page(page):
            #     pass  # TODO: Implement rrweb injection for Stagehand if needed

        except Exception as e:
            logger.error(f"Error starting browser: {e}")
            raise BrowserStartupError(f"Failed to start browser: {e}") from e

    async def stop(self):
        logger.info(
            "Closing browser",
            extra={
                "profile_id": self.profile.id,
            },
        )
        try:
            if self._stagehand:
                await self._stagehand.close()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            raise
        finally:
            # clean up local browser profile after stagehand is stopped
            self.profile.cleanup(self.profile.id)

        del self._sessions[self.profile.id]


@asynccontextmanager
async def browser_session(profile: BrowserProfile, *, nested: bool = False):
    session = BrowserSession.get(profile)
    if not nested:
        await session.start()
    try:
        yield session
    finally:
        if not nested:
            await session.stop()
