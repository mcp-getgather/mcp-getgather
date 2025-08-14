from __future__ import annotations

import copy
import os
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self

import sentry_sdk
from patchright.async_api import async_playwright
from pydantic import BaseModel, Field as pyField, PrivateAttr, computed_field
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from getgather.config import settings
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.connectors.spec_models import BrandSpec, Flow, PageSpec
from getgather.logs import logger
from getgather.sentry import attach_to_sentry

if TYPE_CHECKING:
    from getgather.detect import PageDetectResult


class InputPrompt(BaseModel):
    name: str
    prompt: str | None = None
    label: str | None = None
    type: str | None = None
    options: list[str] | None = None  # for dynamic selection prompts


class ChoicePrompt(BaseModel):
    name: str
    prompt: str | None = None
    groups: list[InputPrompt]
    prompts: list[InputPrompt]  # TODO: replaced by groups by keeping it until clients are updated
    message: str | None = None


class StatePrompt(BaseModel):
    name: str
    prompt: str
    choices: list[ChoicePrompt]

    @classmethod
    def from_legacy_prompts(cls, prompts: list[InputPrompt]) -> Self:
        """Backwards compatibility for legacy step prompts."""
        return cls(
            name="", prompt="", choices=[ChoicePrompt(name="", groups=prompts, prompts=prompts)]
        )

    @cached_property
    def choices_map(self) -> dict[str, ChoicePrompt]:
        return {group.name: group for group in self.choices}


class Bundle(BaseModel):
    name: str
    content: str


class FlowState(BaseModel):
    _state_records_: ClassVar[list[dict[str, Any]]] = []

    # private attributes that should not be set directly
    _spec: BrandSpec | None = PrivateAttr(default=None)
    _finished: bool = PrivateAttr(default=False)
    _prompt: StatePrompt | None = PrivateAttr(default=None)
    _field_detections: dict[str, bool] | None = PrivateAttr(default=None)
    _page_detections: list[PageDetectResult] | None = PrivateAttr(default=None)

    # internal states
    browser_profile_id: str | None = pyField(exclude=True, default=None)
    brand_id: BrandIdEnum | None = pyField(exclude=True, default=None)
    type: Literal["auth", "extract"] = pyField(exclude=True, default="auth")

    paused: str | None = pyField(exclude=True, default=None)
    bundle_dir: Path | None = pyField(exclude=True, default=None)

    # fields returned to client and sent back to continue the flow
    step_index: int = 0
    current_page_spec_name: str | None = None
    inputs: dict[str, str] = pyField(default_factory=dict)
    error: str | None = None
    bundle: Bundle | None = None

    async def init(self, *, browser_profile_id: str, brand_id: BrandIdEnum | None = None):
        if self._spec:
            return

        self.browser_profile_id = browser_profile_id

        if brand_id:
            if self.brand_id:
                assert self.brand_id == brand_id, "Brand ID mismatch"
            else:
                self.brand_id = brand_id

        assert self.brand_id, "brand_id is required to initialize the flow state"

        from getgather.connectors.spec_loader import load_brand_spec

        self._spec = await load_brand_spec(self.brand_id)
        self._record(event="input")

    @property
    def spec(self) -> BrandSpec:
        assert self._spec, "Spec must be initialized before accessing spec"
        return self._spec

    @computed_field
    @property
    def brand_name(self) -> str:
        return self.spec.name

    @property
    def flow(self) -> Flow:
        match self.type:
            case "auth":
                return self.spec.auth
            case "extract":
                assert self.spec.extract, f"Extract flow is not defined for brand {self.brand_id}"
                return self.spec.extract
            case _:
                raise ValueError(f"Invalid flow type: {self.type}")

    @property
    def current_page_spec(self) -> PageSpec:
        assert self.current_page_spec_name, "current page is not set yet"
        assert self._spec, "Spec must be initialized before accessing current_page_spec"

        page_spec = next(
            (p for p in self.flow.pages if p.name == self.current_page_spec_name), None
        )
        if not page_spec:
            raise ValueError(
                f"Page spec '{self.current_page_spec_name}' not found in spec '{self._spec.name}'"
            )

        return page_spec

    @property
    def finished(self) -> bool:
        return self._finished

    async def set_finished(self, value: bool):
        self._finished = value
        if value:
            self._record(event="finished")
            await self.log_records(sentry=False)

    @computed_field
    @property
    def prompt(self) -> StatePrompt | None:
        return self._prompt

    @prompt.setter
    def prompt(self, value: StatePrompt | None):
        self._prompt = value
        self._record(event="prompt" if value else "next_page")

    @property
    def field_detections(self) -> dict[str, bool]:
        assert self._field_detections, "Field detections must be set before accessing"
        return self._field_detections

    @field_detections.setter
    def field_detections(self, value: dict[str, bool]):
        self._field_detections = value
        self._record(event="detect_fields")

    @property
    def page_detections(self) -> list[PageDetectResult]:
        assert self._page_detections, "Page detections must be set before accessing"
        return self._page_detections

    @page_detections.setter
    def page_detections(self, value: list[PageDetectResult]):
        self._page_detections = value
        self._record(event="detect_pages")

    def _record(
        self,
        *,
        event: Literal["input", "detect_fields", "detect_pages", "prompt", "next_page", "finished"],
    ):
        if self.type != "auth":
            return

        if event == "input" and self.step_index == 0 and self.current_page_spec_name is None:
            FlowState._state_records_.clear()

        record = self.model_dump(exclude={"brand_name", "bundle", "step_index"})
        record["event"] = event

        # Scrub password fields from inputs before recording
        scrubbed_inputs = copy.deepcopy(self.inputs)
        for key in scrubbed_inputs:
            if "password" in key.lower():
                scrubbed_inputs[key] = "***SCRUBBED***"
        record["inputs"] = scrubbed_inputs

        if event.startswith("detect_"):
            record["field_detections"] = copy.deepcopy(self._field_detections)

        if event == "detect_pages":
            record["page_detections"] = (
                [d.model_dump() for d in self._page_detections] if self._page_detections else None
            )

        if event == "prompt":
            record["prompt"] = self._prompt.model_dump() if self._prompt else None

        FlowState._state_records_.append(record)

        logger.debug(f"🔍 FSM event: {JSON.from_data(record, indent=2).text}")

    async def log_records(
        self, *, sentry: bool = False, sentry_scope: sentry_sdk.Scope | None = None
    ):
        if self.type != "auth":
            return

        all_columns = set(key for record in FlowState._state_records_ for key in record.keys())
        sorted_columns = ["event", "current_page_spec_name"]
        sorted_columns.extend(sorted(all_columns - set(sorted_columns)))

        table = Table(show_header=True, header_style="bold", show_lines=True)
        for key in sorted_columns:
            table.add_column(key, overflow="fold", no_wrap=False)
        for record in FlowState._state_records_:
            cells: list[JSON] = []
            for key in sorted_columns:
                js = JSON.from_data(record.get(key), indent=2)

                # override the no_wrap / overflow that JSON.from_data set
                js.text.overflow = "fold"
                js.text.no_wrap = False

                cells.append(js)
            table.add_row(*cells)

        # save the output as a html file, use a wider console to avoid text wrapping
        console = Console(width=400, record=True, file=open(os.devnull, "wt"))
        console.print(table)
        html_path = settings.screenshots_dir / f"flow_states_{self.browser_profile_id}.html"
        console.save_html(str(html_path))
        logger.info(f"Saved flow state records to file://{html_path.resolve()}")

        # attach to sentry
        if sentry and settings.SENTRY_DSN:
            image_path = settings.screenshots_dir / f"flow_states_{self.browser_profile_id}.jpg"
            async with async_playwright() as pw:
                browser = await pw.chromium.launch()
                page = await browser.new_page()
                await page.goto(f"file://{html_path.resolve()}")
                await page.screenshot(path=image_path, full_page=True)
                await browser.close()

            attach_to_sentry(image_path, scope=sentry_scope)
            logger.info(f"Saved flow state records to sentry and file://{image_path.resolve()}")
