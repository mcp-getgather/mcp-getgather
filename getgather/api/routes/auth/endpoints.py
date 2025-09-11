from typing import Annotated

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from getgather.api.types import request_info
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.signin_flow import SigninFlowRequest, SigninFlowResponse, signin_flow

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/v1/{brand_id}")
@router.post("/v1/{brand_id}/{link_id}")
async def auth(
    brand_id: BrandIdEnum,
    signin_request: Annotated[SigninFlowRequest, "Request data for an auth flow."],
    link_id: str | None = None,
) -> SigninFlowResponse:
    """Start or continue an authentication flow for a connector."""
    if signin_request.location:
        request_info.set(signin_request.location)

    return await signin_flow(brand_id, signin_request, link_id)


@router.post("/{brand_id}")
@router.post("/{brand_id}/{link_id}")
async def auth_flow_redirect(brand_id: BrandIdEnum, link_id: str | None = None) -> RedirectResponse:
    """Redirect old auth flow endpoint to versioned endpoint."""
    url = f"/api/auth/v1/{brand_id}"
    if link_id:
        url += f"/{link_id}"
    return RedirectResponse(url=url, status_code=307)
