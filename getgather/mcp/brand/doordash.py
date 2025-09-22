import os
import time
from functools import wraps
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar, overload

from fastmcp import Context

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.logs import logger
from getgather.mcp.agent import run_agent_for_brand
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile
from getgather.mcp.stagehand_agent import run_stagehand_agent

P = ParamSpec("P")
T = TypeVar("T")
DictReturnType = dict[str, Any]


@overload
def time_execution(
    func: Callable[P, Awaitable[DictReturnType]],
) -> Callable[P, Awaitable[DictReturnType]]: ...


@overload
def time_execution(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: ...


def time_execution(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """Decorator to time function execution and log the results."""

    @wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        function_name = func.__name__
        logger.info(f"Starting {function_name}")

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {function_name} in {execution_time:.2f} seconds")

            # Add timing info to result if it's a dict
            if isinstance(result, dict):
                # Type checker knows this is a dict now
                result["execution_time_seconds"] = round(execution_time, 2)

            return result  # type: ignore[return-value]
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {function_name} after {execution_time:.2f} seconds: {e}")
            raise

    return async_wrapper


doordash_mcp = BrandMCPBase(brand_id="doordash", name="Doordash MCP")


@doordash_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from Doordash.com."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    orders = await run_distillation_loop(
        "https://www.doordash.com/orders", patterns, browser_profile=browser_profile
    )
    return {"orders": orders}


REORDER_INSTRUCTIONS = (
    "Following the instructions below to reorder the last order on Doordash:"
    " 1. Go to Orders page at https://www.doordash.com/orders."
    " 2. Find the most recent order from {restaurant_name} on the page,"
    "   and click the 'Reorder' button, "
    "   then you will be redirected to the page of the restaurant."
    " 3. Click the red cart button on the top right corner of the page to open the cart."
    " 4. Continue the process to place the order. "
    "   Make sure choose delivery option and not pickup,"
    "   and the delivery address is the same as the last order."
    " 5. At the end, confirm the order is placed successfully."
)

CHECK_STATUS_INSTRUCTIONS = (
    "Following the instructions below to"
    " check the status of the in progress order on Doordash:"
    " 1. Go to Orders page at https://www.doordash.com/orders."
    " 2. Find the most recent in progress order on the top of the page,"
    " 3. Extract the order status including the estinated delivery time if available, and return the result."
    " 4. If there is no in progress order, return 'no in progress order found'."
)


@doordash_mcp.tool(tags={"private"})
async def reorder_previous_order(ctx: Context, restaurant_name: str) -> dict[str, Any]:
    """Reorder the previous order on Doordash.com from the given restaurant."""
    task = REORDER_INSTRUCTIONS.format(restaurant_name=restaurant_name)
    return await run_agent_for_brand(task)


@doordash_mcp.tool(tags={"private"})
async def check_order_status(ctx: Context) -> dict[str, Any]:
    """Check the status of the in progress order on Doordash.com."""
    task = CHECK_STATUS_INSTRUCTIONS
    return await run_agent_for_brand(task)


@doordash_mcp.tool(tags={"private"})
@time_execution
async def get_orders_stagehand() -> dict[str, Any]:
    """Get orders from Doordash.com using Stagehand."""
    agent = await run_stagehand_agent()
    page = agent.page
    await page.goto("https://www.doordash.com/orders")
    try:
        prompt = (
            "Go to https://www.doordash.com/orders and extract all order details "
            "including restaurant names, order dates, and order status"
        )
        result = await agent.execute(prompt)
        return {"status": "success", "orders": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await agent.close()


@doordash_mcp.tool(tags={"private"})
@time_execution
async def reorder_previous_order_stagehand(ctx: Context, restaurant_name: str) -> dict[str, Any]:
    """Reorder the previous order on Doordash.com from the given restaurant using Stagehand."""
    agent = await run_stagehand_agent()
    try:
        prompt = REORDER_INSTRUCTIONS.format(restaurant_name=restaurant_name)
        result = await agent.execute(prompt)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await agent.close()


@doordash_mcp.tool(tags={"private"})
@time_execution
async def check_order_status_stagehand(ctx: Context) -> dict[str, Any]:
    """Check the status of the in progress order on Doordash.com using Stagehand."""
    agent = await run_stagehand_agent()
    try:
        prompt = CHECK_STATUS_INSTRUCTIONS
        result = await agent.execute(prompt)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await agent.close()
