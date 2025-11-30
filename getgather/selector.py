import re
from typing import Protocol

import zendriver as zd

from getgather.element import Element


class Selector(Protocol):
    """Protocol for selector that handle different query types."""

    def can_handle(self, selector: str) -> bool:
        """Check if this can handle the given selector.

        Args:
            selector: The selector string to check

        Returns:
            True if this can process the selector, False otherwise
        """
        ...

    async def query(self, page: zd.Tab, selector: str, timeout: float = 0) -> Element | None:
        """Execute the query using this selector .

        Args:
            page: The Zendriver tab/page to query
            selector: The selector string to execute
            timeout: Query timeout in seconds

        Returns:
            An Element wrapper if found, None otherwise
        """
        ...


class XPath(Selector):
    """XPath selector for queries like //div[@id='foo']."""

    def can_handle(self, selector: str) -> bool:
        """XPath selectors start with '//'."""
        return selector.startswith("//")

    async def query(self, page: zd.Tab, selector: str, timeout: float = 0) -> Element | None:
        """Query using XPath selector."""

        elements = await page.xpath(selector, timeout)
        if elements and len(elements) > 0:
            return Element(elements[0], xpath_selector=selector)
        return None


class HasText(Selector):
    """Playwright :has-text() pseudo-selector.

    Supports selectors like:
    - h5:has-text("Cart")
    - button:has-text('Continue')
    - div.container:has-text("Total")

    Matching behavior:
    - Case-sensitive substring matching
    - Matches text in element or descendants
    - Trims whitespace from matched text
    """

    # TODO: think better regex
    # Regex to match :has-text() with single or double quotes
    HAS_TEXT_PATTERN = re.compile(r':has-text\(["\']([^"\']*)["\']\)')

    def can_handle(self, selector: str) -> bool:
        """:has-text() selectors contain the :has-text( substring."""
        return ":has-text(" in selector

    def parse_selector(self, selector: str) -> tuple[str, list[str]]:
        """Parse :has-text() selector into base CSS selector and text filters.

        Args:
            selector: Selector like 'h5:has-text("Cart")'

        Returns:
            Tuple of (base_css_selector, [text_filters])
            Example: ('h5', ['Cart'])

        Raises:
            ValueError: If selector is malformed
        """
        # Find all :has-text() occurrences
        matches = list(self.HAS_TEXT_PATTERN.finditer(selector))

        if not matches:
            raise ValueError(f"Malformed :has-text() selector: {selector}")

        # Extract text filters
        text_filters = [match.group(1) for match in matches]

        # Remove all :has-text() to get base CSS selector
        base_selector = self.HAS_TEXT_PATTERN.sub("", selector).strip()

        if not base_selector:
            raise ValueError(f"Selector must have a base element before :has-text(): {selector}")

        return base_selector, text_filters

    async def query(self, page: zd.Tab, selector: str, timeout: float = 0) -> Element | None:
        """Query elements matching base selector and filter by text content.

        Uses native Zendriver API to:
        1. Parse the selector to extract base CSS and text filter
        2. Query all elements matching the base CSS selector
        3. Filter by text content in Python
        4. Return the first matching element
        """
        base_selector, text_filters = self.parse_selector(selector)

        elements = await page.query_selector_all(base_selector)
        if not elements:
            return None

        # Filter elements by text content
        for elem in elements:
            # Get text content from the element
            text = elem.text.strip() if elem.text else ""

            # Check if all text filters match
            if all(text_filter in text for text_filter in text_filters):
                return Element(elem, css_selector=selector)

        return None


class CSS(Selector):
    """Standard CSS selector (fallback for all other selectors)."""

    def can_handle(self, selector: str) -> bool:
        """CSS handles everything that other don't."""
        return True

    async def query(self, page: zd.Tab, selector: str, timeout: float = 0) -> Element | None:
        """Query using standard CSS selector."""
        element = await page.select(selector, timeout=timeout)
        if element:
            return Element(element, css_selector=selector)
        return None


# Selector in priority order (first match wins)
SELECTORS: list[Selector] = [
    XPath(),
    HasText(),
    CSS(),
]
