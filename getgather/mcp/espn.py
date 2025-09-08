import os
from typing import Any

from fastmcp import Context, FastMCP

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.distill import load_distillation_patterns, run_distillation_loop

espn_mcp = FastMCP[Context](name="ESPN MCP")

SCHEDULE_URL = "https://www.espn.com/college-football/schedule"


@espn_mcp.tool
async def get_schedule(ctx: Context) -> dict[str, Any]:
    """Get the week's college footballschedule from ESPN."""

    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    schedule = await run_distillation_loop(SCHEDULE_URL, patterns)
    parsed_schedule = await parse_schedule(str(schedule))
    return {"schedule": parsed_schedule}


async def parse_schedule(schedule: str) -> dict[str, Any]:
    """Parse the schedule from ESPN."""
    profile = BrowserProfile()
    async with browser_session(profile) as session:
        page = await session.page()
        await page.set_content(schedule)
        # Find all schedule tables (one for each day)
        schedule_tables = page.locator('div[class*="ScheduleTables"]')

        # Extract all games in a single in-page evaluation to minimize round-trips
        extracted_games = await schedule_tables.evaluate_all(
            r"""
            (nodes) => {
              const games = [];
              for (const table of nodes) {
                let date = "Unknown Date";
                const dateEl = table.querySelector(".Table__Title");
                if (dateEl) date = (dateEl.textContent || "").trim();
                const rows = table.querySelectorAll("tbody tr");
                rows.forEach((row) => {
                  const game = {
                    date,
                    away_team: "",
                    away_rank: "",
                    home_team: "",
                    home_rank: "",
                    time: "",
                    location: "",
                    status: "",
                    result: "",
                    betting_line: "",
                    over_under: "",
                  };
                  // Away team
                  const awayCell = row.querySelector(".events__col");
                  if (awayCell) {
                    const links = Array.from(awayCell.querySelectorAll("a"))
                      .map((a) => (a.textContent || "").trim())
                      .filter((t) => t && t.trim());
                    if (links.length) game.away_team = links[0];
                    const rankEl = awayCell.querySelector(".rank");
                    if (rankEl) game.away_rank = (rankEl.textContent || "").trim();
                  }
                  // Home team
                  const homeCell = row.querySelector(".colspan__col");
                  if (homeCell) {
                    const links = Array.from(homeCell.querySelectorAll("a"))
                      .map((a) => (a.textContent || "").trim())
                      .filter((t) => t && t.trim());
                    if (links.length) game.home_team = links[0];
                    const rankEl = homeCell.querySelector(".rank");
                    if (rankEl) game.home_rank = (rankEl.textContent || "").trim();
                  }
                  // Time / Status / Result
                  const tds = row.querySelectorAll("td");
                  const timeCell = tds && tds.length > 2 ? tds[2] : null;
                  if (timeCell) {
                    const timeText = (timeCell.textContent || "").trim();
                    if (timeText.includes("LIVE")) {
                      game.status = "LIVE";
                    } else {
                      game.time = timeText;
                    }
                    const resultLinks = Array.from(timeCell.querySelectorAll("a"));
                    for (const a of resultLinks) {
                      const t = (a.textContent || "").trim();
                      if (t && /[a-zA-Z0-9]/.test(t)) {
                        game.result = t;
                        game.status = "FINAL";
                        break;
                      }
                    }
                  }
                  // Location
                  const locationCell = row.querySelector(".venue__col");
                  if (locationCell) {
                    const locationLink = locationCell.querySelector("a");
                    if (locationLink) {
                      const locText = (locationLink.textContent || "").replace(/\s*/g, "");
                      game.location = locText;
                    }
                  }
                  if (game.away_team && game.home_team) {
                    games.push(game);
                  }
                });
              }
              return games;
            }
            """
        )
        return extracted_games
