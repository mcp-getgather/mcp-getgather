from fastapi import APIRouter, HTTPException, Request, status

from getgather.api.routes.link.types import (
    TokenLookupResponse,
)
from getgather.hosted_link_manager import HostedLinkManager, LinkDataUpdate
from getgather.logs import logger

router = APIRouter(prefix="/link", tags=["link"])


@router.get("/status/{link_id}", response_model=TokenLookupResponse)
async def get_hosted_link(
    request: Request,
    link_id: str,
) -> TokenLookupResponse:
    logger.info(
        "[get_hosted_link] Retrieving hosted link",
        extra={"link_id": link_id, "request_url": str(request.url)},
    )

    try:
        link_data = HostedLinkManager.get_link_data(link_id)
        if not link_data:
            logger.warning("[get_hosted_link] Link not found", extra={"link_id": link_id})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hosted link '{link_id}' not found",
            )

        response = TokenLookupResponse(
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

        logger.info(
            "[get_hosted_link] Successfully retrieved link data",
            extra={
                "link_id": link_id,
                "brand_id": link_data.brand_id,
                "profile_id": link_data.profile_id,
                "status": link_data.status,
                "redirect_url": link_data.redirect_url,
                "status_message": link_data.status_message,
            },
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving hosted link", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving hosted link",
        )


@router.patch("/status/{link_id}")
async def update_hosted_link(
    request: Request,
    link_id: str,
    update_data: LinkDataUpdate,
) -> TokenLookupResponse:
    logger.info(
        "[update_hosted_link] Updating hosted link status",
        extra={
            "link_id": link_id,
            "request_url": str(request.url),
            "update_data": update_data.model_dump(),
        },
    )

    try:
        link_data = HostedLinkManager.get_link_data(link_id)
        if not link_data:
            logger.warning("[update_hosted_link] Link not found", extra={"link_id": link_id})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hosted link '{link_id}' not found",
            )

        updated_link = HostedLinkManager.update_link(link_id, update_data)
        if not updated_link:
            if HostedLinkManager.is_expired(link_data):
                logger.warning("[update_hosted_link] Link expired", extra={"link_id": link_id})
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Hosted link '{link_id}' has expired",
                )
            else:
                logger.warning(
                    "[update_hosted_link] Link not found for update", extra={"link_id": link_id}
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Hosted link '{link_id}' not found for update",
                )

        logger.info(
            "[update_hosted_link] Successfully updated hosted link",
            extra={
                "link_id": link_id,
                "new_status": updated_link.status,
                "brand_id": updated_link.brand_id,
                "profile_id": updated_link.profile_id,
            },
        )
        response = TokenLookupResponse(
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
        logger.info(
            f"[update_hosted_link] Returning updated response with status: {response.status}"
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating hosted link status", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating hosted link status",
        )
