import importlib
import json
import math
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from patchright.async_api import Frame, Locator, Page, Response, TimeoutError

from getgather.connectors.spec_models import Field
from getgather.logs import logger

PAGE_TIMEOUT = 30_000


async def wait_for_selector(page: Page, selector: str, timeout: int = 3000) -> None:
    try:
        element = page.locator(selector)
        timestamp = time.time()
        await element.wait_for(state="visible", timeout=timeout)
        duration = math.floor((time.time() - timestamp) * 1000)
        logger.debug(f"✅ Selector {selector} appears after {duration} ms")
    except Exception as e:
        logger.warning(f"⚠️ Selector {selector} didn't appear after {timeout} ms: {str(e)}")
        raise


@asynccontextmanager
async def try_download(page: Page, download_filename: str | None, download_dir: Path | None):
    """
    Try to download a file and save it to the given directory.
    """
    if not download_filename:
        yield
    elif not download_dir:
        logger.warning(f"No profile directory provided, skipping download of {download_filename}")
        yield
    else:
        async with page.expect_download() as download_info:
            yield
            logger.info(f"Downloading {download_filename} to {download_dir}")
            download = await download_info.value
            await download.save_as(download_dir / download_filename)


LOCATOR_ALL_TIMEOUT = 100  # ms


async def get_first_visible(locator: Locator) -> Locator | None:
    # First try to use the locator directly, but if that fails, try the first element
    try:
        if await locator.is_visible():
            return locator
    except Exception:
        try:
            if await locator.first.is_visible():
                return locator.first
        except Exception:
            return None


async def is_visible(locator: Locator) -> bool:
    return await get_first_visible(locator) is not None


async def handle_click(
    page: Frame | Page,
    selector: str,
    download_filename: str | None,
    bundle_dir: Path | None,
    timeout: int = 3000,
):
    logger.info(f"📝 Clicking {selector}...")
    async with try_download(page, download_filename, bundle_dir):  # type: ignore
        try:
            button = await get_first_visible(page.locator(selector))
            logger.debug(f"🔘 Button {selector} is {'visible' if button else 'not visible'}")
            if button:
                logger.debug(f"🔘 Clicking {selector}...")
                await button.click()
                logger.debug(f"🔘 Clicked {selector}")
        except TimeoutError as e:
            if timeout > 0:
                timeout -= LOCATOR_ALL_TIMEOUT
                logger.info(
                    f"⏳ Locator {selector} not found {e}, retrying with {timeout} ms timeout..."
                )
                await handle_click(page, selector, download_filename, bundle_dir, timeout)
            else:
                raise
        except Exception:
            raise

    await page.wait_for_timeout(100)


async def handle_navigate(page: Page, url: str):
    logger.info(f"🌐 Navigating to {url}...")
    await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    await page.wait_for_load_state("domcontentloaded")
    logger.info(f"🌐 Navigated to {url}")


async def handle_fill_single(frame: Frame | Page, field: Field, value: str) -> None:
    """Fill a single input field."""
    await frame.wait_for_timeout(500)
    logger.info(f"📝 Filling {field.name}")
    assert field.selector, "Field selector is required"

    input = frame.locator(field.selector)
    await input.clear()
    # use key board events to fill the input, which is needed to trigger javascript on some sites
    await input.press_sequentially(value, delay=100)
    await frame.wait_for_timeout(200)

    # shift focus to complete the input
    parent = input.locator("xpath=..")
    await parent.focus()


async def handle_fill_multi(frame: Frame | Page, field: Field, values: str | list[str]) -> None:
    """Fill repeated elements selected by `field.selectors`."""
    await frame.wait_for_timeout(500)
    # Coerce single string into a list for uniform processing.
    vals: list[str] = list(values) if isinstance(values, str) else values
    outer = frame.locator(field.selectors)  # type: ignore[arg-type]
    await outer.first.wait_for(state="attached", timeout=5_000)

    inner = frame.locator(f"{field.selectors} >>> input")
    if await inner.count() > 0:
        await inner.first.wait_for(state="attached", timeout=5_000)
        target = inner
    else:
        # Fallback if no match
        await frame.locator(f"css={field.selectors}").first.wait_for(
            state="attached", timeout=5_000
        )
        target = frame.locator(f"css={field.selectors}")

    for idx, val in enumerate(vals):
        logger.info(f"📝 Filling {field.name} {idx + 1}/{len(vals)}")
        await target.nth(idx).clear()
        await target.nth(idx).press_sequentially(val, delay=100)
        await frame.wait_for_timeout(200)


async def handle_network_extraction(page: Page, predicate: str) -> Any:
    """Wait for a network response whose URL contains *predicate* and return the parsed
    JSON body when available.  If the body cannot be parsed, an empty list is
    returned.  The return type is annotated as ``Any`` because the shape of the
    JSON payload can vary between connectors.
    """

    # Wait for the network response matching the given URL stub.
    logger.info(f"🔍 Waiting for {predicate}...")

    def _url_matches(resp: Response) -> bool:  # noqa: D401
        """Predicate that checks if the response URL contains the predicate string."""

        return predicate in resp.url

    # Cast is needed until Playwright ships precise type hints for `wait_for_event`.
    response: Response = cast(
        Response,
        await page.wait_for_event(  # type: ignore[reportUnknownReturnType]
            "response",
            _url_matches,
            timeout=3 * PAGE_TIMEOUT,
        ),
    )

    # Try to parse JSON (fall back to empty list).
    try:
        orders: Any = await response.json()
        logger.debug("Orders:")
        if "orders" not in orders:
            logger.warning(f"Orders not found in {orders}")
        logger.debug(json.dumps(orders, indent=2))
    except Exception as e:
        logger.error(f"Failed to parse JSON response: {e}")
        orders = []
        raise e

    return orders


async def handle_graphql_response(
    page: Page,
    graphql_endpoint_predicate: str,
    target_operation_name: str,
) -> Any:
    """Return JSON payload for a specific GraphQL operation.

    Args:
        page: The Playwright Page object.
        graphql_endpoint_predicate: A string that should be present in the GraphQL endpoint URL.
        target_operation_name: The 'operationName' of the GraphQL query to capture.

    Returns:
        The parsed JSON body of the targeted GraphQL response,
        or an empty list if not found or on error.
    """
    orders = []
    max_retries = 3
    while not orders and max_retries > 0:
        try:
            async with page.expect_response(
                lambda resp: (
                    graphql_endpoint_predicate in resp.url
                    and resp.request.method == "POST"
                    and target_operation_name in (resp.request.post_data or "")
                ),
                timeout=3 * PAGE_TIMEOUT,
            ) as response_info:
                logger.debug("🔄 Reloading page and waiting for POST request...")
                await page.reload()

            response = await response_info.value

            # Parse JSON immediately while response is still available
            try:
                orders: Any = await response.json()
                logger.info(f"🏁 Successfully parsed JSON response for '{target_operation_name}'.")
                return orders
            except json.JSONDecodeError as json_exc:
                logger.error(
                    f"Failed to parse final JSON response for '{target_operation_name}': {json_exc}"
                )
                orders = []
                max_retries -= 1
        except TimeoutError as e:
            logger.warning(
                f"Timeout waiting for POST to '{graphql_endpoint_predicate}' with operation '{target_operation_name}': {e}"
            )
            orders = []
            max_retries -= 1
        except Exception as e:
            logger.error(f"Error capturing GraphQL response: {e}")
            orders = []
            max_retries -= 1
    return orders


async def get_brand_function(brand_name: str, function_name: str) -> Any:
    """Get a brand function by name."""
    module_path = f"getgather.connectors.brand_specs.custom_functions.{brand_name}"
    module = importlib.import_module(module_path)
    return getattr(module, function_name)


async def get_label_text(
    page: Page, selector: str, *, iframe_selector: str | None = None, timeout: int | None = 2_000
) -> str | None:
    """
    Grab all text content from a locator, optionally inside an iframe.
    If timeout is None: skip waiting. Otherwise wait up to `timeout` ms.
    """
    # choose frame vs page
    locator = (
        page.frame_locator(iframe_selector).locator(selector)
        if iframe_selector
        else page.locator(selector)
    )

    # only wait if timeout is specified
    if timeout is not None:
        try:
            await locator.first.wait_for(state="attached", timeout=timeout)
        except TimeoutError:
            pass  # didn’t show up in time—just read whatever’s there

    parts = await locator.all_text_contents()
    text = " ".join(parts).strip()
    return text or None


async def _match_selection_index(locator: Locator, field: Field, value: str) -> int:
    """Return 0-based index within *locator* whose text (or explicit index) matches *value*."""
    option_label_selector = field.option_label
    count: int = await locator.count()
    if count == 0:
        raise ValueError("No selectable options found")

    # If numeric string treat as 1-based index
    if value.isdigit():
        idx = int(value) - 1
        if 0 <= idx < count:
            return idx

    # Otherwise compare label text (case-insensitive, trimmed)
    for i in range(count):
        item: Locator = locator.nth(i)
        if option_label_selector:
            text_raw = await item.locator(option_label_selector).inner_text()
        else:
            text_raw = await item.inner_text()
        text: str = (text_raw or "").strip()
        if text.lower() == value.strip().lower():
            return i

    # finally, if the value is a bool and the name has _choice_idx, then use the index
    if value.lower() == "true" and "_choice_" in field.name:
        idx = int(field.name.split("_choice_")[-1])
        if 0 <= idx < count:
            return idx
        else:
            raise ValueError(f"Could not find option matching '{value}' from {field.name}")
    raise ValueError(f"Could not find option matching '{value}'")


async def handle_select_option(frame: Frame | Page, field: Field, value: str):
    """Select an option from a dynamic choices list.

    The list of selectable elements is given by ``field.option_items``.  *value* can
    be either a 1-based index (as string) or the visible label text.
    """

    if not field.option_items:
        raise ValueError("option_items selector missing for selection field")

    items_locator = frame.locator(field.option_items)
    idx = await _match_selection_index(items_locator, field, value)

    logger.info("📝 Selecting option %s for %s", idx + 1, field.name)

    target = items_locator.nth(idx)

    # Prefer checking an input element if present; fallback to click.
    input_elem = target.locator("input[type=radio], input[type=checkbox]")
    if await input_elem.count() > 0:
        try:
            await input_elem.first.check()
        except Exception:
            await target.click()
    else:
        await target.click()

    await frame.wait_for_timeout(200)
