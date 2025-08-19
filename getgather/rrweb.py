import json
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

from patchright.async_api import Page
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

    def _generate_injection_script(self) -> str:
        """Generate the JavaScript injection script."""
        return f"""
            // RRWeb recording script injection
            const rrwebScript = document.createElement('script');
            rrwebScript.src = '{self.script_url}';
            rrwebScript.onload = function() {{
                console.log('RRWeb script loaded');
                startRRWebRecording();
            }};
            document.head.appendChild(rrwebScript);

            function startRRWebRecording() {{
                if (typeof rrwebRecord !== 'undefined' && window.saveEvent) {{
                    rrwebRecord({{ 
                        emit(event) {{ 
                            window.saveEvent(event); 
                        }}, 
                        maskAllInputs: {str(self.mask_all_inputs).lower()}
                    }});
                    console.log('RRWeb recording started');
                }}
            }}
        """

    def should_inject_for_page(self, page: Page) -> bool:
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

    async def inject_into_page(
        self, page: Page, save_event_callback: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> bool:
        """Inject RRWeb recording into a page if conditions are met."""
        try:
            if not self.should_inject_for_page(page):
                return False

            # Expose save_event function to browser
            await page.expose_function("saveEvent", save_event_callback)  # type: ignore[reportUnknownMemberType]

            # Inject RRWeb recording script
            await page.add_init_script(self._generate_injection_script())

            logger.debug(f"RRWeb script injected for page: {page.url}")
            return True

        except Exception as e:
            logger.error(f"Failed to inject RRWeb script: {e}")
            return False


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

    async def add_event(self, activity_id: str, event: dict[str, Any]) -> None:
        """Add an RRWeb event to an activity."""
        recording = self._load_activity_recording(activity_id)

        if recording:
            # Add event to existing recording
            recording.events.append(event)
        else:
            # Create new recording with this event
            recording = Recording(activity_id=activity_id, events=[event])

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
