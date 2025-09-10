import os
from typing import Any

from fastmcp import Context, FastMCP

from getgather.distill import load_distillation_patterns, run_distillation_loop

espn_mcp = FastMCP[Context](name="ESPN MCP")

SCHEDULE_URL = "https://www.espn.com/college-football/schedule"


@espn_mcp.tool
async def get_schedule(ctx: Context) -> dict[str, Any]:
    """Get the week's college footballschedule from ESPN."""

    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    schedule = await run_distillation_loop(SCHEDULE_URL, patterns)
    return {"schedule": schedule}
