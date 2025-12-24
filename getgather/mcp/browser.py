import zendriver as zd


class BrowserManager:
    """Manages browser instances."""

    def __init__(self):
        self._incognito_browsers: dict[str, zd.Browser] = {}
        self._zen_global_browser: zd.Browser | None = None

    def get_incognito_browser(self, id: str) -> zd.Browser | None:
        """Get an incognito browser by ID."""
        return self._incognito_browsers.get(id)

    def set_incognito_browser(self, id: str, browser: zd.Browser) -> None:
        """Set an incognito browser by ID."""
        self._incognito_browsers[id] = browser

    def has_incognito_browser(self, id: str) -> bool:
        """Check if an incognito browser exists by ID."""
        return id in self._incognito_browsers

    def get_global_browser(self) -> zd.Browser | None:
        """Get the global browser instance."""
        return self._zen_global_browser

    def set_global_browser(self, browser: zd.Browser) -> None:
        """Set the global browser instance."""
        self._zen_global_browser = browser


browser_manager = BrowserManager()
