from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from getgather.connectors.spec_loader import BrandIdEnum, list_brand_specs, load_brand_spec

router = APIRouter(prefix="/brands", tags=["brands"])

class APIBrandSpec(BaseModel):
    id: str
    name: str

@router.get("", response_model=list[APIBrandSpec])
async def get_brands(test: bool = False):
    """
    Get a list of all brands and their details.
    """
    full_specs = await list_brand_specs(include="all" if test else "prod")
    return [APIBrandSpec(id=spec.id, name=spec.name) for spec in full_specs]


@router.get("/{brand_id}", response_model=APIBrandSpec)
async def get_brand(
    brand_id: BrandIdEnum,
):
    """
    Get a specific brand by ID.
    """
    try:
        spec = await load_brand_spec(brand_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found: {e}",
        )
    return APIBrandSpec(id=spec.id, name=spec.name)
