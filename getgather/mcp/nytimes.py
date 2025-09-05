import os
from typing import Any

from fastmcp import Context, FastMCP

from getgather.distill import load_distillation_patterns, run_distillation_loop

nytimes_mcp = FastMCP[Context](name="NYTimes MCP")

BESTSELLERS_URL = "https://www.nytimes.com/books/best-sellers/"


@nytimes_mcp.tool
async def get_bestsellers_list(ctx: Context) -> dict[str, Any]:
    """Get the bestsellers list from NY Times."""

    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    best_sellers = await run_distillation_loop(BESTSELLERS_URL, patterns)
    return {"best_sellers": best_sellers}
