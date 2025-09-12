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
from getgather.mcp.connection_manager import connection_manager

router = APIRouter(prefix="/link", tags=["link"])


@router.post("/create", response_model=HostedLinkTokenResponse)
async def create_hosted_link(
    request: Request,
    hosted_link_request: Annotated[
        HostedLinkTokenRequest, "Request data for creating a hosted link."
    ],
) -> HostedLinkTokenResponse:
    relevant_headers = {
        "host": request.headers.get("host"),
        "x-forwarded-host": request.headers.get("x-forwarded-host"),
        "x-forwarded-proto": request.headers.get("x-forwarded-proto"),
        "x-forwarded-port": request.headers.get("x-forwarded-port"),
        "user-agent": request.headers.get("user-agent"),
    }

    logger.info(
        "[create_hosted_link] Creating hosted link",
        extra={
            "brand_id": hosted_link_request.brand_id,
            "request_url": str(request.url),
            "headers": relevant_headers,
        },
    )

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

        # URL construction
        original_scheme = request.url.scheme
        original_host = request.headers.get("host")
        forwarded_proto = request.headers.get("x-forwarded-proto")
        forwarded_host = request.headers.get("x-forwarded-host")

        scheme = forwarded_proto or original_scheme
        host = forwarded_host or original_host
        base_url = f"{scheme}://{host}".rstrip("/")
        hosted_link_url = f"{base_url}/link/{link_id}"
        response = HostedLinkTokenResponse(
            link_id=link_id,
            profile_id=profile_id,
            hosted_link_url=hosted_link_url,
            expiration=expiration,
        )

        logger.info(
            "[create_hosted_link] Successfully created hosted link",
            extra={
                "link_id": link_id,
                "profile_id": profile_id,
                "redirect_url": redirect_url,
                "hosted_link_url": hosted_link_url,
                "original_scheme": original_scheme,
                "original_host": original_host,
                "forwarded_proto": forwarded_proto,
                "forwarded_host": forwarded_host,
                "final_scheme": scheme,
                "final_host": host,
            },
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating hosted link", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating hosted link",
        )


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

        # If status became "completed", update connection manager
        if str(updated_link.status) == "completed":
            connection_manager.set_connected(updated_link.brand_id, True)
            logger.info(
                "[update_hosted_link] Marked brand as connected",
                extra={"brand_id": str(updated_link.brand_id)},
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
