from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import ClassVar

from fastapi import HTTPException
from patchright.async_api import BrowserContext, Page, Playwright, async_playwright

from getgather.browser.profile import BrowserProfile
from getgather.browser.resource_blocker import configure_context
from getgather.logs import logger
from getgather.rrweb import rrweb_injector


class BrowserStartupError(HTTPException):
    """Raised when browser fails to start."""

    def __init__(self, message: str):
        super().__init__(status_code=503, detail=message, headers={"X-No-Retry": "true"})


class BrowserSession:
    _sessions: ClassVar[dict[str, BrowserSession]] = {}  # tracking profile_id -> session

    def __init__(self, profile_id: str):
        self.profile: BrowserProfile = BrowserProfile(id=profile_id)
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None

        self.total_event = 0

    @classmethod
    def get(cls, profile: BrowserProfile) -> BrowserSession:
        if profile.id in cls._sessions:  # retrieve active session
            return cls._sessions[profile.id]
        else:  # create new session
            return BrowserSession(profile.id)

    @property
    def context(self) -> BrowserContext:
        assert self._context is not None, "Browser session not started"
        return self._context

    @property
    def playwright(self) -> Playwright:
        assert self._playwright is not None, "Browser session not started"
        return self._playwright

    async def new_page(self) -> Page:
        logger.info(f"Creating new page in context with profile {self.profile.id}")
        return await self.context.new_page()

    async def page(self) -> Page:
        # TODO: It's okay for now to return the last page. We may want to track all pages in the future.
        if self.context.pages and len(self.context.pages) > 0:
            logger.info(f"Returning existing page in context with profile {self.profile.id}")
            return self.context.pages[-1]
        return await self.new_page()

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

            self._playwright = await async_playwright().start()
            self._context = await self.profile.launch(
                profile_id=self.profile.id, browser_type=self.playwright.chromium
            )

            await configure_context(self._context)

            debug_page = await self.page()
            await debug_page.goto("https://ifconfig.me")

            # Intentionally create a new page to apply resources filtering (from blocklists)
            page = await self.new_page()

            page.on(
                "load",
                lambda page: asyncio.create_task(rrweb_injector.setup_rrweb(self.context, page)),
            )

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
            if self.context.browser:
                await self.context.browser.close()
        except Exception as e:
            logger.error(f"Error closing browser. Stopping playwright manually: {e}")
            raise
        finally:
            await self.playwright.stop()

        # clean up local browser profile after playwright is stopped
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
