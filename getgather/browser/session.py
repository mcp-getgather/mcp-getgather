from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager, suppress
from typing import ClassVar

from fastapi import HTTPException
from nanoid import generate
from patchright.async_api import BrowserContext, Page, Playwright, async_playwright

from getgather.browser.profile import BrowserProfile
from getgather.browser.resource_blocker import configure_context
from getgather.logs import logger
from getgather.rrweb import rrweb_injector, rrweb_manager

FRIENDLY_CHARS: str = "23456789abcdefghijkmnpqrstuvwxyz"


class BrowserStartupError(HTTPException):
    """Raised when browser fails to start."""

    def __init__(self, message: str):
        super().__init__(status_code=503, detail=message, headers={"X-No-Retry": "true"})


class BrowserSession:
    _sessions: ClassVar[dict[str, BrowserSession]] = {}  # tracking profile_id -> session
    _locks: ClassVar[dict[str, asyncio.Lock]] = defaultdict(asyncio.Lock)

    def __new__(cls, profile_id: str) -> BrowserSession:
        if profile_id in cls._sessions:
            return cls._sessions[profile_id]
        else:
            instance = super(BrowserSession, cls).__new__(cls)
            return instance

    def __init__(self, profile_id: str):
        if getattr(self, "_initialized", False):  # double init check_initialized")
            return
        self._initialized = True
        self.profile: BrowserProfile = BrowserProfile(id=profile_id)
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None

        self.session_id = generate(FRIENDLY_CHARS, 8)
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

    async def start(self) -> BrowserSession:
        if self.profile.id in BrowserSession._sessions:
            # Session already started
            return BrowserSession._sessions[self.profile.id]
        lock = self._locks[self.profile.id]
        async with lock:  # prevent race condition when two requests try to start the same profile
            try:
                if self.profile.id in BrowserSession._sessions:
                    # Session already started
                    return BrowserSession._sessions[self.profile.id]
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
                await debug_page.goto("https://checkip.amazonaws.com")

                # Intentionally create a new page to apply resources filtering (from blocklists)
                page = await self.new_page()

                page.on(
                    "load",
                    lambda page: asyncio.create_task(
                        rrweb_injector.setup_rrweb(self.context, page)
                    ),
                )

                # safely register the session at the end
                self._sessions[self.profile.id] = self

                return self

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

        await rrweb_manager.save_recording(self.session_id)

        try:
            if self._context and self.context.browser:
                await self.context.browser.close()
        except Exception as e:
            logger.error(f"Error closing browser; continuing teardown: {e}")
        finally:
            if self._playwright:
                with suppress(Exception):  # try or die kill playwright
                    await self.playwright.stop()

        try:
            # clean up local browser profile after playwright is stopped
            self.profile.cleanup(self.profile.id)
        finally:  # ensure we always remove session from tracking
            self._sessions.pop(self.profile.id, None)
            self._context = None
            self._playwright = None


@asynccontextmanager
async def browser_session(profile: BrowserProfile, *, nested: bool = False, stop_ok: bool = True):
    session = BrowserSession.get(profile)
    if not nested:
        session = await session.start()
    try:
        yield session
    finally:
        if not nested and stop_ok:
            await session.stop()
