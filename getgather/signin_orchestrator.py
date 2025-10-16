from datetime import datetime
from enum import StrEnum

import sentry_sdk
from fastapi import HTTPException
from patchright.async_api import Page, Route

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession, BrowserStartupError
from getgather.config import settings
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.flow import flow_step
from getgather.flow_state import FlowState
from getgather.logs import logger
from getgather.sentry import set_user_context, setup_error_context


class ProxyError(HTTPException):
    """Exception raised when a proxy connection fails."""

    def __init__(self, message: str):
        super().__init__(status_code=503, detail=message, headers={"X-No-Retry": "true"})


class SigninStatus(StrEnum):
    """The status of the sign in flow."""

    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    NEED_INPUT = "NEED_INPUT"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class SigninOrchestrator:
    """Manages sign in flows for connectors."""

    def __init__(
        self,
        *,
        brand_id: BrandIdEnum,
        browser_profile: BrowserProfile,
        state: FlowState | None = None,
    ):
        self.brand_id = brand_id
        self.browser_profile = browser_profile
        self.state = state or FlowState(brand_id=brand_id)
        self.status = (
            SigninStatus.INITIALIZING
            if self.state.current_page_spec_name is None and self.state.step_index == 0
            else SigninStatus.RUNNING
        )

        # Internal flag to avoid repeatedly updating Sentry user.
        self._sentry_user_set: bool = False

    def _maybe_set_sentry_user(self) -> None:
        """Attach user context to Sentry based on current inputs (once)."""
        if self._sentry_user_set:
            return

        if set_user_context(self.state.inputs):
            self._sentry_user_set = True

    async def advance(self) -> FlowState:
        """Start the sign in flow for a connector."""
        logger.info(
            f"🔥 Starting sign in for {self.brand_id}",
        )
        try:
            browser_session = BrowserSession.get(self.browser_profile)
            await self.state.init(
                browser_profile_id=self.browser_profile.id, brand_id=self.brand_id
            )

            # Attach user context to Sentry as soon as we have it.
            self._maybe_set_sentry_user()

            if self.status == SigninStatus.INITIALIZING:
                await browser_session.start()

            page = await browser_session.page()
            if settings.SHOULD_BLOCK_UNWANTED_RESOURCES:
                # For now block the images etc
                await self._block_unwanted_resources(page)
        except BrowserStartupError as e:
            sentry_sdk.capture_exception(e)
            raise

        try:
            while (
                not self.state.finished
                and self.status != SigninStatus.NEED_INPUT
                and self.status != SigninStatus.PAUSED
            ):
                await flow_step(page=page, flow_state=self.state)

                # Refresh Sentry user when inputs change.
                self._maybe_set_sentry_user()

                # Check if the flow is finished
                if self.state.finished:
                    logger.info(
                        f"✅ Auth flow for {self.brand_id} is complete",
                        extra={"profile_id": self.browser_profile.id},
                    )
                    self.status = SigninStatus.FINISHED
                # Check if we need user input
                elif self.state.prompt:
                    logger.info(
                        f"Auth flow for {self.brand_id} needs input",
                        extra={"profile_id": self.browser_profile.id},
                    )
                    self.status = SigninStatus.NEED_INPUT
                elif self.state.paused:
                    logger.info(
                        f"🕒 Auth flow for {self.brand_id} is paused",
                        extra={"profile_id": self.browser_profile.id},
                    )
                    self.status = SigninStatus.PAUSED
        except Exception as e:
            self.status = SigninStatus.ERROR
            self.state.error = str(e)
            filename = f"{browser_session.profile.id}_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            filepath = settings.screenshots_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)
            html = await page.content()
            with open(filepath.with_suffix(".html"), "w", encoding="utf-8") as f:
                f.write(html)
            await browser_session.stop()
            with sentry_sdk.isolation_scope() as scope:
                # Attach user to this isolated scope as well.
                set_user_context(self.state.inputs, scope=scope)
                setup_error_context(
                    scope=scope,
                    e=e,
                    brand_id=self.brand_id,
                    error_type="signin_flow_error",
                    flow_state=self.state.model_dump(),
                    browser_profile_id=browser_session.profile.id,
                    page_content=html,
                    screenshot_path=filepath,
                )
                await self.state.log_records(sentry=True, sentry_scope=scope)
                sentry_sdk.capture_exception(e)
            if "ERR_TUNNEL_CONNECTION_FAILED" in str(e):
                raise ProxyError("Proxy connection failed") from e
            raise e
        finally:
            pass

        return self.state

    async def finalize(self) -> None:
        logger.info(
            f"🚩 Finalizing sign in for {self.brand_id}",
            extra={"profile_id": self.browser_profile.id},
        )
        browser_session = BrowserSession.get(self.browser_profile)
        await browser_session.stop()

    async def _block_unwanted_resources(self, page: Page) -> None:
        """Block loading of images, media, fonts, and specific domains."""
        await page.route("**/*", lambda route: self._handle_route(route))

    async def _handle_route(self, route: Route) -> None:
        """Handle route requests and block unwanted resources."""
        request = route.request
        resource_type = request.resource_type
        url = request.url

        try:
            # Abort requests for images, media, fonts – they are not needed for sign in flows.
            if resource_type in ["image", "media", "font"]:
                await route.abort()
                return

            # Abort tracking / analytics requests that slow things down and are irrelevant.
            if "quantummetric.com" in url or "nr-data.net" in url or "googletagmanager.com" in url:
                await route.abort()
                return

            # Allow all other requests to proceed.
            await route.continue_()
        except Exception as e:  # swallow errors if the page/context has already been closed
            logger.debug(f"Route handling ignored for closed page or context. url={url} err={e}")
