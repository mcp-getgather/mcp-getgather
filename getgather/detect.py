import asyncio
import logging
from datetime import datetime
from operator import attrgetter

from nanoid import generate
from patchright.async_api import FrameLocator, Page
from pydantic import BaseModel

from getgather.actions import is_visible
from getgather.config import settings
from getgather.connectors.spec_models import Field, PageSpec, PageSpecYML
from getgather.flow_state import FlowState
from getgather.logs import logger


def get_universal_pages() -> list[PageSpec]:
    """Get universal pages that should be available for all brand specs."""
    universal_pages_yml = [
        PageSpecYML(
            name="Chrome Network Error",
            url="chrome-error://chromewebdata/",
            end=True,
            message="❌ Network connection error. Please check your internet connection and try again.",
        ),
    ]

    # Add test-specific universal pages
    if settings.ENVIRONMENT in ["local", "test"]:
        universal_pages_yml.append(
            PageSpecYML(
                name="ACME Test Error Page",
                url="http://localhost:5001/error-page",
                end=True,
                message="❌ Test error page detected. This is a universal test error.",
            )
        )

    return [
        PageSpec.from_yml(page_yml, fields_map={}, pages_map={}) for page_yml in universal_pages_yml
    ]


class PageSpecDetector:
    """Callable helper that figures out which PageSpec matches the current URL/DOM.

    Instantiate it once with the connector's ``page_states`` and then call the
    instance with a Playwright ``Page`` object:

    ```python
    detector = PageSpecDetector(page_states)
    page_spec = await detector(page)
    ```
    """

    def __init__(self, flow_state: FlowState):
        self.flow_state = flow_state

    async def _detect_once(self, page: Page, field_detections: dict[str, bool]) -> str:
        """Try to match a single ``PageSpec`` without polling.

        All page specifications are evaluated *concurrently* and we select the
        most specific one—i.e. the page with the highest number of satisfied
        visibility checks.  This prevents less-specific pages that are supersets
        of selectors from being matched first just because they appear earlier
        in the list.
        """

        url: str = page.url
        logger.info(f"🔍 Detecting page: {url}")

        # When debugging, save a screenshot / HTML snapshot for inspection.
        if logger.isEnabledFor(logging.DEBUG):
            filename = f"{self.flow_state.browser_profile_id}_{datetime.now().strftime('%Y%m%d_%H%M')}_{generate(size=5)}.png"
            filepath = settings.screenshots_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)

            # Try to get page content, but handle navigation errors gracefully
            try:
                html = await page.content()
                with open(filepath.with_suffix(".html"), "w", encoding="utf-8") as f:
                    f.write(html)
                logger.debug(f"📸 Saved screenshot → file://{filepath}")
            except Exception as e:
                logger.debug(f"⚠️ Can't capture page content during navigation: {e}")

        self.flow_state.page_detections = [
            _detect_page_spec(ps, url, field_detections) for ps in self.flow_state.flow.pages
        ]
        matched = [result for result in self.flow_state.page_detections if result.matched]

        if not matched:
            raise ValueError(f"No page spec found for {url}")

        best_result = max(matched, key=attrgetter("score"))
        logger.info(
            f"🎯 ** detected page as {best_result.page_name}",
            extra={"profile_id": self.flow_state.browser_profile_id},
        )
        return best_result.page_name

    async def detect(
        self, page: Page, *, timeout_ms: int = 30_000, interval_ms: int = 1_000
    ) -> str:
        """Detect the page, polling until success or *timeout_ms* expires."""

        intervals = timeout_ms // interval_ms
        await asyncio.sleep(interval_ms / 1000)
        while intervals >= 0:
            try:
                self.flow_state.field_detections = await _detect_fields(
                    self.flow_state.flow.fields, page
                )
                return await self._detect_once(page, self.flow_state.field_detections)
            except ValueError as e:
                logger.debug(
                    f"❌ Error detecting page: {e}"
                )  # debug because it is conceivable that we need to retry in normal situations
                if intervals == 0:
                    break
                await asyncio.sleep(interval_ms / 1000)
                intervals -= 1

        raise ValueError(f"❌ No page state found for {page.url}")


async def _detect_field(field: Field, page: Page):
    selector = field.selector or field.selectors
    if selector is None:
        return True

    # detect field inside iframe
    if field.iframe_selector:
        iframe: FrameLocator = page.frame_locator(field.iframe_selector)
        return await is_visible(iframe.locator(selector))

    return await is_visible(page.locator(selector))


async def _detect_fields(fields: list[Field], page: Page) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for field in fields:
        result = await _detect_field(field, page)
        results[field.name] = result
    return results


class PageDetectResult(BaseModel):
    page_name: str
    url: bool | None  # whether the url matches
    fields: float  # percentage of fields that are visible
    score: int

    @property
    def matched(self) -> bool:
        return self.url is not False and self.fields == 1.0


def _detect_page_spec(
    spec: PageSpec, url: str, visible_fields: dict[str, bool]
) -> PageDetectResult:
    url_match = url.startswith(str(spec.url)) if spec.url else None
    fields_match = {
        fld.name: visible_fields.get(fld.name, False) for fld in spec.fields(include="required")
    }

    score = sum(fields_match.values())
    fields_match_ratio = score / len(fields_match) if fields_match else 1.0

    return PageDetectResult(
        page_name=spec.name, url=url_match, fields=fields_match_ratio, score=score
    )
