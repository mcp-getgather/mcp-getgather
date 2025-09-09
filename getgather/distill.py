import asyncio
import json
import os
import re
import urllib.parse
from glob import glob
from typing import cast

import pwinput
from bs4 import BeautifulSoup
from bs4.element import Tag
from patchright.async_api import Locator, Page
from pydantic import BaseModel

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.logs import logger
from getgather.mcp.shared import get_mcp_browser_profile


class Pattern(BaseModel):
    name: str
    pattern: BeautifulSoup

    class Config:
        arbitrary_types_allowed = True


class Match(BaseModel):
    name: str
    priority: int
    distilled: str
    matches: list[Locator]

    class Config:
        arbitrary_types_allowed = True


def get_selector(input_selector: str | None) -> tuple[str | None, str | None]:
    pattern = r"^(iframe(?:[^\s]*\[[^\]]+\]|[^\s]+))\s+(.+)$"
    if not input_selector:
        return None, None
    match = re.match(pattern, input_selector)
    if not match:
        return input_selector, None
    return match.group(2), match.group(1)


async def convert(distilled: str):
    document = BeautifulSoup(distilled, "html.parser")
    snippet = document.find("script", {"type": "application/json"})
    if snippet:
        logger.info(f"Found a data converter.")
        logger.info(snippet.get_text())
        try:
            converter = json.loads(snippet.get_text())
            logger.info(f"Start converting using {converter}")

            rows = document.select(str(converter.get("rows", "")))
            logger.info(f"Found {len(rows)} rows")
            converted: list[dict[str, str]] = []
            for _, el in enumerate(rows):
                kv: dict[str, str] = {}
                for col in converter.get("columns", []):
                    name = col.get("name")
                    selector = col.get("selector")
                    attribute = col.get("attribute")
                    if not name or not selector:
                        continue
                    item = el.select_one(str(selector))
                    if item:
                        if attribute:
                            value = item.get(attribute)
                            if isinstance(value, list):
                                value = value[0] if value else None
                            if isinstance(value, str):
                                kv[name] = value.strip()
                        else:
                            kv[name] = item.get_text(strip=True)
                if len(kv.keys()) > 0:
                    converted.append(kv)
            logger.info(f"Conversion done for {len(converted)} entries.")
            return converted
        except Exception as error:
            logger.error(f"Conversion error: {str(error)}")


async def ask(message: str, mask: str | None = None) -> str:
    if mask:
        return pwinput.pwinput(f"{message}: ", mask=mask)
    else:
        return input(f"{message}: ")


async def autofill(page: Page, distilled: str, fields: list[str]):
    document = BeautifulSoup(distilled, "html.parser")
    root = document.find("html")
    domain = None
    if root:
        domain = cast(Tag, root).get("gg-domain")

    for field in fields:
        element = document.find("input", {"type": field})
        selector = None
        frame_selector = None

        if element:
            selector, frame_selector = get_selector(str(cast(Tag, element).get("gg-match")))

        if selector:
            source = f"{domain}_{field}" if domain else field
            key = source.upper()
            value = os.getenv(key)

            if value and len(value) > 0:
                logger.info(f"Using {key} for {field}")

                if frame_selector:
                    await page.frame_locator(str(frame_selector)).locator(str(selector)).fill(value)
                else:
                    await page.fill(str(selector), value)
            else:
                placeholder = cast(Tag, element).get("placeholder")
                prompt = str(placeholder) if placeholder else f"Please enter {field}"
                mask = "*" if field == "password" else None

                if frame_selector:
                    await (
                        page.frame_locator(str(frame_selector))
                        .locator(str(selector))
                        .fill(await ask(prompt, mask))
                    )

                else:
                    await page.fill(str(selector), await ask(prompt, mask))
            await asyncio.sleep(0.25)


async def locate(locator: Locator) -> Locator | None:
    count = await locator.count()
    if count > 0:
        for i in range(count):
            el = locator.nth(i)
            if await el.is_visible():
                return el
    return None


async def click(
    page: Page, selector: str, timeout: int = 3000, frame_selector: str | None = None
) -> None:
    LOCATOR_ALL_TIMEOUT = 100
    if frame_selector:
        locator = page.frame_locator(str(frame_selector)).locator(str(selector))
    else:
        locator = page.locator(str(selector))
    try:
        elements = await locator.all()
        logger.debug(f'Found {len(elements)} elements for selector "{selector}"')
        for element in elements:
            logger.debug(f"Checking {element}")
            if await element.is_visible():
                logger.debug(f"Clicking on {element}")
                try:
                    await element.click()
                    return
                except Exception as err:
                    logger.warning(f"Failed to click on {selector} {element}: {err}")
    except Exception as e:
        if timeout > 0 and "TimeoutError" in str(type(e)):
            logger.warning(f"retrying click {selector} {timeout}")
            await click(page, selector, timeout - LOCATOR_ALL_TIMEOUT, frame_selector)
            return
        logger.error(f"Failed to click on {selector}: {e}")
        raise e


async def autoclick(page: Page, distilled: str):
    document = BeautifulSoup(distilled, "html.parser")
    buttons = document.find_all(attrs={"gg-autoclick": True})

    for button in buttons:
        if isinstance(button, Tag):
            selector, frame_selector = get_selector(str(button.get("gg-match")))
            if selector:
                logger.info(f"Auto-clicking {selector}")
                if isinstance(frame_selector, list):
                    frame_selector = str(frame_selector[0]) if frame_selector else None
                await click(page, str(selector), frame_selector=frame_selector)


async def terminate(page: Page, distilled: str) -> bool:
    document = BeautifulSoup(distilled, "html.parser")
    stops = document.find_all(attrs={"gg-stop": True})
    if len(stops) > 0:
        logger.info("Found stop elements, terminating session...")
        return True
    return False


def load_distillation_patterns(path: str) -> list[Pattern]:
    patterns: list[Pattern] = []
    for name in glob(path, recursive=True):
        with open(name, "r", encoding="utf-8") as f:
            content = f.read()
        patterns.append(Pattern(name=name, pattern=BeautifulSoup(content, "html.parser")))
    return patterns


async def distill(hostname: str | None, page: Page, patterns: list[Pattern]) -> Match | None:
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
        matches: list[Locator] = []
        targets = pattern.find_all(attrs={"gg-match": True}) + pattern.find_all(
            attrs={"gg-match-html": True}
        )

        for target in targets:
            if not isinstance(target, Tag):
                continue

            html = target.get("gg-match-html")
            selector, frame_selector = get_selector(str(html if html else target.get("gg-match")))

            if not selector:
                continue

            if frame_selector:
                source = await locate(page.frame_locator(str(frame_selector)).locator(selector))
            else:
                source = await locate(page.locator(selector))

            if source:
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
                    raw_text = await source.text_content()
                    if raw_text:
                        target.string = raw_text.strip()
                matches.append(source)
            else:
                optional = target.get("gg-optional") is not None
                logger.debug(f"Optional {selector} has no match")
                if not optional:
                    found = False

        if found and len(matches) > 0:
            distilled = str(pattern)
            result.append(
                Match(
                    name=name,
                    priority=priority,
                    distilled=distilled,
                    matches=matches,
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
    location: str,
    patterns: list[Pattern],
    fields: list[str] = [],
    browser_profile: BrowserProfile | None = None,
):
    if len(patterns) == 0:
        logger.error("No distillation patterns provided")
        raise ValueError("No distillation patterns provided")

    hostname = urllib.parse.urlparse(location).hostname or ""

    # Use provided profile, or try to get from MCP context, or create new one
    if browser_profile:
        profile = browser_profile
    else:
        profile = get_mcp_browser_profile() or BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()

        logger.info(f"Starting browser {profile.id}")
        logger.info(f"Navigating to {location}")
        await page.goto(location)

        TICK = 1  # seconds
        TIMEOUT = 15  # seconds
        max = TIMEOUT // TICK

        current = Match(name="", priority=-1, distilled="", matches=[])

        for iteration in range(max):
            logger.info("")
            logger.info(f"Iteration {iteration + 1} of {max}")
            await asyncio.sleep(TICK)

            match = await distill(hostname, page, patterns)
            if match:
                if match.distilled == current.distilled:
                    logger.debug(f"Still the same: {match.name}")
                else:
                    current = match
                    print()
                    print(current.distilled)
                    await autofill(page, current.distilled, fields)
                    await autoclick(page, current.distilled)
                    if await terminate(page, current.distilled):
                        converted = await convert(current.distilled)
                        if converted:
                            return converted
                        break

            else:
                logger.debug(f"No matched pattern found")

        return current.distilled
