from typing import Any

from getgather.brand_state import brand_state_manager
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.mcp.registry import BrandMCPBase

espn_mcp = BrandMCPBase(brand_id="espn", name="ESPN MCP")


@espn_mcp.tool()
async def get_college_football_games() -> list[dict[str, Any]]:
    """Get information about college football games from ESPN schedule page."""
    return await extract_college_football_schedule()


async def extract_college_football_schedule() -> list[dict[str, Any]]:
    """
    Extract college football games from ESPN schedule page

    Returns:
        List of dictionaries containing game information
    """
    if brand_state_manager.is_brand_connected(espn_mcp.brand_id):
        profile_id = brand_state_manager.get_browser_profile_id(espn_mcp.brand_id)
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    games: list[dict[str, Any]] = []
    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto(
            "https://www.espn.com/college-football/schedule/_/week/1/year/2025/seasontype/2"
        )
        await page.wait_for_selector("h1:has-text('College Football Schedule')")
        await page.wait_for_timeout(1000)

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

        games.extend(extracted_games)

    return games
