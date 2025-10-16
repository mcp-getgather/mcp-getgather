from __future__ import annotations

from contextlib import suppress
from typing import Protocol

from patchright.async_api import Page

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession


class PageProvider(Protocol):
    """Minimal interface for producing and managing Playwright pages."""

    profile: BrowserProfile

    async def new_page(self, *, initial_url: str | None = None) -> Page:
        """Create or return a Playwright page ready for use."""
        ...

    async def close_page(self, page: Page) -> None:
        """Close a previously created page."""
        ...

    async def shutdown(self) -> None:
        """Tear down any resources associated with the provider."""
        ...


class SharedBrowserPageProvider:
    """Provide pages backed by a shared browser session for a profile."""

    def __init__(
        self,
        profile: BrowserProfile,
        session: BrowserSession,
        anchor_page: Page,
        *,
        stop_on_shutdown: bool = False,
    ):
        self.profile = profile
        self._session = session
        self._anchor_page = anchor_page
        self.stop_on_shutdown = stop_on_shutdown
        self._active_pages: set[Page] = set()
        self._closed = False

    @classmethod
    async def create(
        cls,
        profile: BrowserProfile,
        *,
        anchor_url: str | None = "https://ifconfig.me",
        stop_on_shutdown: bool = False,
    ) -> "SharedBrowserPageProvider":
        session = BrowserSession.get(profile)
        await session.start()

        anchor_page = await session.new_page()
        if anchor_url:
            await anchor_page.goto(anchor_url)

        return cls(
            profile=profile,
            session=session,
            anchor_page=anchor_page,
            stop_on_shutdown=stop_on_shutdown,
        )

    def _register_page(self, page: Page) -> None:
        self._active_pages.add(page)
        page.on("close", lambda _: self._active_pages.discard(page))

    async def new_page(self, *, initial_url: str | None = None) -> Page:
        page = await self._session.new_page()
        self._register_page(page)
        if initial_url:
            await page.goto(initial_url)
        return page

    async def close_page(self, page: Page) -> None:
        self._active_pages.discard(page)
        if not page.is_closed():
            with suppress(Exception):
                await page.close()

    async def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True

        for page in list(self._active_pages):
            if not page.is_closed():
                with suppress(Exception):
                    await page.close()
        self._active_pages.clear()

        if self._anchor_page and not self._anchor_page.is_closed():
            with suppress(Exception):
                await self._anchor_page.close()

        if self.stop_on_shutdown:
            with suppress(Exception):
                await self._session.stop()


class IncognitoPageProvider:
    """Provide pages using an ephemeral incognito browser session."""

    def __init__(
        self,
        profile: BrowserProfile,
        session: BrowserSession,
    ):
        self.profile = profile
        self._session = session
        self._active_pages: set[Page] = set()
        self._closed = False

    @classmethod
    async def create(cls, profile: BrowserProfile | None = None) -> "IncognitoPageProvider":
        browser_profile = profile or BrowserProfile()
        session = BrowserSession.get(browser_profile)
        await session.start()
        return cls(browser_profile, session)

    def _register_page(self, page: Page) -> None:
        self._active_pages.add(page)
        page.on("close", lambda _: self._active_pages.discard(page))

    async def new_page(self, *, initial_url: str | None = None) -> Page:
        page = await self._session.new_page()
        self._register_page(page)
        if initial_url:
            await page.goto(initial_url)
        return page

    async def close_page(self, page: Page) -> None:
        self._active_pages.discard(page)
        if not page.is_closed():
            with suppress(Exception):
                await page.close()

    async def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True

        for page in list(self._active_pages):
            if not page.is_closed():
                with suppress(Exception):
                    await page.close()
        self._active_pages.clear()

        with suppress(Exception):
            await self._session.stop()
