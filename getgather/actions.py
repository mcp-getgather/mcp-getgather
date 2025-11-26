import json
from typing import Any, cast

from patchright.async_api import Page, Response, TimeoutError

from getgather.logs import logger

PAGE_TIMEOUT = 30_000


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
