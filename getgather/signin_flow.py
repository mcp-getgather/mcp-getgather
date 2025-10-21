from fastapi import HTTPException
from pydantic import BaseModel, Field

from getgather.api.types import RequestInfo
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession, BrowserStartupError
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.extract_orchestrator import ExtractOrchestrator, ExtractState
from getgather.flow_state import FlowState
from getgather.hosted_link_manager import HostedLinkManager
from getgather.logs import logger
from getgather.parse import BundleOutput
from getgather.signin_orchestrator import ProxyError, SigninOrchestrator, SigninStatus


class SigninFlowRequest(BaseModel):
    """Request for an auth flow."""

    profile_id: str | None = Field(
        description="The browser profile ID used for the extraction.", default=None
    )
    state: FlowState | None = Field(description="The state of the auth flow.", default=None)
    extract: bool = Field(
        default=True,
        description="Whether to extract the data after the auth flow is complete.",
    )
    location: RequestInfo | None = Field(
        description="The location for the client making the request.",
        default=None,
    )


class ExtractResult(BaseModel):
    """Result of an extract flow."""

    profile_id: str = Field(description="The browser profile ID used for the extraction.")
    state: ExtractState = Field(
        description="The state of the extract flow.",
    )
    bundles: list[BundleOutput] = Field(
        description="The file bundles and their contents that were extracted.",
    )


class SigninFlowResponse(BaseModel):
    """Response from an sign in flow step."""

    profile_id: str = Field(description="The browser profile ID used for the extraction.")
    status: SigninStatus = Field(description="The status of the sign in flow.")
    state: FlowState = Field(description="The state of the sign in flow.")
    extract_result: ExtractResult | None = Field(
        default=None,
        description="The result of the extract flow, if one occurs.",
    )


async def signin_flow(
    brand_id: BrandIdEnum,
    signin_request: SigninFlowRequest,
    link_id: str | None = None,
) -> SigninFlowResponse:
    """Start or continue an authentication flow for a connector."""
    if link_id:
        link_data = HostedLinkManager.get_link_data(link_id)
        if not link_data:
            raise HTTPException(status_code=404, detail="Link not found")

    try:
        # Initialize the auth manager
        if signin_request.profile_id:
            browser_profile = BrowserProfile(id=signin_request.profile_id)
        else:
            browser_profile = BrowserProfile()

        browser_session = BrowserSession.get(browser_profile)
        browser_session = await browser_session.start()
        signin_orchestrator = SigninOrchestrator(
            brand_id=brand_id,
            browser_profile=browser_profile,
            state=signin_request.state,
        )
        state = await signin_orchestrator.advance()

        extract_result = None
        if state.finished:
            if state.error:
                logger.warning(
                    f"❗ Unauthenticated terminal page during sign in: {state.error}",
                    extra={"profile_id": browser_profile.id},
                )
            elif signin_request.extract:
                extract_orchestrator = ExtractOrchestrator(
                    brand_id=brand_id,
                    browser_profile=browser_profile,
                    nested_browser_session=True,
                )
                await extract_orchestrator.extract_flow()
                extract_result = ExtractResult(
                    profile_id=browser_profile.id,
                    state=extract_orchestrator.state,
                    bundles=extract_orchestrator.bundles,
                )
            await signin_orchestrator.finalize()

        if extract_result:
            logger.info(
                f"Extracted Data sample: {extract_result.bundles[0].content[:200] if extract_result.bundles else 'None'}",
                extra={"brand_id": brand_id},
            )
        # Convert response to API format
        return SigninFlowResponse(
            profile_id=browser_profile.id,
            state=signin_orchestrator.state,
            status=signin_orchestrator.status,
            extract_result=extract_result,
        )

    except BrowserStartupError as e:
        logger.error(f"Browser startup error in sign in flow: {e}", exc_info=True)
        raise e
    except ProxyError as e:
        logger.error(f"Proxy error in sign in flow: {e}", exc_info=True)
        raise e
    except Exception as e:
        logger.error(f"Error in sign in flow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
