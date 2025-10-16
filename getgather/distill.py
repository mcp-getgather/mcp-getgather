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

from getgather.browser.page_provider import (
    IncognitoPageProvider,
    PageProvider,
    SharedBrowserPageProvider,
)
from getgather.browser.profile import BrowserProfile
from getgather.logs import logger


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


ConversionResult = list[dict[str, str | list[str]]]


def get_selector(input_selector: str | None) -> tuple[str | None, str | None]:
    pattern = r"^(iframe(?:[^\s]*\[[^\]]+\]|[^\s]+))\s+(.+)$"
    if not input_selector:
        return None, None
    match = re.match(pattern, input_selector)
    if not match:
        return input_selector, None
    return match.group(2), match.group(1)


def extract_value(item: Tag, attribute: str | None = None) -> str:
    if attribute:
        value = item.get(attribute)
        if isinstance(value, list):
            value = value[0] if value else ""
        return value.strip() if isinstance(value, str) else ""
    return item.get_text(strip=True)


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
            converted: ConversionResult = []
            for _, el in enumerate(rows):
                kv: dict[str, str | list[str]] = {}
                for col in converter.get("columns", []):
                    name = col.get("name")
                    selector = col.get("selector")
                    attribute = col.get("attribute")
                    kind = col.get("kind")
                    if not name or not selector:
                        continue

                    if kind == "list":
                        items = el.select(str(selector))
                        kv[name] = [extract_value(item, attribute) for item in items]
                        continue

                    item = el.select_one(str(selector))
                    if item:
                        kv[name] = extract_value(item, attribute)
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


async def autofill(page: Page, distilled: str):
    document = BeautifulSoup(distilled, "html.parser")
    root = document.find("html")
    domain = None
    if root:
        domain = cast(Tag, root).get("gg-domain")

    processed: list[str] = []

    for element in document.find_all("input", {"type": True}):
        if not isinstance(element, Tag):
            continue

        input_type = element.get("type")
        name = element.get("name")

        if not name or (isinstance(name, str) and len(name) == 0):
            logger.warning(f"There is an input (of type {input_type}) without a name!")

        selector, frame_selector = get_selector(str(element.get("gg-match", "")))
        if not selector:
            logger.warning(f"There is an input (of type {input_type}) without a selector!")
            continue

        if input_type in ["email", "tel", "text", "password"]:
            field = name or input_type
            logger.debug(f"Autofilling type={input_type} name={name}...")

            source = f"{domain}_{field}" if domain else field
            key = str(source).upper()
            value = os.getenv(key)

            if value and len(value) > 0:
                logger.info(f"Using {key} for {field}")
                if frame_selector:
                    await page.frame_locator(str(frame_selector)).locator(str(selector)).fill(value)
                else:
                    await page.fill(str(selector), value)
                element["value"] = value
            else:
                placeholder = element.get("placeholder")
                prompt = str(placeholder) if placeholder else f"Please enter {field}"
                mask = "*" if input_type == "password" else None
                user_input = await ask(prompt, mask)
                if frame_selector:
                    await (
                        page.frame_locator(str(frame_selector))
                        .locator(str(selector))
                        .fill(user_input)
                    )
                else:
                    await page.fill(str(selector), user_input)
                element["value"] = user_input
            await asyncio.sleep(0.25)
        elif input_type == "radio":
            if not name:
                logger.warning(f"There is no name for radio button with id {element.get('id')}!")
                continue
            if name in processed:
                continue
            processed.append(str(name))

            choices: list[dict[str, str]] = []
            print()
            radio_buttons = document.find_all("input", {"type": "radio"})
            for button in radio_buttons:
                if not isinstance(button, Tag):
                    continue
                if button.get("name") != name:
                    continue
                button_id = button.get("id")
                label_element = (
                    document.find("label", {"for": str(button_id)}) if button_id else None
                )
                label = label_element.get_text() if label_element else None
                choice_id = str(button_id) if button_id else ""
                choice_label = label or str(button_id) if button_id else ""
                choices.append({"id": choice_id, "label": choice_label})
                print(f" {len(choices)}. {choice_label}")

            choice = 0
            while choice < 1 or choice > len(choices):
                answer = await ask(f"Your choice (1-{len(choices)})")
                try:
                    choice = int(answer)
                except ValueError:
                    choice = 0

            logger.info(f"Choosing {choices[choice - 1]['label']}")
            print()

            selected_choice = choices[choice - 1]
            radio = document.find("input", {"type": "radio", "id": selected_choice["id"]})
            if radio and isinstance(radio, Tag):
                selector, frame_selector = get_selector(str(radio.get("gg-match")))
                if frame_selector:
                    await page.frame_locator(str(frame_selector)).locator(str(selector)).check()
                else:
                    await page.check(str(selector))

        elif input_type == "checkbox":
            checked = element.get("checked")
            if checked is not None:
                logger.info(f"Checking {name}")
                if frame_selector:
                    await page.frame_locator(str(frame_selector)).locator(str(selector)).check()
                else:
                    await page.check(str(selector))

    return str(document)


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


async def autoclick(page: Page, distilled: str, expr: str):
    document = BeautifulSoup(distilled, "html.parser")
    elements = document.select(expr)
    for el in elements:
        selector, frame_selector = get_selector(str(el.get("gg-match")))
        if selector:
            logger.info(f"Clicking {selector}")
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
        print("RESULT", result)
        match = result[0]
        logger.info(f"✓ Best match: {match.name}")
        return match


async def run_distillation_loop(
    location: str,
    patterns: list[Pattern],
    browser_profile: BrowserProfile | None = None,
    timeout: int = 15,
    interactive: bool = True,
    with_terminate_flag: bool = False,
    page_provider: PageProvider | None = None,
) -> dict[str, str | ConversionResult | None | bool] | str | ConversionResult:
    if len(patterns) == 0:
        logger.error("No distillation patterns provided")
        raise ValueError("No distillation patterns provided")

    hostname = urllib.parse.urlparse(location).hostname or ""

    created_page_provider = False
    if page_provider is None:
        if browser_profile is None:
            page_provider = await IncognitoPageProvider.create()
            profile_id = "incognito"
        else:
            page_provider = await SharedBrowserPageProvider.create(
                browser_profile, stop_on_shutdown=True
            )
            profile_id = browser_profile.id
        created_page_provider = True
    else:
        profile_id = browser_profile.id if browser_profile else "custom"

    page = await page_provider.new_page()
    try:
        logger.info(f"Starting browser {profile_id}")
        logger.info(f"Navigating to {location}")
        await page.goto(location)

        TICK = 1  # seconds
        max = timeout // TICK

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
                    distilled = match.distilled
                    current = match
                    print()
                    print(distilled)

                    if await terminate(page, distilled):
                        converted = await convert(distilled)
                        if with_terminate_flag:
                            return {
                                "terminated": True,
                                "result": converted if converted else distilled,
                            }
                        else:
                            return converted if converted else distilled

                    if interactive:
                        distilled = await autofill(page, distilled)
                        await autoclick(page, distilled, "[gg-autoclick]:not(button)")
                        await autoclick(
                            page, distilled, "button[gg-autoclick], button[type=submit]"
                        )
                        current.distilled = distilled

            else:
                logger.debug(f"No matched pattern found")

        if with_terminate_flag:
            return {"terminated": False, "result": current.distilled}
        else:
            return current.distilled
    finally:
        await page_provider.close_page(page)
        if created_page_provider:
            await page_provider.shutdown()
