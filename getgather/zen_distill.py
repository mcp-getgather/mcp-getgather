import asyncio
import os
import random
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlunparse

import nanoid
import sentry_sdk
import zendriver as zd
from bs4 import BeautifulSoup, Tag
from nanoid import generate

from getgather.config import settings
from getgather.distill import (
    ConversionResult,
    Match,
    Pattern,
    convert,
    get_selector,
    load_distillation_patterns,
    terminate,
)
from getgather.logs import logger


def _safe_fragment(value: str) -> str:
    """Convert a value to a safe filename fragment."""
    fragment = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return fragment or "distill"


async def capture_page_artifacts(
    page: zd.Tab,  # type: ignore[name-defined]
    *,
    identifier: str,
    prefix: str,
    capture_html: bool = True,
) -> tuple[Path, Path | None, str | None]:
    """Capture a screenshot (and optional HTML) for debugging/triage."""

    settings.screenshots_dir.mkdir(parents=True, exist_ok=True)

    base_identifier = _safe_fragment(identifier)
    base_prefix = _safe_fragment(prefix)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    token = generate(size=5)
    filename = f"{base_identifier}_{base_prefix}_{timestamp}_{token}.png"
    screenshot_path = settings.screenshots_dir / filename

    await page.save_screenshot(filename=str(screenshot_path), full_page=True)  # type: ignore[attr-defined]

    html_path: Path | None = None
    html_content: str | None = None
    if capture_html:
        try:
            html_content = await page.get_content()  # type: ignore[attr-defined]
        except Exception as exc:  # ignore navigation races during capture
            logger.debug(f"⚠️ Can't capture page content during navigation: {exc}")
        else:
            html_path = screenshot_path.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")

    logger.debug(
        "📸 Distill artifact saved",
        extra={
            "screenshot": f"file://{screenshot_path}",
            "html": f"file://{html_path}" if html_path else None,
        },
    )

    return screenshot_path, html_path, html_content


async def report_distill_error(
    *,
    error: Exception,
    page: zd.Tab | None,  # type: ignore[name-defined]
    profile_id: str,
    location: str,
    hostname: str,
    iteration: int,
) -> None:
    screenshot_path: Path | None = None
    html_path: Path | None = None

    if page:
        try:
            screenshot_path, html_path, _ = await capture_page_artifacts(
                page,
                identifier=profile_id,
                prefix="distill_error",
            )
        except Exception as capture_error:
            logger.warning(f"Failed to capture distillation artifacts: {capture_error}")

    context: dict[str, Any] = {
        "location": location,
        "hostname": hostname,
        "iteration": iteration,
    }

    logger.error(
        "Distillation error",
        extra={
            "profile_id": profile_id,
            "location": location,
            "iteration": iteration,
            "screenshot": f"file://{screenshot_path}" if screenshot_path else None,
        },
    )

    if settings.SENTRY_DSN:
        with sentry_sdk.isolation_scope() as scope:
            scope.set_context("distill", context)
            if screenshot_path:
                scope.add_attachment(
                    filename=screenshot_path.name,
                    path=str(screenshot_path),
                )
            if html_path:
                scope.add_attachment(
                    filename=html_path.name,
                    path=str(html_path),
                )

            sentry_sdk.capture_exception(error)


async def init_zendriver_browser() -> zd.Browser:
    FRIENDLY_CHARS = "23456789abcdefghijkmnpqrstuvwxyz"
    id = nanoid.generate(FRIENDLY_CHARS, 6)
    user_data_dir: Path = settings.profiles_dir / id

    logger.info(
        f"Launching Zendriver browser with user_data_dir: {user_data_dir}",
        extra={"profile_id": id},
    )
    browser = await zd.start(user_data_dir=str(user_data_dir), browser_args=["--no-sandbox"])
    browser.id = id  # type: ignore[attr-defined]

    return browser


async def get_new_page(browser: zd.Browser) -> zd.Tab:
    page = await browser.get()

    async def handle_request(event: zd.cdp.fetch.RequestPaused) -> None:
        resource_type = event.resource_type
        request_url = event.request.url

        deny_type = resource_type in [
            zd.cdp.network.ResourceType.IMAGE,
            zd.cdp.network.ResourceType.MEDIA,
            zd.cdp.network.ResourceType.FONT,
        ]
        should_deny = deny_type

        if not should_deny:
            await page.send(zd.cdp.fetch.continue_request(request_id=event.request_id))
            return

        logger.debug(f" DENY: {request_url}")
        await page.send(
            zd.cdp.fetch.fail_request(
                request_id=event.request_id,
                error_reason=zd.cdp.network.ErrorReason.BLOCKED_BY_CLIENT,
            )
        )

    page.add_handler(zd.cdp.fetch.RequestPaused, handle_request)  # type: ignore[reportUnknownMemberType]
    return page


class Element:
    """Wrapper to handle both CSS and XPath selector differences for browser elements."""

    def __init__(
        self,
        element: zd.Element,
        css_selector: str | None = None,
        xpath_selector: str | None = None,
    ):
        self.element = element
        self.tag = element.tag
        self.page = element.tab
        self.css_selector = css_selector
        self.xpath_selector = xpath_selector

    async def inner_html(self) -> str:
        return await self.element.get_html()

    async def inner_text(self) -> str:
        return self.element.text

    async def click(self) -> None:
        if self.css_selector:
            await self.css_click()
        else:
            await self.xpath_click()
        await asyncio.sleep(0.25)

    async def type_text(self, text: str) -> None:
        await self.element.clear_input()
        await asyncio.sleep(0.1)
        for char in text:
            await self.element.send_keys(char)
            await asyncio.sleep(random.uniform(0.01, 0.05))

    async def css_click(self) -> None:
        if not self.css_selector:
            logger.warning("Cannot perform CSS click: no css_selector available")
            return
        logger.debug(f"Attempting JavaScript CSS click for {self.css_selector}")
        try:
            escaped_selector = self.css_selector.replace("\\", "\\\\").replace('"', '\\"')
            js_code = f"""
            (() => {{
                let element = document.querySelector("{escaped_selector}");
                if (element) {{ element.click(); return true; }}
                return false;
            }})()
            """
            result = await self.page.evaluate(js_code)
            if result:
                logger.info(f"JavaScript CSS click succeeded for {self.css_selector}")
                return
            else:
                logger.warning(f"JavaScript CSS click could not find element {self.css_selector}")
        except Exception as js_error:
            logger.error(f"JavaScript CSS click failed: {js_error}")

    async def xpath_click(self) -> None:
        if not self.xpath_selector:
            logger.warning(f"Cannot perform XPath click: no xpath_selector available")
            return
        logger.debug(f"Attempting JavaScript XPath click for {self.xpath_selector}")
        try:
            escaped_selector = self.xpath_selector.replace("\\", "\\\\").replace('"', '\\"')
            js_code = f"""
            (() => {{
                let element = document.evaluate("{escaped_selector}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) {{ element.click(); return true; }}
                return false;
            }})()
            """
            result = await self.page.evaluate(js_code)
            if result:
                logger.info(f"JavaScript XPath click succeeded for {self.xpath_selector}")
                return
            else:
                logger.warning(
                    f"JavaScript XPath click could not find element {self.xpath_selector}"
                )
        except Exception as js_error:
            logger.error(f"JavaScript XPath click failed: {js_error}")


async def page_query_selector(page: zd.Tab, selector: str, timeout: float = 0) -> Element | None:
    try:
        if selector.startswith("//"):
            elements = await page.xpath(selector, timeout)
            if elements and len(elements) > 0:
                return Element(elements[0], xpath_selector=selector)
            return None

        element = await page.select(selector, timeout=timeout)
        if element:
            return Element(element, css_selector=selector)
        return None
    except (asyncio.TimeoutError, Exception):
        return None


async def distill(hostname: str | None, page: zd.Tab, patterns: list[Pattern]) -> Match | None:
    result: list[Match] = []

    for item in patterns:
        name = item.name
        pattern = item.pattern

        root = pattern.find("html")
        gg_priority = root.get("gg-priority", "-1") if isinstance(root, Tag) else "-1"
        try:
            priority = int(str(gg_priority).lstrip("= "))
        except ValueError:
            priority = -1
        domain = root.get("gg-domain") if isinstance(root, Tag) else None

        if domain and hostname:
            local = "localhost" in hostname or "127.0.0.1" in hostname
            if isinstance(domain, str) and not local and domain.lower() not in hostname.lower():
                logger.debug(f"Skipping {name} due to mismatched domain {domain}")
                continue

        logger.debug(f"Checking {name} with priority {priority}")

        found = True
        match_count = 0

        targets = pattern.find_all(attrs={"gg-match": True}) + pattern.find_all(
            attrs={"gg-match-html": True}
        )

        for target in targets:
            if not isinstance(target, Tag):
                continue

            if not found:
                break

            html = target.get("gg-match-html")
            selector, _ = get_selector(str(html if html else target.get("gg-match")))

            if not selector:
                continue

            source = await page_query_selector(page, selector)
            if source:
                match_count += 1
                if html:
                    target.clear()
                    fragment = BeautifulSoup(
                        "<div>" + await source.inner_html() + "</div>", "html.parser"
                    )
                    if fragment.div:
                        for child in list(fragment.div.children):
                            child.extract()
                            target.append(child)
                else:
                    raw_text = await source.inner_text()
                    if raw_text:
                        target.string = raw_text.strip()
                    if source.tag in ["input", "textarea", "select"]:
                        target["value"] = source.element.value or ""
                match_count += 1
            else:
                optional = target.get("gg-optional") is not None
                logger.debug(f"Optional {selector} has no match")
                if not optional:
                    found = False

        if found and match_count > 0:
            distilled = str(pattern)
            result.append(
                Match(
                    name=name,
                    priority=priority,
                    distilled=distilled,
                )
            )

    result = sorted(result, key=lambda x: x.priority)

    if len(result) == 0:
        logger.debug("No matches found")
        return None
    else:
        logger.debug(f"Number of matches: {len(result)}")
        for item in result:
            logger.debug(f" - {item.name} with priority {item.priority}")
        match = result[0]
        logger.info(f"✓ Best match: {match.name}")
        return match


async def run_distillation_loop(
    location: str, patterns: list[Pattern], browser: zd.Browser, timeout: int = 15
) -> tuple[bool, str, ConversionResult | None]:
    """Run the distillation loop with zendriver.

    Returns:
        terminated: bool indicating successful termination
        distilled: the raw distilled HTML
        converted: the converted JSON if successful, otherwise None
    """
    if len(patterns) == 0:
        logger.error("No distillation patterns provided")
        raise ValueError("No distillation patterns provided")

    hostname = urllib.parse.urlparse(location).hostname or ""

    page = await get_new_page(browser)
    logger.info(f"Navigating to {location}")
    try:
        await page.get(location)
    except Exception as error:
        logger.error(f"Failed to navigate to {location}: {error}")
        await report_distill_error(
            error=error,
            page=page,
            profile_id=browser.id,  # type: ignore[attr-defined]
            location=location,
            hostname=hostname,
            iteration=0,
        )
        raise ValueError(f"Failed to navigate to {location}: {error}")

    TICK = 1  # seconds
    max = timeout // TICK

    current = Match(name="", priority=-1, distilled="")

    for iteration in range(max):
        logger.info("")
        logger.info(f"Iteration {iteration + 1} of {max}")
        await asyncio.sleep(TICK)

        match = await distill(hostname, page, patterns)
        if match:
            if match.distilled == current.distilled:
                logger.debug(f"Still the same: {match.name}")
            else:
                distilled = match.distilled
                current = match

                if await terminate(distilled):
                    converted = await convert(distilled)
                    await page.close()
                    return (True, distilled, converted)

                current.distilled = distilled

        else:
            logger.debug(f"No matched pattern found")

    await report_distill_error(
        error=ValueError("No matched pattern found"),
        page=page,
        profile_id=browser.id,  # type: ignore[attr-defined]
        location=location,
        hostname=hostname,
        iteration=max,
    )
    await page.close()
    return (False, current.distilled, None)


async def short_lived_mcp_tool(
    location: str,
    pattern_wildcard: str,
    result_key: str,
    url_hostname: str,
) -> tuple[bool, dict[str, Any]]:
    path = os.path.join(os.path.dirname(__file__), "mcp", "patterns", pattern_wildcard)
    patterns = load_distillation_patterns(path)

    browser = await init_zendriver_browser()
    terminated, distilled, converted = await run_distillation_loop(location, patterns, browser)
    await browser.stop()  # type: ignore[attr-defined]

    result: dict[str, Any] = {result_key: converted if converted else distilled}
    if result_key in result:
        items_value = result[result_key]
        if isinstance(items_value, list):
            for item in cast(list[dict[str, Any]], items_value):
                if "link" in item:
                    link = cast(str, item["link"])
                    parsed = urllib.parse.urlparse(link)
                    netloc: str = parsed.netloc if parsed.netloc else url_hostname
                    url: str = urlunparse((
                        "https",
                        netloc,
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment,
                    ))
                    item["url"] = url
    return terminated, result
