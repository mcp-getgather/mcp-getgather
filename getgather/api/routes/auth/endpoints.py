import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from getgather.api.routes.auth.types import (
    AuthFlowRequest,
    AuthFlowResponse,
    ExtractResult,
)
from getgather.api.types import request_info
from getgather.auth_orchestrator import AuthOrchestrator, ProxyError
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserStartupError
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.extract_orchestrator import ExtractOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/{brand_id}")
async def auth_flow_redirect(
    request: Request,
    brand_id: BrandIdEnum,
) -> RedirectResponse:
    """Redirect old auth flow endpoint to versioned endpoint."""
    return RedirectResponse(url=f"/auth/v1/{brand_id}", status_code=307)


@router.post("/v1/{brand_id}")
async def auth_flow(
    request: Request,
    brand_id: BrandIdEnum,
    auth_request: Annotated[AuthFlowRequest, "Request data for an auth flow."],
) -> AuthFlowResponse:
    """Start or continue an authentication flow for a connector."""
    logger.debug("Request ", request)

    if auth_request.location:
        request_info.set(auth_request.location)

    # Validate connector against the enum
    try:
        # Initialize the auth manager
        if auth_request.profile_id:
            browser_profile = BrowserProfile.get(profile_id=auth_request.profile_id)
        else:
            # TODO: allow web api to pass into browser config
            browser_profile = BrowserProfile.create()
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
                    extra={"profile_id": browser_profile.profile_id},
                )
            elif auth_request.extract:
                extract_orchestrator = ExtractOrchestrator(
                    brand_id=brand_id,
                    browser_profile=browser_profile,
                    nested_browser_session=True,
                )
                await extract_orchestrator.extract_flow()
                extract_result = ExtractResult(
                    profile_id=browser_profile.profile_id,
                    state=extract_orchestrator.state,
                    bundles=extract_orchestrator.bundles,
                )
            await auth_orchestrator.finalize()

        # Convert response to API format
        return AuthFlowResponse(
            profile_id=browser_profile.profile_id,
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
