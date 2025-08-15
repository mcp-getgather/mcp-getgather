from fastapi import HTTPException
from pydantic import BaseModel, Field

from getgather.activity import track_activity
from getgather.api.types import RequestInfo
from getgather.auth_orchestrator import AuthOrchestrator, AuthStatus, ProxyError
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession, BrowserStartupError
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.extract_orchestrator import ExtractOrchestrator, ExtractState
from getgather.flow_state import FlowState
from getgather.logs import logger
from getgather.parse import BundleOutput


class AuthFlowRequest(BaseModel):
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


class AuthFlowResponse(BaseModel):
    """Response from an auth flow step."""

    profile_id: str = Field(description="The browser profile ID used for the extraction.")
    status: AuthStatus = Field(description="The status of the auth flow.")
    state: FlowState = Field(description="The state of the auth flow.")
    extract_result: ExtractResult | None = Field(
        default=None,
        description="The result of the extract flow, if one occurs.",
    )


async def auth_flow(
    brand_id: BrandIdEnum,
    auth_request: AuthFlowRequest,
) -> AuthFlowResponse:
    """Start or continue an authentication flow for a connector."""
    # Use activity context manager for hosted link auth recording
    # TODO: record activity auth
    return await _auth_flow(brand_id, auth_request)


async def _auth_flow(brand_id: BrandIdEnum, auth_request: AuthFlowRequest):
    try:
        # Initialize the auth manager
        if auth_request.profile_id:
            browser_profile = BrowserProfile(id=auth_request.profile_id)
        else:
            browser_profile = BrowserProfile()

        browser_session = await BrowserSession.get(browser_profile)
        await browser_session.start()

        auth_orchestrator = AuthOrchestrator(
            brand_id=brand_id,
            browser_profile=browser_profile,
            state=auth_request.state,
        )
        state = await auth_orchestrator.advance()

        extract_result = None
        if state.finished:
            if state.error:
                logger.warning(
                    f"❗ Unauthenticated terminal page during auth: {state.error}",
                    extra={"profile_id": browser_profile.id},
                )
            elif auth_request.extract:
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
            await auth_orchestrator.finalize()

        if extract_result:
            logger.info(
                f"Extracted Data sample: {extract_result.bundles[0].content[:200] if extract_result.bundles else 'None'}",
                extra={"brand_id": brand_id},
            )
        # Convert response to API format
        return AuthFlowResponse(
            profile_id=browser_profile.id,
            state=auth_orchestrator.state,
            status=auth_orchestrator.status,
            extract_result=extract_result,
        )

    except BrowserStartupError as e:
        logger.error(f"Browser startup error in auth flow: {e}", exc_info=True)
        raise e
    except ProxyError as e:
        logger.error(f"Proxy error in auth flow: {e}", exc_info=True)
        raise e
    except Exception as e:
        logger.error(f"Error in auth flow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
