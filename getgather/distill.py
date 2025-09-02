from bs4 import BeautifulSoup
from bs4.element import Tag
from patchright.async_api import Locator, Page
from pydantic import BaseModel

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


async def locate(locator: Locator) -> Locator | None:
    count = await locator.count()
    if count > 0:
        for i in range(count):
            el = locator.nth(i)
            if await el.is_visible():
                return el
    return None


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
            if isinstance(domain, str) and domain.lower() not in hostname.lower():
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
            selector = html if html else target.get("gg-match")

            if not selector or not isinstance(selector, str):
                continue

            frame_selector = target.get("gg-frame")

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
