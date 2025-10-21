import os
from typing import Any, cast
from urllib.parse import urlparse, urlunparse

from fastmcp import Context

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import GatherMCP

npr_mcp = GatherMCP(brand_id="npr", name="NPR MCP")


@npr_mcp.tool
async def get_headlines(ctx: Context) -> dict[str, Any]:
    """Get the current news headlines from NPR."""

    location = "https://text.npr.org"
    path = os.path.join(os.path.dirname(__file__), "patterns", "**/npr-*.html")
    patterns = load_distillation_patterns(path)

    browser_profile = BrowserProfile()
    session = BrowserSession.get(browser_profile)
    session = await session.start()
    distilled, terminated = await run_distillation_loop(
        location, patterns, browser_profile, interactive=False
    )
    await session.context.close()

    if terminated:
        result_key = "headlines"
        result: dict[str, Any] = {result_key: distilled}
        if "headlines" in result:
            headlines_value = result["headlines"]
            if isinstance(headlines_value, list):
                for headline in cast(list[dict[str, Any]], headlines_value):
                    if "link" in headline:
                        link = cast(str, headline["link"])
                        parsed = urlparse(link)
                        netloc: str = parsed.netloc if parsed.netloc else "npr.org"
                        url: str = urlunparse((
                            "https",
                            netloc,
                            parsed.path,
                            parsed.params,
                            parsed.query,
                            parsed.fragment,
                        ))
                        headline["url"] = url
        return result

    raise ValueError("Failed to retrieve NPR headlines")
