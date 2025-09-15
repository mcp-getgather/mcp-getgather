import asyncio
import json
from typing import Any

from patchright.async_api import Frame, Page, TimeoutError

from getgather.actions import (
    get_label_text,
    handle_click,
    handle_fill_multi,
    handle_fill_single,
    handle_graphql_response,
    handle_navigate,
    handle_network_extraction,
    handle_select_option,
    wait_for_selector,
)
from getgather.connectors.spec_loader import BrandIdEnum, load_custom_functions
from getgather.connectors.spec_models import Choice, Field
from getgather.detect import PageSpecDetector
from getgather.flow_state import Bundle, ChoicePrompt, FlowState, InputPrompt, PageSpec, StatePrompt
from getgather.logs import logger


async def handle_field_prompt(page: Page, field: Field) -> InputPrompt:
    prompt_to_return = InputPrompt(
        name=field.name,
        prompt=field.prompt,
        label=field.label,
        type=field.type,
    )

    # If this is a selection field, capture dynamic option labels.
    if field.type == "selection" and field.option_items:
        locator = page.locator(field.option_items)
        count = await locator.count()
        # Only expose options when there is more than one choice.  For the
        # per-group sentinel fields (scoped with :nth-of-type) the count is 1,
        # and rendering a single radio button is redundant with the group
        # label.
        if count > 1:
            opts: list[str] = []
            for i in range(count):
                item = locator.nth(i)
                if field.option_label:
                    text = await item.locator(field.option_label).inner_text()
                else:
                    text = await item.inner_text()
                opts.append((text or "").strip())
            prompt_to_return.options = opts

    if prompt_to_return.label:
        prompt_to_return.prompt = await get_label_text(page, prompt_to_return.label)

    logger.debug(f"🍃 Prompt message: {prompt_to_return.prompt}")
    return prompt_to_return


async def _maybe_navigate_to_start(page: Page, flow_state: FlowState) -> None:
    """Navigate to the flow's start page—if defined—on the first iteration."""
    if flow_state.current_page_spec_name is None:
        match flow_state.flow.start:
            case PageSpec():
                if flow_state.flow.start.url:
                    await page.goto(
                        flow_state.flow.start.url, wait_until="domcontentloaded", timeout=60_000
                    )
                    start_page = flow_state.flow.start
                    flow_state.current_page_spec_name = start_page.name
                else:
                    raise ValueError(
                        f"⚠️ No URL provided for start page '{flow_state.flow.start.name}'"
                    )
            case str():
                await page.goto(
                    flow_state.flow.start, wait_until="domcontentloaded", timeout=60_000
                )
            case None:
                pass


async def _collect_needed_inputs(flow_state: FlowState, page: Page) -> StatePrompt | None:
    """Return prompts for inputs that are still missing for *current_page*."""
    if not flow_state.current_page_spec:
        return None

    choices = flow_state.current_page_spec.choices
    if not choices:
        return None

    # ------------------------------------------------------------------
    # Dynamic choices expansion – build prompt groups from page DOM
    # ------------------------------------------------------------------
    if choices.dynamic and not choices.groups:
        dyn = choices.dynamic
        items = page.locator(dyn.option_items)
        count = await items.count()
        for idx in range(count):
            item = items.nth(idx)
            if dyn.option_label:
                label = (await item.locator(dyn.option_label).inner_text()) or ""
            else:
                label = (await item.inner_text()) or ""

            label = label.strip() or f"Option {idx + 1}"

            # Limit this sentinel field to just *one* option (nth-child selector)
            scoped_items_selector = f"{dyn.option_items}:nth-of-type({idx + 1})"

            sel_field = Field(
                name=f"{choices.name}_choice_{idx}",
                type="selection",
                prompt=label,
                option_items=scoped_items_selector,
                option_label=dyn.option_label,
                expect_nav=False,
            )

            grp = Choice(
                name=label,
                prompt=label,
                required_fields=[sel_field],
                optional_fields=[],
            )
            choices.groups.append(grp)

    any_group_filled = any(choice.is_filled(flow_state.inputs) for choice in choices.groups)
    if any_group_filled:
        return None

    prompt_text: str = choices.prompt

    groups: list[ChoicePrompt] = []
    for choice in choices.groups:
        # Resolve group-specific label substitution.
        group_name = choice.name
        prompts_list: list[InputPrompt] = []
        for fld in choice.fields_accept_input:
            prompts_list.append(await handle_field_prompt(page=page, field=fld))
        groups.append(
            ChoicePrompt(
                name=group_name,
                prompt=choice.prompt,
                groups=prompts_list,
                message=await _get_choice_message(
                    page,
                    choice,
                    flow_state.field_detections,
                ),
            )
        )

    return StatePrompt(
        name=choices.name,
        prompt=prompt_text,
        choices=groups,
    )


async def _get_choice_message(
    page: Page, choice: Choice, field_detections: dict[str, bool]
) -> str | None:
    messages: list[str] = []
    for field in choice.all_fields:
        if field.type == "message" and field_detections.get(field.name, False):
            if field.label:
                message: str | None = await get_label_text(
                    page,
                    field.label,
                    iframe_selector=field.iframe_selector,
                )
            else:
                message = field.prompt

            messages.append(message or "")
    return "\n".join(messages) if messages else None


async def _handle_fields(fld: Field, current_frame: Frame | Page, flow_state: FlowState):
    logger.debug(f"🌐 Handling field {fld.name}.")
    if fld.name in flow_state.inputs:
        value = flow_state.inputs[fld.name]
        del flow_state.inputs[fld.name]  # reset the value
    else:
        value = ""

    if fld.type == "click" or fld.type == "autoclick":
        if not fld.selector:
            raise ValueError(f"⚠️ No selector provided for click field '{fld.name}'")
        await handle_click(current_frame, fld, None, flow_state.bundle_dir)
    elif fld.needs_multi_fill:
        await handle_fill_multi(current_frame, fld, value)
    elif fld.needs_single_fill:
        await handle_fill_single(current_frame, fld, value)
    elif fld.type == "navigate":
        if not fld.url:
            raise ValueError(f"⚠️ No URL provided for navigate field '{fld.name}'")
        if isinstance(current_frame, Frame):
            page = current_frame.page
        else:
            page = current_frame
        await handle_navigate(page, fld.url)
    elif fld.type == "selection":
        await handle_select_option(current_frame, fld, value)


async def _execute_page_fields(page: Page, flow_state: FlowState) -> None:
    """Perform the actions (fill/click) required by every field in the current
    page specification."""
    current_page = flow_state.current_page_spec
    if not current_page.choices:
        return

    for choice in current_page.choices.groups:
        if not choice.is_filled(flow_state.inputs):
            continue

        for field in choice.fields_need_action:
            current_frame = page
            # TODO: make this a general handle_action function that is called for each field
            # Switch to iframe if needed
            if field.iframe_selector:
                try:
                    frame_elem = await page.wait_for_selector(field.iframe_selector)
                    frame_content = await frame_elem.content_frame() if frame_elem else None
                    if frame_content:
                        current_frame = frame_content
                except Exception:
                    logger.warning(
                        "⚠️ Could not switch to iframe %s for field %s",
                        field.iframe_selector,
                        field.name,
                    )

            await _handle_fields(field, current_frame, flow_state)

            if field.expect_nav and field.type != "navigate" and field.url:
                logger.debug(f"🌐 Expecting navigation to {field.url}...")

                # TODO: enforce field.url if expect_nav is true
                # wait for the response to the url to ensure page is loaded
                try:
                    timeout = current_page.timeout * 1000 if current_page.timeout else 10000
                    async with page.expect_response(field.url, timeout=timeout) as response_info:
                        await asyncio.wait_for(response_info.value, timeout=timeout)
                except (TimeoutError, asyncio.TimeoutError):
                    logger.warning(
                        f"⚠️ Timeout waiting for navigation to {field.url}. Possible incorrect credentials or navigation failure."
                    )
                    # Continue execution to allow handling of error states

            if field.delay_ms:
                logger.info(f"💤 Waiting for {field.delay_ms} ms...")
                await page.wait_for_timeout(field.delay_ms)

        # After executing the chosen group, run any unconditional "afterwards" fields.
        if current_page.choices.afterwards:
            for aft in current_page.choices.afterwards:
                await _handle_fields(aft, page, flow_state)

    # Field execution complete; the caller will decide the next step.


async def _detect_next_page(
    page: Page, page_detector: PageSpecDetector, flow_state: FlowState
) -> bool:
    """Detect the next page and update the flow_state accordingly. Returns True if it is an end page."""
    flow_state.current_page_spec_name = await page_detector.detect(page)

    flow_state.error = flow_state.current_page_spec.message

    if flow_state.current_page_spec.end:
        logger.info(
            "✅ Terminal page reached, finishing...",
            extra={"profile_id": flow_state.browser_profile_id},
        )
        await flow_state.set_finished(True)
        return True
    return False


async def flow_step_fsm(*, page: Page, flow_state: FlowState) -> FlowState:
    await _maybe_navigate_to_start(page, flow_state)
    detector = PageSpecDetector(flow_state)
    is_end_page = await _detect_next_page(page, detector, flow_state)
    if is_end_page:
        return flow_state
    needed_inputs = await _collect_needed_inputs(flow_state, page)

    # If we are missing any inputs we pause the automation and return the prompts
    if needed_inputs:
        flow_state.prompt = needed_inputs
        logger.debug(f"Exiting flow step with needed inputs: {needed_inputs}")
        return flow_state
    else:
        await _execute_page_fields(page, flow_state)
        flow_state.prompt = None
        return flow_state


async def flow_step(*, page: Page, flow_state: FlowState) -> FlowState:
    steps = flow_state.flow.steps
    page_specs = flow_state.flow.pages

    if page_specs:
        assert not steps, "Cannot have both page_specs and steps"
        return await flow_step_fsm(page=page, flow_state=flow_state)

    step = steps[flow_state.step_index]
    timeout = step.timeout * 1000 if step.timeout else 3000

    # ------------------------------------------------------------------
    # Preemptively start network listener to avoid race conditions when
    # a navigation and a network extraction are defined in the same step.
    # We launch the listener *before* navigation so that we don't miss
    # fast network calls triggered during page load.
    # ------------------------------------------------------------------
    network_task: asyncio.Task[Any] | None = None
    if step.url and step.listen_to_url_stub_json:
        # Start listening for the target response *before* navigating.
        network_task = asyncio.create_task(
            handle_network_extraction(page, step.listen_to_url_stub_json)
        )

    if step.sleep:
        logger.info(f"💤 Sleeping for {step.sleep} seconds...")
        await page.wait_for_timeout(step.sleep * 1000)

    if step.url:
        await handle_navigate(page, step.url)

    if step.wait_for_selector:
        logger.info(f"⏱️ Waiting {timeout} ms for selector {step.wait_for_selector}...")
        await wait_for_selector(page, step.wait_for_selector, timeout=timeout)

    if step.wait_for_url:
        logger.info(f"🌐 Waiting for {step.wait_for_url}...")
        await page.wait_for_url(step.wait_for_url, timeout=timeout)

    # Get iframe context from fields if any
    current_page = page
    if step.fields and len(step.fields) > 0:
        prompts_to_return: list[InputPrompt] = []
        has_needed_inputs = True
        for field in step.fields:
            if field.type == "navigate":
                if not field.url:
                    raise ValueError(f"⚠️ No URL provided for navigate field '{field.name}'")
                if isinstance(current_page, Frame):
                    page = current_page.page
                else:
                    page = current_page
                await handle_navigate(page, field.url)
                continue

            # This allows us to ask for a prompt if the field is not already filled without it being another step
            value = flow_state.inputs.get(field.name, "")
            if field.needs_input and not value:
                prompt = await handle_field_prompt(page, field)
                prompts_to_return.append(prompt)
                has_needed_inputs = False
                continue

            if not has_needed_inputs:
                continue
            if field.iframe_selector:
                logger.info(f"🖼️ Switching to iframe {field.iframe_selector}...")
                frame = await page.wait_for_selector(field.iframe_selector)
                if frame:
                    frame_content = await frame.content_frame()
                    if frame_content:
                        current_page = frame_content
                    else:
                        logger.warning(f"⚠️ Could not get frame content for {field.iframe_selector}")

            if field.type == "click" or field.type == "autoclick":
                if field.selector:
                    await handle_click(
                        current_page,
                        field,
                        step.download_filename,
                        flow_state.bundle_dir,
                        timeout,
                    )
                else:
                    raise ValueError(f"⚠️ No selector provided for {field.name}")
            elif field.type == "wait" and field.selector:
                await wait_for_selector(current_page, field.selector, timeout=timeout)
            elif field.needs_multi_fill:
                await handle_fill_multi(current_page, field, value)
            elif field.needs_single_fill:
                await handle_fill_single(current_page, field, value)

        flow_state.prompt = (
            StatePrompt.from_legacy_prompts(prompts_to_return) if prompts_to_return else None
        )
        if not has_needed_inputs:
            return flow_state

    if step.click:
        await handle_click(
            current_page,
            step.click,
            step.download_filename,
            flow_state.bundle_dir,
            timeout,
        )

    if step.press:
        logger.info(f"⌨️ Pressing {step.press}...")
        await page.keyboard.press(step.press)
        await page.wait_for_timeout(200)

    bundle = None
    if step.bundle:
        if step.slurp_selector:
            logger.info(f"📦 Slurping and packaging {step.slurp_selector}...")
            locator = page.locator(step.slurp_selector)
            await locator.wait_for(state="visible")
            content = await locator.evaluate_all(
                'elements => elements.map(element => element.innerHTML).join("")'
            )
            bundle = Bundle(name=step.bundle, content=content)
            logger.info(f"📦 {step.bundle} is {len(content)} bytes.")
        if step.listen_to_url_stub_json:
            if network_task is not None:
                # Await the result captured by the pre-navigation listener.
                orders: Any = await network_task
            else:
                # Fallback to the legacy behaviour when listener starts after
                # navigation.
                orders = await handle_network_extraction(
                    page,
                    step.listen_to_url_stub_json,
                )
            content = json.dumps(orders)
            bundle = Bundle(name=step.bundle, content=content)
            logger.info(f"📦 {step.bundle} is {len(content)} bytes.")
        if step.graphql:
            orders = await handle_graphql_response(
                page,
                step.graphql.endpoint,
                step.graphql.operation,
            )
            content = json.dumps(orders)  # Makes content a string
            if orders:  # check the original response is not empty
                if step.graphql.function:
                    brand_specific_function = load_custom_functions(
                        brand_id=BrandIdEnum(flow_state.brand_name.lower())
                    )
                    content = (
                        await brand_specific_function.retrieve_image_url_and_price_for_wayfair(
                            page,
                            content,
                        )
                    )
                    content = json.dumps(content)
            bundle = Bundle(name=step.bundle, content=content)
            logger.info(f"📦 {step.bundle} is {len(content)} bytes.")

    # before the increment, but after the work is done
    if flow_state.step_index >= len(flow_state.flow.steps) - 1:
        await flow_state.set_finished(True)
    flow_state.step_index += 1
    flow_state.paused = step.pause
    flow_state.bundle = bundle

    return flow_state
