import os
from typing import Any, cast
from urllib.parse import urlparse, urlunparse

from fastmcp import Context

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import GatherMCP

groundnews_mcp = GatherMCP(brand_id="groundnews", name="Ground News MCP")


@groundnews_mcp.tool
async def get_stories(ctx: Context) -> dict[str, Any]:
    """Get the latest news stories from Ground News."""

    location = "https://ground.news"
    path = os.path.join(os.path.dirname(__file__), "patterns", "**/groundnews-*.html")
    patterns = load_distillation_patterns(path)

    browser_profile = BrowserProfile()
    session = BrowserSession.get(browser_profile)
    session = await session.start()
    distilled, terminated = await run_distillation_loop(
        location, patterns, browser_profile, interactive=False
    )
    await session.context.close()

    if terminated:
        result_key = "stories"
        result: dict[str, Any] = {result_key: distilled}
        if "stories" in result:
            stories_value = result["stories"]
            if isinstance(stories_value, list):
                for story in cast(list[dict[str, Any]], stories_value):
                    if "link" in story:
                        link = cast(str, story["link"])
                        parsed = urlparse(link)
                        netloc: str = parsed.netloc if parsed.netloc else "ground.news"
                        url: str = urlunparse((
                            "https",
                            netloc,
                            parsed.path,
                            parsed.params,
                            parsed.query,
                            parsed.fragment,
                        ))
                        story["url"] = url
        return result

    raise ValueError("Failed to retrieve Ground News stories")
