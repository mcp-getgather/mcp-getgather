"""
Session cleanup scheduler using the schedule library for automatically stopping browser sessions after one hour.
"""

from datetime import datetime, timedelta

from getgather.browser.session import BrowserSession
from getgather.logs import logger


async def cleanup_old_sessions():
    """Check for and stop sessions that have been running too long."""
    logger.info("Checking for old sessions to stop")
    current_time = datetime.now()
    max_session_age = timedelta(minutes=30)
    browser_sessions = BrowserSession.get_all_sessions()

    logger.info(f"Found {len(browser_sessions)} browser sessions")

    # Find sessions that are older than max_session_age
    for browser_session in browser_sessions:
        if browser_session.launched_at is None:
            logger.warning(
                f"Session {browser_session.profile.id} has no launch time, skipping cleanup check"
            )
            continue

        session_age = current_time - browser_session.launched_at
        if session_age > max_session_age:
            try:
                logger.info(
                    f"Session {browser_session.profile} is older than 30 minutes, stopping it"
                )
                await browser_session.stop()
                logger.info(f"Successfully stopped session {browser_session.profile.id}")
            except Exception as e:
                logger.error(f"Failed to stop session {browser_session.profile.id}: {e}")
