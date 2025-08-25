import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from patchright.async_api import BrowserContext, Page
from pydantic import BaseModel

from getgather.config import settings
from getgather.logs import logger


def _is_csp_domain(domain: str) -> bool:
    """Check if domain matches any CSP website patterns."""
    for pattern in settings.CSP_WEBSITES:
        if pattern.startswith("*."):
            # Wildcard pattern: *.example.com matches subdomain.example.com
            base_domain = pattern[2:]
            if domain.endswith(base_domain):
                return True
        else:
            # Exact or substring match
            if pattern in domain:
                return True
    return False


class RRWebInjector:
    """Handles RRWeb script injection for browser pages."""

    def __init__(self):
        self.script_url = settings.RRWEB_SCRIPT_URL
        self.mask_all_inputs = settings.RRWEB_MASK_ALL_INPUTS
        self.enabled = settings.ENABLE_RRWEB_RECORDING
        self.injected_contexts: set[BrowserContext] = set()
        self.events: list[Any] = []

    async def save_event(self, event: dict[str, Any]) -> None:
        """Save an rrweb event from browser."""
        self.events.append(event)

    def flush_events(self) -> list[Any]:
        """Return the events and reset events to empty list"""
        try:
            return self.events
        finally:
            self.events = []

    async def inject_into_page(self, page: Page):
        if self._should_inject_for_page(page):
            await page.add_script_tag(url=self.script_url)
            await page.evaluate(
                "() => { rrwebRecord({ emit(event) { window.saveEvent(event); }, maskAllInputs: true }); }",
                isolated_context=False,
            )

    def _should_inject_for_page(self, page: Page) -> bool:
        """Determine if RRWeb should be injected for this page."""
        if not self.enabled:
            return False

        url = page.url
        if not url or url == "about:blank":
            return False

        domain = urlparse(url).hostname
        if not domain:
            return False

        if _is_csp_domain(domain):
            logger.info(f"Skipping RRWeb injection for CSP domain: {domain}")
            return False

        return True


class Recording(BaseModel):
    """Recording response model for API."""

    activity_id: str
    events: list[dict[str, Any]]


class RRWebManager:
    """Per-activity file-based RRWeb recording management."""

    def __init__(self, recordings_dir: Path):
        self.recordings_dir = recordings_dir

    def _get_activity_file_path(self, activity_id: str) -> Path:
        """Get the file path for an activity's recording."""
        return self.recordings_dir / f"activity_{activity_id}.json"

    def _load_activity_recording(self, activity_id: str) -> Recording | None:
        """Load recording for a specific activity."""
        file_path = self._get_activity_file_path(activity_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return None
                data = json.loads(content)
                return Recording.model_validate(data)
        except (json.JSONDecodeError, OSError):
            return None

    def _save_activity_recording(self, recording: Recording) -> None:
        """Save recording for a specific activity."""
        file_path = self._get_activity_file_path(recording.activity_id)

        with open(file_path, "w") as f:
            json.dump(recording.model_dump(), f, indent=2, default=str)

    async def save_recording(self, activity_id: str) -> None:
        """Add an RRWeb event to an activity."""
        events = rrweb_injector.flush_events()
        if len(events) > 0:
            recording = Recording(activity_id=activity_id, events=events)
            self._save_activity_recording(recording)

    async def get_recording_by_activity_id(self, activity_id: str) -> Recording | None:
        """Get recording by activity ID."""
        return self._load_activity_recording(activity_id)

    async def activity_has_recording(self, activity_id: str) -> bool:
        """Check if activity has recording."""
        file_path = self._get_activity_file_path(activity_id)
        return file_path.exists()


# Global instances
rrweb_manager = RRWebManager(settings.recordings_dir)
rrweb_injector = RRWebInjector()
