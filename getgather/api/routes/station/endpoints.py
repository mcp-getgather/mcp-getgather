from fastapi import APIRouter, HTTPException, status

from getgather.api.routes.station.types import UpdateBrandEnabledRequest
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.logs import logger

router = APIRouter(prefix="/station", tags=["station"])


@router.get("/brands", response_model=list[BrandState])
async def get_brands() -> list[BrandState]:
    logger.info(f"Retrieving brand status")
    try:
        return BrandState.get_all()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving brand status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving brand status",
        )


@router.patch("/brands/{brand_id}")
async def update_brand_enabled(
    brand_id: BrandIdEnum,
    request: UpdateBrandEnabledRequest,
) -> BrandState:
    logger.info(f"Updating brand status: {brand_id}")
    brand_state = BrandState.get_by_brand_id(brand_id)
    if not brand_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand {brand_id} not found",
        )
    BrandState.update_enabled(brand_id, request.enabled)
    brand_state.enabled = request.enabled
    return brand_state
