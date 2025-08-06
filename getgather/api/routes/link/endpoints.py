import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, status

from getgather.api.routes.link.types import (
    HostedLinkTokenRequest,
    HostedLinkTokenResponse,
    TokenLookupResponse,
)
from getgather.hosted_link_manager import HostedLinkManager, SessionData, SessionDataUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/link", tags=["link"])


def get_session_data(session_id: str) -> SessionData | None:
    return HostedLinkManager.get_session_data(session_id)


@router.post("/create", response_model=HostedLinkTokenResponse)
async def create_hosted_link_session(
    request: Request,
    hosted_link_request: Annotated[
        HostedLinkTokenRequest, "Request data for creating a hosted link session."
    ],
) -> HostedLinkTokenResponse:
    logger.info(f"Creating hosted link session for brand: {hosted_link_request.brand_id}")
    try:
        redirect_url = hosted_link_request.redirect_url or ""
        session_data = HostedLinkManager.create_session(
            brand_id=hosted_link_request.brand_id,
            redirect_url=redirect_url,
            url_lifetime_seconds=hosted_link_request.url_lifetime_seconds,
            profile_id=hosted_link_request.profile_id,
        )
        session_id = session_data["session_id"]
        expiration = session_data["expiration"]
        profile_id = session_data["profile_id"]
        base_url = str(request.base_url).rstrip("/")
        hosted_link_url = f"{base_url}/link/{session_id}"
        return HostedLinkTokenResponse(
            session_id=session_id,
            profile_id=profile_id,
            hosted_link_url=hosted_link_url,
            expiration=expiration,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating hosted link session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating hosted link session",
        )


@router.get("/status/{session_id}", response_model=TokenLookupResponse)
async def get_hosted_link_session(
    session_id: str,
) -> TokenLookupResponse:
    logger.info(f"Retrieving hosted link session: {session_id}")
    try:
        session_data = HostedLinkManager.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hosted link session '{session_id}' not found",
            )

        return TokenLookupResponse(
            session_id=session_id,
            profile_id=session_data.profile_id,
            brand_id=str(session_data.brand_id),
            redirect_url=session_data.redirect_url,
            webhook=None,
            status=str(session_data.status),
            created_at=str(session_data.created_at),
            expires_at=str(session_data.expires_at),
            extract_result=session_data.extract_result,
            message=session_data.status_message or "Auth in progress...",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving hosted link session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving hosted link session",
        )


@router.patch("/status/{session_id}")
async def update_hosted_link_session_status(
    session_id: str,
    update_data: SessionDataUpdate,
) -> TokenLookupResponse:
    logger.info(f"Updating hosted link session status: {session_id}")
    try:
        session_data = HostedLinkManager.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hosted link session '{session_id}' not found",
            )

        updated_session = HostedLinkManager.update_session(session_id, update_data)
        if not updated_session:
            if HostedLinkManager.is_expired(session_data):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Hosted link session '{session_id}' has expired",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Hosted link session '{session_id}' not found for update",
                )

        logger.info(
            f"Updated hosted link session {session_id} with status: {updated_session.status}"
        )
        return TokenLookupResponse(
            session_id=session_id,
            profile_id=updated_session.profile_id,
            brand_id=str(updated_session.brand_id),
            redirect_url=updated_session.redirect_url,
            webhook=None,
            status=str(updated_session.status),
            created_at=str(updated_session.created_at),
            expires_at=str(updated_session.expires_at),
            extract_result=updated_session.extract_result,
            message="Session status updated successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating hosted link session status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating hosted link session status",
        )
