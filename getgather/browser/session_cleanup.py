"""
Session cleanup scheduler using the schedule library for automatically stopping browser sessions after one hour.
"""

from datetime import datetime, timedelta

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession, LaunchedProfile
from getgather.logs import logger


async def cleanup_old_sessions():
    """Check for and stop sessions that have been running too long."""
    logger.info("Checking for old sessions to stop")
    current_time = datetime.now()
    max_session_age = timedelta(minutes=30)
    sessions_to_stop: list[LaunchedProfile] = []

    launched_sessions = BrowserSession.get_launched_profile_ids()

    logger.info(f"Found {len(launched_sessions)} launched sessions")

    # Find sessions that are older than max_session_age
    for launched_session in launched_sessions:
        if launched_session.launched_at is None:
            logger.warning(
                f"Session {launched_session.profile_id} has no launch time, skipping cleanup check"
            )
            continue

        session_age = current_time - launched_session.launched_at
        if session_age > max_session_age:
            logger.info(
                f"Session {launched_session.profile_id} is older than 30 minutes, stopping it"
            )
            session = BrowserSession.get(BrowserProfile(id=launched_session.profile_id))
            if session:
                sessions_to_stop.append(launched_session)

    for launched_profile in sessions_to_stop:
        try:
            logger.info(f"Stopping session {launched_profile.profile_id}")
            session = BrowserSession.get(BrowserProfile(id=launched_profile.profile_id))
            await session.stop()
            logger.info(f"Successfully stopped session {launched_profile.profile_id}")
        except Exception as e:
            logger.error(f"Failed to stop session {launched_profile.profile_id}: {e}")

    if sessions_to_stop:
        logger.info(f"Cleaned up {len(sessions_to_stop)} old sessions")
