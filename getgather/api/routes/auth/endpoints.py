from typing import Annotated

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from getgather.api.types import request_info
from getgather.auth_flow import AuthFlowRequest, AuthFlowResponse, auth_flow
from getgather.connectors.spec_loader import BrandIdEnum

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/v1/{brand_id}")
@router.post("/v1/{brand_id}/{link_id}")
async def auth(
    brand_id: BrandIdEnum,
    auth_request: Annotated[AuthFlowRequest, "Request data for an auth flow."],
    link_id: str | None = None,
) -> AuthFlowResponse:
    """Start or continue an authentication flow for a connector."""
    if auth_request.location:
        request_info.set(auth_request.location)

    return await auth_flow(brand_id, auth_request, link_id)


@router.post("/{brand_id}")
@router.post("/{brand_id}/{link_id}")
async def auth_flow_redirect(brand_id: BrandIdEnum, link_id: str | None = None) -> RedirectResponse:
    """Redirect old auth flow endpoint to versioned endpoint."""
    url = f"/api/auth/v1/{brand_id}"
    if link_id:
        url += f"/{link_id}"
    return RedirectResponse(url=url, status_code=307)
