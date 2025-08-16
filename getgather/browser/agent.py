from typing import Any

from browser_use import Agent, BrowserSession
from browser_use.agent.views import AgentOutput
from browser_use.browser.views import BrowserStateSummary
from browser_use.llm import ChatOpenAI
from fastmcp import Context
from patchright.async_api import BrowserContext

from getgather.config import settings
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.shared import start_browser_session


async def run_agent(mcp_context: Context, browser_context: BrowserContext, task: str) -> str | None:
    # TODO: Add support for non-OpenAI models
    if not settings.BROWSER_USE_MODEL or not settings.OPENAI_API_KEY:
        raise ValueError("BROWSER_USE_MODEL or OPENAI_API_KEY is not set")

    browser_session = BrowserSession(browser_context=browser_context)
    llm = ChatOpenAI(model=settings.BROWSER_USE_MODEL, api_key=settings.OPENAI_API_KEY)

    async def callback(
        browser_state_summary: BrowserStateSummary, agent_output: AgentOutput, step_number: int
    ):
        update = f"[Thinking]: {agent_output.thinking}\n [Next goal]: {agent_output.next_goal}"
        await mcp_context.report_progress(progress=step_number, message=update)

    agent = Agent[Any, Any](
        task=task,
        llm=llm,
        browser_session=browser_session,
        register_new_step_callback=callback,
    )
    results = await agent.run()  # type: ignore
    return results.final_result()


async def run_agent_for_brand(
    *, brand_id: BrandIdEnum, task: str, mcp_ctx: Context
) -> dict[str, Any]:
    browser_session = None
    try:
        browser_session = await start_browser_session(brand_id)

        logger.info(f"Running agent with task: {task}")
        result = await run_agent(mcp_ctx, browser_session.context, task)
        logger.info(f"Agent result: {result}")

        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if browser_session:
            await browser_session.stop()
