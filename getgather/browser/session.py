from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, ClassVar

from fastapi import HTTPException
from patchright.async_api import BrowserContext, Page, Playwright, async_playwright

from getgather.browser.profile import BrowserProfile
from getgather.context import current_activity
from getgather.database.repositories.activity_repository import Activity
from getgather.logs import logger


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
        self._activity: Activity | None = None

    @classmethod
    async def get(cls, profile: BrowserProfile) -> BrowserSession:
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

    async def page(self) -> Page:
        # TODO: It's okay for now to return the last page. We may want to track all pages in the future.
        if not self.context.pages:
            await self.context.new_page()
        return self.context.pages[-1]

    async def save_event(self, event: dict[str, Any]) -> None:
        activity = current_activity.get()
        if activity:
            print(f"DEBUGPRINT: Saving event for activity {activity.name} (ID: {activity.id})")
            # TODO: Store event with activity context in database
            # For now, just log the association
        else:
            print(f"DEBUGPRINT: No activity context found for event")
        
        print(f"DEBUGPRINT[461]: session.py:57: event={len(event)}")
        

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
            await self._context.expose_function("saveEvent", self.save_event)  # type: ignore
        except Exception as e:
            logger.error(f"Error starting browser: {e}")
            raise BrowserStartupError(f"Failed to start browser: {e}") from e

    async def start_recording(self):
        page = await self.page()
        await page.add_script_tag(
            url="https://cdn.jsdelivr.net/npm/rrweb@2.0.0-alpha.14/dist/record/rrweb-record.min.js"
        )
        await page.evaluate(
            "() => { rrwebRecord({ emit(event) { window.saveEvent(event); }, maskAllInputs: true }); }",
            isolated_context=False,
        )


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
    session = await BrowserSession.get(profile)
    if not nested:
        await session.start()
    try:
        yield session
    finally:
        if not nested:
            await session.stop()
