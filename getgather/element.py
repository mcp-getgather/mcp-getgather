import asyncio
import random

import zendriver as zd

from getgather.logs import logger


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

    async def check(self) -> None:
        logger.error("TODO: Element#check")
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
