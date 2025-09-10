from typing import Annotated

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from getgather.api.types import request_info
from getgather.signin_flow import SigninFlowRequest, SigninFlowResponse, signin_flow
from getgather.connectors.spec_loader import BrandIdEnum

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/{brand_id}")
async def auth_flow_redirect(brand_id: BrandIdEnum) -> RedirectResponse:
    """Redirect old auth flow endpoint to versioned endpoint."""
    return RedirectResponse(url=f"/api/auth/v1/{brand_id}", status_code=307)


@router.post("/v1/{brand_id}")
async def auth(
    brand_id: BrandIdEnum,
    signin_request: Annotated[SigninFlowRequest, "Request data for an auth flow."],
) -> SigninFlowResponse:
    """Start or continue an authentication flow for a connector."""
    if signin_request.location:
        request_info.set(signin_request.location)

    return await signin_flow(brand_id, signin_request)
