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
    logger.info(
        f"[create_hosted_link] Creating hosted link for brand: {hosted_link_request.brand_id}"
    )

    # Log incoming request details
    relevant_headers = {
        "host": request.headers.get("host"),
        "x-forwarded-host": request.headers.get("x-forwarded-host"),
        "x-forwarded-proto": request.headers.get("x-forwarded-proto"),
        "x-forwarded-port": request.headers.get("x-forwarded-port"),
        "user-agent": request.headers.get("user-agent"),
    }
    logger.info(f"[create_hosted_link] Request URL: {request.url}")
    logger.info(f"[create_hosted_link] Relevant headers: {relevant_headers}")

    try:
        redirect_url = hosted_link_request.redirect_url or ""
        logger.info(f"[create_hosted_link] Redirect URL: {redirect_url}")

        link_data = HostedLinkManager.create_link(
            brand_id=BrandIdEnum(hosted_link_request.brand_id),
            redirect_url=redirect_url,
            url_lifetime_seconds=hosted_link_request.url_lifetime_seconds,
            profile_id=hosted_link_request.profile_id,
        )
        link_id = link_data["link_id"]
        expiration = link_data["expiration"]
        profile_id = link_data["profile_id"]
        logger.info(f"[create_hosted_link] Created link_id: {link_id}, profile_id: {profile_id}")

        # URL construction with detailed logging
        original_scheme = request.url.scheme
        original_host = request.headers.get("host")
        forwarded_proto = request.headers.get("x-forwarded-proto")
        forwarded_host = request.headers.get("x-forwarded-host")

        scheme = forwarded_proto or original_scheme
        host = forwarded_host or original_host
        base_url = f"{scheme}://{host}".rstrip("/")
        hosted_link_url = f"{base_url}/link/{link_id}"

        logger.info(f"[create_hosted_link] URL construction:")
        logger.info(f"  - original_scheme: {original_scheme}")
        logger.info(f"  - original_host: {original_host}")
        logger.info(f"  - forwarded_proto: {forwarded_proto}")
        logger.info(f"  - forwarded_host: {forwarded_host}")
        logger.info(f"  - final_scheme: {scheme}")
        logger.info(f"  - final_host: {host}")
        logger.info(f"  - base_url: {base_url}")
        logger.info(f"  - hosted_link_url: {hosted_link_url}")

        response = HostedLinkTokenResponse(
            link_id=link_id,
            profile_id=profile_id,
            hosted_link_url=hosted_link_url,
            expiration=expiration,
        )
        logger.info(f"[create_hosted_link] Returning response with URL: {response.hosted_link_url}")
        return response
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
    request: Request,
    link_id: str,
) -> TokenLookupResponse:
    logger.info(f"[get_hosted_link] Retrieving hosted link: {link_id}")
    logger.info(f"[get_hosted_link] Request URL: {request.url}")

    try:
        link_data = HostedLinkManager.get_link_data(link_id)
        if not link_data:
            logger.warning(f"[get_hosted_link] Link not found: {link_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hosted link '{link_id}' not found",
            )

        logger.info(f"[get_hosted_link] Found link data:")
        logger.info(f"  - brand_id: {link_data.brand_id}")
        logger.info(f"  - profile_id: {link_data.profile_id}")
        logger.info(f"  - status: {link_data.status}")
        logger.info(f"  - redirect_url: {link_data.redirect_url}")
        logger.info(f"  - status_message: {link_data.status_message}")

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
        logger.info(f"[get_hosted_link] Returning status response: {response.status}")
        return response
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
    request: Request,
    link_id: str,
    update_data: LinkDataUpdate,
) -> TokenLookupResponse:
    logger.info(f"[update_hosted_link] Updating hosted link status: {link_id}")
    logger.info(f"[update_hosted_link] Request URL: {request.url}")
    logger.info(f"[update_hosted_link] Update data: {update_data.model_dump()}")

    try:
        link_data = HostedLinkManager.get_link_data(link_id)
        if not link_data:
            logger.warning(f"[update_hosted_link] Link not found: {link_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hosted link '{link_id}' not found",
            )

        logger.info(f"[update_hosted_link] Current link status: {link_data.status}")

        updated_link = HostedLinkManager.update_link(link_id, update_data)
        if not updated_link:
            if HostedLinkManager.is_expired(link_data):
                logger.warning(f"[update_hosted_link] Link expired: {link_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Hosted link '{link_id}' has expired",
                )
            else:
                logger.warning(f"[update_hosted_link] Link not found for update: {link_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Hosted link '{link_id}' not found for update",
                )

        logger.info(f"[update_hosted_link] Successfully updated {link_id}:")
        logger.info(f"  - new_status: {updated_link.status}")
        logger.info(f"  - brand_id: {updated_link.brand_id}")
        logger.info(f"  - profile_id: {updated_link.profile_id}")

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
        logger.error(f"Error updating hosted link status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating hosted link status",
        )
