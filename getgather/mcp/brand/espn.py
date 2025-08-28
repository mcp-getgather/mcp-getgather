import re
from typing import Any

from getgather.brand_state import brand_state_manager
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.mcp.registry import BrandMCPBase

espn_mcp = BrandMCPBase(brand_id="espn", name="ESPN MCP")


@espn_mcp.tool()
async def get_college_football_games() -> list[dict[str, Any]]:
    """Get information about college football games from ESPN."""
    return await extract_college_football_schedule()


async def extract_college_football_schedule() -> list[dict[str, Any]]:
    """
    Extract college football games from ESPN schedule page

    Args:
        page: Playwright Page object already navigated to ESPN CFB schedule

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

        for table_index in range(await schedule_tables.count()):
            table = schedule_tables.nth(table_index)

            # Get the date from table title
            date_element = table.locator(".Table__Title")
            date = (
                (await date_element.inner_text()).strip()
                if (await date_element.count()) > 0
                else "Unknown Date"
            )
            print(f"Date: {date}")

            # Find all game rows in this table
            game_rows = table.locator("tbody tr")

            for row_index in range(await game_rows.count()):
                row = game_rows.nth(row_index)
                print(f"Row: {row}")

                try:
                    game_data = {
                        "date": date,
                        "away_team": "",
                        "away_rank": "",
                        "home_team": "",
                        "home_rank": "",
                        "time": "",
                        # "tv": "",
                        "location": "",
                        "status": "",
                        "result": "",
                        "betting_line": "",
                        "over_under": "",
                    }

                    # Extract away team information
                    print("Extracting away team information")
                    away_team_cell = row.locator(".events__col")
                    if await away_team_cell.count() > 0:
                        # Get team name - look for text-containing anchor (not logo)
                        away_links = away_team_cell.locator("a")
                        for i in range(await away_links.count()):
                            link = away_links.nth(i)
                            link_text = (await link.inner_text()).strip()
                            if link_text and not link_text.isspace():  # Skip empty/logo links
                                game_data["away_team"] = link_text
                                print(f"Away team: {link_text}")
                                break

                        # Get ranking if exists
                        rank_element = away_team_cell.locator(".rank")
                        if await rank_element.count() > 0:
                            game_data["away_rank"] = (await rank_element.inner_text()).strip()
                            print(f"Away rank: {game_data['away_rank']}")

                    # Extract home team information
                    print("Extracting home team information")
                    home_team_cell = row.locator(".colspan__col")
                    if await home_team_cell.count() > 0:
                        # Get team name - look for text-containing anchor (not logo)
                        home_links = home_team_cell.locator("a")
                        for i in range(await home_links.count()):
                            link = home_links.nth(i)
                            link_text = (await link.inner_text()).strip()
                            if link_text and not link_text.isspace():  # Skip empty/logo links
                                game_data["home_team"] = link_text
                                print(f"Home team: {link_text}")
                                break

                        # Get ranking if exists
                        rank_element = home_team_cell.locator(".rank")
                        if await rank_element.count() > 0:
                            game_data["home_rank"] = (await rank_element.inner_text()).strip()
                            print(f"Home rank: {game_data['home_rank']}")

                    # Extract time/status information
                    print("Extracting time/status information")
                    time_cell = row.locator("td").nth(2)  # Third column
                    if await time_cell.count() > 0:
                        time_text = (await time_cell.inner_text()).strip()
                        if "LIVE" in time_text:
                            game_data["status"] = "LIVE"
                        else:
                            game_data["time"] = time_text
                            print(f"Time: {game_data['time']}")

                    # Check if this is a completed game (has result instead of time)
                    print("Checking if this is a completed game")
                    result_links = time_cell.locator("a")
                    if await result_links.count() > 0:
                        # Get the first link that has meaningful text
                        for i in range(await result_links.count()):
                            link = result_links.nth(i)
                            result_text = (await link.inner_text()).strip()
                            if result_text and any(char.isalnum() for char in result_text):
                                game_data["result"] = result_text
                                game_data["status"] = "FINAL"
                                print(f"Result: {game_data['result']}")
                                break

                    # Extract TV information
                    # tv_cell = row.locator(".broadcast__col")
                    # if await tv_cell.count() > 0:
                    #     # Try to get network name from image alt text or div text
                    #     network_img = tv_cell.locator("img")
                    #     if await network_img.count() > 0:
                    #         alt_text = await network_img.get_attribute("alt")
                    #         game_data["tv"] = alt_text or ""
                    #     else:
                    #         # Fallback to div text
                    #         network_div = tv_cell.locator(".network-name, div")
                    #         if await network_div.count() > 0:
                    #             game_data["tv"] = (await network_div.first.inner_text()).strip()

                    # Extract location information
                    print("Extracting location information")
                    location_cell = row.locator(".venue__col")
                    if await location_cell.count() > 0:
                        location_link = location_cell.locator("a")
                        if await location_link.count() > 0:
                            location_text = (await location_link.inner_text()).strip()
                            # Remove the external link icon from the text
                            game_data["location"] = re.sub(r"\s*", "", location_text)
                            print(f"Location: {game_data['location']}")
                    # Only add games that have at least team information
                    if game_data["away_team"] and game_data["home_team"]:
                        games.append(game_data)

                except Exception as e:
                    print(f"Error processing row {row_index} in table {table_index}: {e}")
                    continue

    return games
