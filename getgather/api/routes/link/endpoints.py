from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, status

from getgather.api.routes.link.types import (
    HostedLinkTokenRequest,
    HostedLinkTokenResponse,
    TokenLookupResponse,
)
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.hosted_link_manager import HostedLinkManager, LinkDataUpdate
from getgather.logs import logger

router = APIRouter(prefix="/link", tags=["link"])


@router.post("/create", response_model=HostedLinkTokenResponse)
async def create_hosted_link(
    request: Request,
    hosted_link_request: Annotated[
        HostedLinkTokenRequest, "Request data for creating a hosted link."
    ],
) -> HostedLinkTokenResponse:
    logger.info(f"Creating hosted link for brand: {hosted_link_request.brand_id}")
    try:
        redirect_url = hosted_link_request.redirect_url or ""
        link_data = HostedLinkManager.create_link(
            brand_id=BrandIdEnum(hosted_link_request.brand_id),
            redirect_url=redirect_url,
            url_lifetime_seconds=hosted_link_request.url_lifetime_seconds,
            profile_id=hosted_link_request.profile_id,
        )
        link_id = link_data["link_id"]
        expiration = link_data["expiration"]
        profile_id = link_data["profile_id"]
        base_url = str(request.base_url).rstrip("/")
        hosted_link_url = f"{base_url}/link/{link_id}"
        return HostedLinkTokenResponse(
            link_id=link_id,
            profile_id=profile_id,
            hosted_link_url=hosted_link_url,
            expiration=expiration,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating hosted link: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating hosted link",
        )


@router.get("/status/{link_id}", response_model=TokenLookupResponse)
async def get_hosted_link(
    link_id: str,
) -> TokenLookupResponse:
    logger.info(f"Retrieving hosted link: {link_id}")
    try:
        link_data = HostedLinkManager.get_link_data(link_id)
        if not link_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hosted link '{link_id}' not found",
            )

        return TokenLookupResponse(
            link_id=link_id,
            profile_id=link_data.profile_id,
            brand_id=str(link_data.brand_id),
            redirect_url=link_data.redirect_url,
            webhook=None,
            status=str(link_data.status),
            created_at=str(link_data.created_at),
            expires_at=str(link_data.expires_at),
            extract_result=link_data.extract_result,
            message=link_data.status_message or "Auth in progress...",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving hosted link: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving hosted link",
        )


@router.patch("/status/{link_id}")
async def update_hosted_link(
    link_id: str,
    update_data: LinkDataUpdate,
) -> TokenLookupResponse:
    logger.info(f"Updating hosted link status: {link_id}")
    try:
        link_data = HostedLinkManager.get_link_data(link_id)
        if not link_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hosted link '{link_id}' not found",
            )

        updated_link = HostedLinkManager.update_link(link_id, update_data)
        if not updated_link:
            if HostedLinkManager.is_expired(link_data):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Hosted link '{link_id}' has expired",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Hosted link '{link_id}' not found for update",
                )

        logger.info(f"Updated hosted link {link_id} with status: {updated_link.status}")
        return TokenLookupResponse(
            link_id=link_id,
            profile_id=updated_link.profile_id,
            brand_id=str(updated_link.brand_id),
            redirect_url=updated_link.redirect_url,
            webhook=None,
            status=str(updated_link.status),
            created_at=str(updated_link.created_at),
            expires_at=str(updated_link.expires_at),
            extract_result=updated_link.extract_result,
            message="Link status updated successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating hosted link status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating hosted link status",
        )
